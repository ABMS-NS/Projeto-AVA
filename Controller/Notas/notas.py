import sys
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db import get_connection, fetch_all, query_one, execute

app = Flask(__name__)
CORS(app)


@app.route("/notas/publicar", methods=["POST"])
def publicar():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        aluno_email = str(data.get("aluno_email", "")).strip()
        turma_id = str(data.get("turma_id", "")).strip()
        nota_valor = data.get("nota")
        professor_email = str(data.get("professor_email", "")).strip()

        if not aluno_email or not turma_id or nota_valor is None or not professor_email:
            return jsonify({"error": "aluno_email, turma_id, nota e professor_email são obrigatórios"}), 400

        professor = query_one("SELECT tipo FROM usuarios WHERE email = ?", (professor_email,))
        if not professor:
            return jsonify({"error": "Professor não encontrado"}), 404
        if professor["tipo"] != "professor":
            return jsonify({"error": "Apenas professores podem publicar notas"}), 403

        aluno = query_one("SELECT email FROM usuarios WHERE email = ?", (aluno_email,))
        if not aluno:
            return jsonify({"error": "Aluno não encontrado"}), 404

        turma = query_one("SELECT id FROM turmas WHERE id = ?", (int(turma_id),))
        if not turma:
            return jsonify({"error": "Turma não encontrada"}), 404

        matricula = query_one(
            "SELECT 1 FROM turma_alunos WHERE turma_id = ? AND aluno_email = ?",
            (int(turma_id), aluno_email),
        )
        if not matricula:
            return jsonify({"error": "Aluno não está matriculado nesta turma"}), 400

        aula_id = data.get("aula_id")
        if aula_id is not None:
            aula_id = int(str(aula_id).strip())
            aula = query_one("SELECT id FROM aulas WHERE id = ?", (aula_id,))
            if not aula:
                return jsonify({"error": "Aula não encontrada"}), 404

        try:
            nota_valor = float(nota_valor)
        except (ValueError, TypeError):
            return jsonify({"error": "Nota deve ser um número"}), 400

        if nota_valor < 0 or nota_valor > 10:
            return jsonify({"error": "Nota deve estar entre 0 e 10"}), 400

        peso = data.get("peso", 1.0)
        try:
            peso = float(peso)
        except (ValueError, TypeError):
            return jsonify({"error": "Peso deve ser um número"}), 400

        descricao = str(data.get("descricao", "")).strip()
        agora = datetime.now().isoformat()

        nota_id = execute(
            "INSERT INTO notas (aluno_email, turma_id, aula_id, nota, peso, descricao, data_lancamento, professor_email) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (aluno_email, int(turma_id), aula_id, nota_valor, peso, descricao, agora, professor_email),
        )

        return jsonify({
            "message": "Nota publicada com sucesso!",
            "id": nota_id,
            "nota": {
                "id": nota_id,
                "aluno_email": aluno_email,
                "turma_id": int(turma_id),
                "aula_id": aula_id,
                "nota": nota_valor,
                "peso": peso,
                "descricao": descricao,
                "data_lancamento": agora,
                "professor_email": professor_email,
            }
        }), 201

    except Exception as e:
        return jsonify({"error": f"Erro ao publicar nota: {str(e)}"}), 500


@app.route("/notas/listar", methods=["GET"])
def listar():
    try:
        turma_id = request.args.get("turma_id", "").strip()
        aluno_email = request.args.get("aluno_email", "").strip()
        aula_id = request.args.get("aula_id", "").strip()

        sql = ("SELECT n.id, n.aluno_email, n.turma_id, n.aula_id, n.nota, n.peso, "
               "n.descricao, n.data_lancamento, n.professor_email, u.nome AS nome_aluno, "
               "t.nome_turma "
               "FROM notas n "
               "JOIN usuarios u ON u.email = n.aluno_email "
               "JOIN turmas t ON t.id = n.turma_id "
               "WHERE 1=1")
        params = []

        if turma_id:
            sql += " AND n.turma_id = ?"
            params.append(int(turma_id))
        if aluno_email:
            sql += " AND n.aluno_email = ?"
            params.append(aluno_email)
        if aula_id:
            sql += " AND n.aula_id = ?"
            params.append(int(aula_id))

        sql += " ORDER BY n.data_lancamento DESC"

        notas = fetch_all(sql, params)
        return jsonify(notas), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao listar notas: {str(e)}"}), 500


