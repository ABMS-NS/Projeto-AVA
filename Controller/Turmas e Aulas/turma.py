import sys
from pathlib import Path
from datetime import datetime

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db import get_connection, fetch_all, query_one, execute

app = Flask(__name__)
CORS(app)

TIMER_SERVICE = "http://localhost:5004"


@app.route("/registro_turma", methods=["POST"])
def registro_turma():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        nome_turma = data.get("nome_turma", "").strip()
        professor_email = data.get("professor_email", "").strip()

        if not nome_turma or not professor_email:
            return jsonify({"error": "nome_turma e professor_email são obrigatórios"}), 400

        existente = query_one(
            "SELECT id FROM turmas WHERE nome_turma = ?", (nome_turma,)
        )
        if existente:
            return jsonify({"error": "Turma já cadastrada"}), 400

        turma_id = execute(
            "INSERT INTO turmas (nome_turma, professor_email) VALUES (?, ?)",
            (nome_turma, professor_email)
        )

        return jsonify({"message": "Turma registrada com sucesso!", "id": turma_id}), 201

    except Exception as e:
        return jsonify({"error": f"Erro no servidor: {str(e)}"}), 500


@app.route("/listar_turmas", methods=["GET"])
def listar_turmas():
    try:
        conn = get_connection()
        turmas_raw = conn.execute(
            "SELECT id, nome_turma, professor_email FROM turmas ORDER BY id"
        ).fetchall()

        resultado = []
        for t in turmas_raw:
            alunos = [
                r["aluno_email"]
                for r in conn.execute(
                    "SELECT aluno_email FROM turma_alunos WHERE turma_id = ?", (t["id"],)
                ).fetchall()
            ]
            aulas = [
                dict(a)
                for a in conn.execute(
                    "SELECT id, turma_id, status, assunto, data_inicio, data_fim, "
                    "duracao_segundos FROM aulas WHERE turma_id = ? ORDER BY id",
                    (t["id"],),
                ).fetchall()
            ]
            for a in aulas:
                a["alunos_presentes"] = [
                    r["aluno_email"]
                    for r in conn.execute(
                        "SELECT aluno_email FROM frequencias WHERE aula_id = ? AND presente = 1",
                        (a["id"],),
                    ).fetchall()
                ]
                a["registros_frequencia"] = [
                    {"email": r["aluno_email"], "hora_entrada": r["hora_entrada"]}
                    for r in conn.execute(
                        "SELECT aluno_email, hora_entrada FROM frequencias WHERE aula_id = ? AND presente = 1 AND hora_entrada IS NOT NULL",
                        (a["id"],),
                    ).fetchall()
                ]

            resultado.append({
                "id": t["id"],
                "nome_turma": t["nome_turma"],
                "professor_email": t["professor_email"],
                "alunos": alunos,
                "aulas": aulas,
            })

        conn.close()
        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao listar turmas: {str(e)}"}), 500


@app.route("/adicionar_aluno_turma", methods=["POST"])
def adicionar_aluno_turma():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        email = data.get("email", "").strip()
        id_turma = data.get("id_turma", "").strip()

        if not email or not id_turma:
            return jsonify({"error": "email e id_turma são obrigatórios"}), 400

        turma = query_one("SELECT id FROM turmas WHERE id = ?", (int(id_turma),))
        if not turma:
            return jsonify({"error": "Turma não encontrada"}), 404

        ja_matriculado = query_one(
            "SELECT 1 FROM turma_alunos WHERE turma_id = ? AND aluno_email = ?",
            (int(id_turma), email),
        )
        if ja_matriculado:
            return jsonify({"error": "Aluno já cadastrado na turma"}), 400

        execute(
            "INSERT INTO turma_alunos (turma_id, aluno_email) VALUES (?, ?)",
            (int(id_turma), email),
        )

        return jsonify({"message": "Aluno adicionado à turma"}), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao adicionar aluno à turma: {str(e)}"}), 500