@app.route("/notas/aluno", methods=["GET"])
def notas_aluno():
    try:
        email = request.args.get("email", "").strip()
        if not email:
            return jsonify({"error": "email é obrigatório"}), 400

        aluno = query_one("SELECT email FROM usuarios WHERE email = ?", (email,))
        if not aluno:
            return jsonify({"error": "Aluno não encontrado"}), 404

        notas = fetch_all(
            "SELECT n.id, n.turma_id, n.aula_id, n.nota, n.peso, n.descricao, "
            "n.data_lancamento, n.professor_email, t.nome_turma "
            "FROM notas n "
            "JOIN turmas t ON t.id = n.turma_id "
            "WHERE n.aluno_email = ? "
            "ORDER BY t.nome_turma, n.data_lancamento DESC",
            (email,),
        )

        agrupadas = {}
        for n in notas:
            turma_id = n["turma_id"]
            if turma_id not in agrupadas:
                agrupadas[turma_id] = {
                    "turma_id": turma_id,
                    "nome_turma": n["nome_turma"],
                    "notas": [],
                }
            agrupadas[turma_id]["notas"].append({
                "id": n["id"],
                "aula_id": n["aula_id"],
                "nota": n["nota"],
                "peso": n["peso"],
                "descricao": n["descricao"],
                "data_lancamento": n["data_lancamento"],
                "professor_email": n["professor_email"],
            })

        return jsonify(list(agrupadas.values())), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao buscar notas: {str(e)}"}), 500


@app.route("/notas/editar", methods=["PUT"])
def editar():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        nota_id = data.get("id")
        if not nota_id:
            return jsonify({"error": "id da nota é obrigatório"}), 400

        nota_existente = query_one("SELECT * FROM notas WHERE id = ?", (int(nota_id),))
        if not nota_existente:
            return jsonify({"error": "Nota não encontrada"}), 404

        nota_valor = data.get("nota", nota_existente["nota"])
        peso = data.get("peso", nota_existente["peso"])
        descricao = data.get("descricao", nota_existente["descricao"])

        try:
            nota_valor = float(nota_valor)
        except (ValueError, TypeError):
            return jsonify({"error": "Nota deve ser um número"}), 400

        if nota_valor < 0 or nota_valor > 10:
            return jsonify({"error": "Nota deve estar entre 0 e 10"}), 400

        try:
            peso = float(peso)
        except (ValueError, TypeError):
            return jsonify({"error": "Peso deve ser um número"}), 400

        execute(
            "UPDATE notas SET nota = ?, peso = ?, descricao = ? WHERE id = ?",
            (nota_valor, peso, str(descricao).strip(), int(nota_id)),
        )

        nota_atualizada = query_one(
            "SELECT n.*, t.nome_turma FROM notas n "
            "JOIN turmas t ON t.id = n.turma_id WHERE n.id = ?",
            (int(nota_id),),
        )

        return jsonify({"message": "Nota atualizada com sucesso!", "nota": nota_atualizada}), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao editar nota: {str(e)}"}), 500


@app.route("/notas/remover", methods=["DELETE"])
def remover():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        nota_id = data.get("id")
        if not nota_id:
            return jsonify({"error": "id da nota é obrigatório"}), 400

        nota_existente = query_one("SELECT * FROM notas WHERE id = ?", (int(nota_id),))
        if not nota_existente:
            return jsonify({"error": "Nota não encontrada"}), 404

        execute("DELETE FROM notas WHERE id = ?", (int(nota_id),))

        return jsonify({"message": "Nota removida com sucesso!"}), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao remover nota: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5005)