@app.route("/iniciar_aula", methods=["POST"])
def iniciar_aula():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        id_turma = str(data.get("id_turma", "")).strip()
        assunto = str(data.get("assunto", "")).strip()
        duracao = str(data.get("duracao", "3600")).strip()

        if not id_turma:
            return jsonify({"error": "id_turma é obrigatório"}), 400

        turma = query_one("SELECT id FROM turmas WHERE id = ?", (int(id_turma),))
        if not turma:
            return jsonify({"error": "Turma não encontrada"}), 404

        aula_ativa = query_one(
            "SELECT id FROM aulas WHERE turma_id = ? AND status = 'ativa'",
            (int(id_turma),),
        )
        if aula_ativa:
            return jsonify({"error": "Já existe uma aula ativa nesta turma"}), 400

        agora = datetime.now()
        data_inicio = agora.isoformat()

        aula_id = execute(
            "INSERT INTO aulas (turma_id, status, assunto, data_inicio, duracao_segundos) "
            "VALUES (?, 'ativa', ?, ?, ?)",
            (int(id_turma), assunto or "Sem assunto definido", data_inicio, int(duracao)),
        )

        try:
            timer_resp = requests.post(
                f"{TIMER_SERVICE}/timer/iniciar",
                json={
                    "id_turma": id_turma,
                    "id_aula": aula_id,
                    "duracao_segundos": duracao,
                },
                timeout=5,
            )
            if timer_resp.status_code == 201:
                timer_data_inicio = timer_resp.json().get("data_inicio")
                if timer_data_inicio:
                    execute(
                        "UPDATE aulas SET data_inicio = ? WHERE id = ?",
                        (timer_data_inicio, aula_id),
                    )
                    data_inicio = timer_data_inicio
        except requests.exceptions.ConnectionError:
            pass

        nova_aula = {
            "id": aula_id,
            "id_turma": int(id_turma),
            "status": "ativa",
            "assunto": assunto or "Sem assunto definido",
            "data_inicio": data_inicio,
            "data_fim": None,
            "duracao_segundos": int(duracao),
            "alunos_presentes": [],
            "registros_frequencia": [],
        }

        return jsonify({"message": "Aula iniciada com sucesso!", "aula": nova_aula}), 201

    except Exception as e:
        return jsonify({"error": f"Erro ao iniciar aula: {str(e)}"}), 500


@app.route("/registrar_presenca_aula", methods=["POST"])
def registrar_presenca_aula():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        email = str(data.get("email", "")).strip()
        id_turma = str(data.get("id_turma", "")).strip()
        id_aula = str(data.get("id_aula", "")).strip()

        if not email or not id_turma or not id_aula:
            return jsonify({"error": "email, id_turma e id_aula são obrigatórios"}), 400

        conn = get_connection()

        turma = conn.execute(
            "SELECT id FROM turmas WHERE id = ?", (int(id_turma),)
        ).fetchone()
        if not turma:
            conn.close()
            return jsonify({"error": "Turma não encontrada"}), 404

        matricula = conn.execute(
            "SELECT 1 FROM turma_alunos WHERE turma_id = ? AND aluno_email = ?",
            (int(id_turma), email),
        ).fetchone()
        if not matricula:
            conn.close()
            return jsonify({"error": "Aluno não está matriculado nesta turma"}), 400

        aula = conn.execute(
            "SELECT id, status FROM aulas WHERE id = ? AND turma_id = ?",
            (int(id_aula), int(id_turma)),
        ).fetchone()
        if not aula:
            conn.close()
            return jsonify({"error": "Aula não encontrada"}), 404

        if aula["status"] != "ativa":
            conn.close()
            return jsonify({"error": "Aula não está ativa"}), 400

        presenca_existente = conn.execute(
            "SELECT 1 FROM frequencias WHERE aula_id = ? AND aluno_email = ?",
            (int(id_aula), email),
        ).fetchone()
        if presenca_existente:
            conn.close()
            conn = get_connection()
            aula_data = conn.execute(
                "SELECT id, turma_id, status, assunto, data_inicio, data_fim, duracao_segundos "
                "FROM aulas WHERE id = ?", (int(id_aula),)
            ).fetchone()
            presentes = [
                r["aluno_email"]
                for r in conn.execute(
                    "SELECT aluno_email FROM frequencias WHERE aula_id = ? AND presente = 1",
                    (int(id_aula),),
                ).fetchall()
            ]
            registros = [
                {"email": r["aluno_email"], "hora_entrada": r["hora_entrada"]}
                for r in conn.execute(
                    "SELECT aluno_email, hora_entrada FROM frequencias WHERE aula_id = ? AND presente = 1 AND hora_entrada IS NOT NULL",
                    (int(id_aula),),
                ).fetchall()
            ]
            conn.close()
            a = dict(aula_data)
            a["alunos_presentes"] = presentes
            a["registros_frequencia"] = registros
            return jsonify({"message": "Presença já registrada", "aula": a}), 200

        try:
            requests.post(
                f"{TIMER_SERVICE}/timer/registrar_presenca",
                json={"email": email, "id_turma": id_turma, "id_aula": id_aula},
                timeout=5,
            )
        except requests.exceptions.ConnectionError:
            pass

        conn.execute(
            "INSERT INTO frequencias (aula_id, turma_id, aluno_email, presente, hora_entrada) "
            "VALUES (?, ?, ?, 1, ?)",
            (int(id_aula), int(id_turma), email, datetime.now().isoformat()),
        )
        conn.commit()

        aula_data = conn.execute(
            "SELECT id, turma_id, status, assunto, data_inicio, data_fim, duracao_segundos "
            "FROM aulas WHERE id = ?", (int(id_aula),)
        ).fetchone()
        presentes = [
            r["aluno_email"]
            for r in conn.execute(
                "SELECT aluno_email FROM frequencias WHERE aula_id = ? AND presente = 1",
                (int(id_aula),),
            ).fetchall()
        ]
        registros = [
            {"email": r["aluno_email"], "hora_entrada": r["hora_entrada"]}
            for r in conn.execute(
                "SELECT aluno_email, hora_entrada FROM frequencias WHERE aula_id = ? AND presente = 1 AND hora_entrada IS NOT NULL",
                (int(id_aula),),
            ).fetchall()
        ]
        conn.close()
        a = dict(aula_data)
        a["alunos_presentes"] = presentes
        a["registros_frequencia"] = registros

        return jsonify({"message": "Presença registrada com sucesso!", "aula": a}), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao registrar presença: {str(e)}"}), 500


@app.route("/terminar_aula", methods=["POST"])
def terminar_aula():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        id_turma = str(data.get("id_turma", "")).strip()
        id_aula = str(data.get("id_aula", "")).strip()

        if not id_turma or not id_aula:
            return jsonify({"error": "id_turma e id_aula são obrigatórios"}), 400

        conn = get_connection()

        turma = conn.execute(
            "SELECT id, nome_turma FROM turmas WHERE id = ?", (int(id_turma),)
        ).fetchone()
        if not turma:
            conn.close()
            return jsonify({"error": "Turma não encontrada"}), 404

        aula = conn.execute(
            "SELECT id, turma_id, status, assunto, data_inicio, duracao_segundos "
            "FROM aulas WHERE id = ? AND turma_id = ?",
            (int(id_aula), int(id_turma)),
        ).fetchone()
        if not aula:
            conn.close()
            return jsonify({"error": "Aula não encontrada"}), 404

        if aula["status"] != "ativa":
            conn.close()
            return jsonify({"error": "Aula já foi encerrada"}), 400

        timer_data = None
        try:
            timer_resp = requests.post(
                f"{TIMER_SERVICE}/timer/encerrar",
                json={"id_turma": id_turma, "id_aula": id_aula},
                timeout=5,
            )
            if timer_resp.status_code == 200:
                timer_data = timer_resp.json()
        except requests.exceptions.ConnectionError:
            pass

        agora = datetime.now()

        data_inicio = aula["data_inicio"]
        data_fim = agora.isoformat()

        alunos_presentes_timer = []
        if timer_data:
            data_inicio = timer_data.get("data_inicio", data_inicio)
            data_fim = timer_data.get("data_fim", data_fim)
            alunos_presentes_timer = timer_data.get("alunos_presentes", [])

        conn.execute(
            "UPDATE aulas SET status = 'encerrada', data_fim = ? WHERE id = ?",
            (data_fim, int(id_aula)),
        )

        presentes_ja = {
            r["aluno_email"]
            for r in conn.execute(
                "SELECT aluno_email FROM frequencias WHERE aula_id = ? AND presente = 1",
                (int(id_aula),),
            ).fetchall()
        }

        for email_timer in alunos_presentes_timer:
            if email_timer not in presentes_ja:
                conn.execute(
                    "INSERT OR IGNORE INTO frequencias (aula_id, turma_id, aluno_email, presente, hora_entrada) "
                    "VALUES (?, ?, ?, 1, ?)",
                    (int(id_aula), int(id_turma), email_timer, data_fim),
                )
                presentes_ja.add(email_timer)

        alunos_turma = [
            r["aluno_email"]
            for r in conn.execute(
                "SELECT aluno_email FROM turma_alunos WHERE turma_id = ?",
                (int(id_turma),),
            ).fetchall()
        ]

        for email_aluno in alunos_turma:
            if email_aluno not in presentes_ja:
                conn.execute(
                    "INSERT OR IGNORE INTO frequencias (aula_id, turma_id, aluno_email, presente, hora_entrada) "
                    "VALUES (?, ?, ?, 0, NULL)",
                    (int(id_aula), int(id_turma), email_aluno),
                )

        conn.commit()

        frequencias = [
            dict(r)
            for r in conn.execute(
                "SELECT aluno_email, presente, hora_entrada FROM frequencias "
                "WHERE aula_id = ? ORDER BY presente DESC, aluno_email",
                (int(id_aula),),
            ).fetchall()
        ]

        alunos_presentes = [f["aluno_email"] for f in frequencias if f["presente"]]
        alunos_ausentes = [f["aluno_email"] for f in frequencias if not f["presente"]]

        registro_frequencia = {
            "id_aula": int(id_aula),
            "id_turma": int(id_turma),
            "turma_nome": turma["nome_turma"],
            "assunto": aula["assunto"],
            "data": agora.strftime("%Y-%m-%d"),
            "inicio": data_inicio,
            "fim": data_fim,
            "alunos_presentes": alunos_presentes,
            "alunos_ausentes": alunos_ausentes,
            "total_alunos": len(alunos_turma),
            "frequencias_individuais": [
                {
                    "email": f["aluno_email"],
                    "presente": bool(f["presente"]),
                    "hora_entrada": f["hora_entrada"],
                }
                for f in frequencias
            ],
        }

        conn.close()

        return jsonify({
            "message": "Aula encerrada com sucesso!",
            "frequencia": registro_frequencia,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao encerrar aula: {str(e)}"}), 500


@app.route("/listar_aulas", methods=["GET"])
def listar_aulas():
    try:
        aulas = fetch_all(
            "SELECT id, turma_id, status, assunto, data_inicio, data_fim, duracao_segundos "
            "FROM aulas ORDER BY id"
        )
        conn = get_connection()
        for a in aulas:
            a["alunos_presentes"] = [
                r["aluno_email"]
                for r in conn.execute(
                    "SELECT aluno_email FROM frequencias WHERE aula_id = ? AND presente = 1",
                    (a["id"],),
                ).fetchall()
            ]
            a["registros_frequencia"] = [
                {"email": r["aluno_email"], "hora_entrada": r["hora_entrada"]}
                for r in conn.execute(
                    "SELECT aluno_email, hora_entrada FROM frequencias WHERE aula_id = ? AND presente = 1 AND hora_entrada IS NOT NULL",
                    (a["id"],),
                ).fetchall()
            ]
        conn.close()
        return jsonify(aulas), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar aulas: {str(e)}"}), 500


@app.route("/listar_aulas_turma", methods=["GET"])
def listar_aulas_turma():
    try:
        id_turma = request.args.get("id_turma", "").strip()
        if not id_turma:
            return jsonify({"error": "id_turma é obrigatório"}), 400

        aulas = fetch_all(
            "SELECT id, turma_id, status, assunto, data_inicio, data_fim, duracao_segundos "
            "FROM aulas WHERE turma_id = ? ORDER BY id",
            (int(id_turma),),
        )
        conn = get_connection()
        for a in aulas:
            a["alunos_presentes"] = [
                r["aluno_email"]
                for r in conn.execute(
                    "SELECT aluno_email FROM frequencias WHERE aula_id = ? AND presente = 1",
                    (a["id"],),
                ).fetchall()
            ]
            a["registros_frequencia"] = [
                {"email": r["aluno_email"], "hora_entrada": r["hora_entrada"]}
                for r in conn.execute(
                    "SELECT aluno_email, hora_entrada FROM frequencias WHERE aula_id = ? AND presente = 1 AND hora_entrada IS NOT NULL",
                    (a["id"],),
                ).fetchall()
            ]
        conn.close()
        return jsonify(aulas), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao listar aulas da turma: {str(e)}"}), 500


@app.route("/listar_frequencias", methods=["GET"])
def listar_frequencias():
    try:
        conn = get_connection()
        aulas = conn.execute(
            "SELECT id, turma_id, assunto, data_inicio, data_fim FROM aulas WHERE status = 'encerrada' ORDER BY data_inicio DESC"
        ).fetchall()

        resultado = []
        for aula in aulas:
            alunos_turma = [
                r["aluno_email"]
                for r in conn.execute(
                    "SELECT aluno_email FROM turma_alunos WHERE turma_id = ?",
                    (aula["turma_id"],),
                ).fetchall()
            ]

            turma = conn.execute(
                "SELECT nome_turma FROM turmas WHERE id = ?", (aula["turma_id"],)
            ).fetchone()

            frequencias = [
                dict(r)
                for r in conn.execute(
                    "SELECT aluno_email, presente, hora_entrada FROM frequencias "
                    "WHERE aula_id = ? ORDER BY presente DESC, aluno_email",
                    (aula["id"],),
                ).fetchall()
            ]

            alunos_presentes = [f["aluno_email"] for f in frequencias if f["presente"]]
            alunos_ausentes = [f["aluno_email"] for f in frequencias if not f["presente"]]

            data_inicio = aula["data_inicio"]
            data_fim = aula["data_fim"]
            data_str = ""
            if data_inicio:
                try:
                    data_str = datetime.fromisoformat(data_inicio).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    data_str = data_inicio[:10] if data_inicio else ""

            resultado.append({
                "id_aula": aula["id"],
                "id_turma": aula["turma_id"],
                "turma_nome": turma["nome_turma"] if turma else f"Turma #{aula['turma_id']}",
                "assunto": aula["assunto"],
                "data": data_str,
                "inicio": data_inicio,
                "fim": data_fim,
                "alunos_presentes": alunos_presentes,
                "alunos_ausentes": alunos_ausentes,
                "total_alunos": len(alunos_turma),
                "frequencias_individuais": [
                    {
                        "email": f["aluno_email"],
                        "presente": bool(f["presente"]),
                        "hora_entrada": f["hora_entrada"],
                    }
                    for f in frequencias
                ],
            })

        conn.close()
        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao listar frequências: {str(e)}"}), 500


@app.route("/listar_frequencias_aula", methods=["GET"])
def listar_frequencias_aula():
    try:
        id_turma = request.args.get("id_turma", "").strip()
        id_aula = request.args.get("id_aula", "").strip()

        if not id_turma or not id_aula:
            return jsonify({"error": "id_turma e id_aula são obrigatórios"}), 400

        conn = get_connection()

        aula = conn.execute(
            "SELECT id, turma_id, assunto, data_inicio, data_fim FROM aulas WHERE id = ? AND turma_id = ?",
            (int(id_aula), int(id_turma)),
        ).fetchone()

        if not aula:
            conn.close()
            return jsonify([]), 200

        turma = conn.execute(
            "SELECT nome_turma FROM turmas WHERE id = ?", (int(id_turma),)
        ).fetchone()

        alunos_turma = [
            r["aluno_email"]
            for r in conn.execute(
                "SELECT aluno_email FROM turma_alunos WHERE turma_id = ?",
                (int(id_turma),),
            ).fetchall()
        ]

        frequencias = [
            dict(r)
            for r in conn.execute(
                "SELECT aluno_email, presente, hora_entrada FROM frequencias "
                "WHERE aula_id = ? ORDER BY presente DESC, aluno_email",
                (int(id_aula),),
            ).fetchall()
        ]

        conn.close()

        alunos_presentes = [f["aluno_email"] for f in frequencias if f["presente"]]
        alunos_ausentes = [f["aluno_email"] for f in frequencias if not f["presente"]]

        data_inicio = aula["data_inicio"]
        data_fim = aula["data_fim"]
        data_str = ""
        if data_inicio:
            try:
                data_str = datetime.fromisoformat(data_inicio).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                data_str = data_inicio[:10] if data_inicio else ""

        resultado = [{
            "id_aula": aula["id"],
            "id_turma": aula["turma_id"],
            "turma_nome": turma["nome_turma"] if turma else f"Turma #{id_turma}",
            "assunto": aula["assunto"],
            "data": data_str,
            "inicio": data_inicio,
            "fim": data_fim,
            "alunos_presentes": alunos_presentes,
            "alunos_ausentes": alunos_ausentes,
            "total_alunos": len(alunos_turma),
            "frequencias_individuais": [
                {
                    "email": f["aluno_email"],
                    "presente": bool(f["presente"]),
                    "hora_entrada": f["hora_entrada"],
                }
                for f in frequencias
            ],
        }]

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao listar frequências: {str(e)}"}), 500


@app.route("/buscar_usuario", methods=["GET"])
def buscar_usuario():
    try:
        email = request.args.get("email", "").strip()
        if not email:
            return jsonify({"error": "email é obrigatório"}), 400

        usuario = query_one(
            "SELECT nome, email, tipo FROM usuarios WHERE email = ?", (email,)
        )
        if not usuario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        return jsonify({
            "nome": usuario["nome"],
            "email": usuario["email"],
            "tipo": usuario["tipo"],
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao buscar usuário: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5003)
