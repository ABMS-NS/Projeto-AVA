import json
import os
from datetime import datetime

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CLASS_FILE = os.path.join(os.path.dirname(__file__), "../../database/classes.json")
AULA_FILE = os.path.join(os.path.dirname(__file__), "../../database/aula.json")
FREQ_FILE = os.path.join(os.path.dirname(__file__), "../../database/frequences.json")
USER_FILE = os.path.join(os.path.dirname(__file__), "../../database/users.json")
TIMER_SERVICE = "http://localhost:5004"


def save_classes(turma):
    """Salva os usuários no arquivo JSON"""
    os.makedirs(os.path.dirname(CLASS_FILE), exist_ok=True)  # se o json existe
    with open(CLASS_FILE, "w", encoding="utf-8") as f:  # abre ele e lê
        json.dump(turma, f, indent=2, ensure_ascii=False)  # SALVA


def load_aulas():
    if os.path.exists(AULA_FILE):
        try:
            with open(AULA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def save_aulas(aulas):
    os.makedirs(os.path.dirname(AULA_FILE), exist_ok=True)
    with open(AULA_FILE, "w", encoding="utf-8") as f:
        json.dump(aulas, f, indent=2, ensure_ascii=False)


def load_frequencias():
    if os.path.exists(FREQ_FILE):
        try:
            with open(FREQ_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def save_frequencias(frequencias):
    os.makedirs(os.path.dirname(FREQ_FILE), exist_ok=True)
    with open(FREQ_FILE, "w", encoding="utf-8") as f:
        json.dump(frequencias, f, indent=2, ensure_ascii=False)


@app.route("/registro_turma", methods=["POST"])
def registro_turma():

    try:
        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, "r", encoding="utf-8") as f:
                classes = json.load(f)
        else:
            classes = []

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar turmas: {str(e)}"}), 500

    try:
        data = request.get_json(silent=True)  # carrega tudo do json

        if not data:
            data = (
                request.form.to_dict()
            )  # se n tiver do jotason, procura diretamente no form

        if not data:
            return jsonify(
                {"error": "Nenhum dado foi enviado"}
            ), 400  # se n tiver dados, só retorna um erro

        nome_turma = data.get("nome_turma", "").strip()  # pega o nome da turma
        professor_email = data.get("professor_email", "").strip()

        if any(t["nome_turma"] == nome_turma for t in classes):
            return jsonify(
                {"error": "Turma já cadastrada"}
            ), 400  # se o nome já for registrado, retorna outro erro

        id_turma = (
            classes[-1].get("id", 0) + 1 if classes else 1
        )  # pega o id do ultimo e salva +1 ou, se não tiver nenhum, salva como 1

        nova_turma = {
            "nome_turma": nome_turma,
            "professor_email": professor_email,
            "id": id_turma,
            "alunos": [],
            "aulas": [],
        }

        # adiciona no json e salva
        classes.append(nova_turma)
        save_classes(classes)

        return jsonify(
            {"message": "Turma registrada com sucesso!", "id": id_turma}
        ), 201

    except Exception as e:
        return jsonify({"error": f"Erro no servidor: {str(e)}"}), 500


@app.route("/listar_turmas", methods=["GET"])
def listar_turmas():
    try:
        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, "r", encoding="utf-8") as f:
                classes = json.load(f)
        else:
            classes = []
        return jsonify(classes), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar turmas: {str(e)}"}), 500


@app.route("/adicionar_aluno_turma", methods=["POST"])
def adicionar_aluno_turma():
    """Referente a Entrar_Alunos() no diagrama de sequência"""
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()

        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        email = data.get("email", "").strip()
        id_turma = data.get("id_turma", "").strip()

        if not email or not id_turma:
            return jsonify({"error": "id da turma é obrigatório"}), 400

        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, "r", encoding="utf-8") as f:
                classes = json.load(f)

        else:
            classes = []

        for turma in classes:
            if turma["id"] == int(id_turma):
                if email in turma["alunos"]:
                    return jsonify({"error": "Aluno já cadastrado na turma"}), 400

                turma["alunos"].append(email)
                save_classes(classes)
                return jsonify({"message": "Aluno adicionado à turma"}), 200

        return jsonify({"error": "Turma não encontrada"}), 404

    except Exception as e:
        return jsonify({"error": f"Erro ao adicionar aluno à turma: {str(e)}"}), 500


@app.route("/iniciar_aula", methods=["POST"])
def iniciar_aula():
    """Fluxo: Começar Aula -> Turma -> Aula -> Timer -> Salvar"""
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

        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, "r", encoding="utf-8") as f:
                classes = json.load(f)
        else:
            return jsonify({"error": "Nenhuma turma encontrada"}), 404

        turma = next((t for t in classes if t["id"] == int(id_turma)), None)
        if not turma:
            return jsonify({"error": "Turma não encontrada"}), 404

        aulas = turma.get("aulas", [])
        for a in aulas:
            if a.get("status") == "ativa":
                return jsonify({"error": "Já existe uma aula ativa nesta turma"}), 400

        id_aula = aulas[-1]["id"] + 1 if aulas else 1

        timer_data_inicio = None
        try:
            timer_resp = requests.post(
                f"{TIMER_SERVICE}/timer/iniciar",
                json={
                    "id_turma": id_turma,
                    "id_aula": id_aula,
                    "duracao_segundos": duracao,
                },
                timeout=5,
            )
            if timer_resp.status_code == 201:
                timer_data_inicio = timer_resp.json().get("data_inicio")
        except requests.exceptions.ConnectionError:
            pass

        nova_aula = {
            "id": id_aula,
            "id_turma": int(id_turma),
            "status": "ativa",
            "assunto": assunto or "Sem assunto definido",
            "data_inicio": timer_data_inicio or datetime.now().isoformat(),
            "data_fim": None,
            "duracao_segundos": int(duracao),
            "alunos_presentes": [],
            "registros_frequencia": [],
        }

        aulas.append(nova_aula)
        turma["aulas"] = aulas
        save_classes(classes)

        todas_aulas = load_aulas()
        todas_aulas.append(nova_aula)
        save_aulas(todas_aulas)

        return jsonify(
            {"message": "Aula iniciada com sucesso!", "aula": nova_aula}
        ), 201

    except Exception as e:
        return jsonify({"error": f"Erro ao iniciar aula: {str(e)}"}), 500


@app.route("/registrar_presenca_aula", methods=["POST"])
def registrar_presenca_aula():
    """Fluxo: Entrar Aula -> Registrar_Aluno -> Timer Registrar_Frequencia"""
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

        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, "r", encoding="utf-8") as f:
                classes = json.load(f)
        else:
            return jsonify({"error": "Nenhuma turma encontrada"}), 404

        turma = next((t for t in classes if t["id"] == int(id_turma)), None)
        if not turma:
            return jsonify({"error": "Turma não encontrada"}), 404

        if email not in turma.get("alunos", []):
            return jsonify({"error": "Aluno não está matriculado nesta turma"}), 400

        aula = next(
            (a for a in turma.get("aulas", []) if a["id"] == int(id_aula)), None
        )
        if not aula:
            return jsonify({"error": "Aula não encontrada"}), 404

        if aula.get("status") != "ativa":
            return jsonify({"error": "Aula não está ativa"}), 400

        if email in aula.get("alunos_presentes", []):
            return jsonify({"message": "Presença já registrada", "aula": aula}), 200

        try:
            requests.post(
                f"{TIMER_SERVICE}/timer/registrar_presenca",
                json={"email": email, "id_turma": id_turma, "id_aula": id_aula},
                timeout=5,
            )
        except requests.exceptions.ConnectionError:
            pass

        aula["alunos_presentes"].append(email)
        aula["registros_frequencia"].append(
            {"email": email, "hora_entrada": datetime.now().isoformat()}
        )

        save_classes(classes)

        todas_aulas = load_aulas()
        for i, a in enumerate(todas_aulas):
            if a["id"] == int(id_aula) and a.get("id_turma") == int(id_turma):
                todas_aulas[i] = aula
                break
        save_aulas(todas_aulas)

        return jsonify(
            {"message": "Presença registrada com sucesso!", "aula": aula}
        ), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao registrar presença: {str(e)}"}), 500


@app.route("/terminar_aula", methods=["POST"])
def terminar_aula():
    """Fluxo: Encerrar Aula -> Terminar_Sessao -> Timer Encerrar_Timer -> Salvar_Frequencia"""
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

        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, "r", encoding="utf-8") as f:
                classes = json.load(f)
        else:
            return jsonify({"error": "Nenhuma turma encontrada"}), 404

        turma = next((t for t in classes if t["id"] == int(id_turma)), None)
        if not turma:
            return jsonify({"error": "Turma não encontrada"}), 404

        aula = next(
            (a for a in turma.get("aulas", []) if a["id"] == int(id_aula)), None
        )
        if not aula:
            return jsonify({"error": "Aula não encontrada"}), 404

        if aula.get("status") != "ativa":
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
        aula["status"] = "encerrada"
        aula["data_fim"] = agora.isoformat()

        if timer_data:
            aula["data_inicio"] = timer_data.get("data_inicio", aula.get("data_inicio"))
            aula["data_fim"] = timer_data.get("data_fim", aula.get("data_fim"))
            aula["alunos_presentes"] = timer_data.get(
                "alunos_presentes", aula.get("alunos_presentes", [])
            )
            aula["registros_frequencia"] = timer_data.get(
                "registros_frequencia", aula.get("registros_frequencia", [])
            )

        alunos_presentes = aula.get("alunos_presentes", [])
        alunos_turma = turma.get("alunos", [])

        frequencias_individuais = []
        for aluno_email in alunos_turma:
            registro = next(
                (
                    r
                    for r in aula.get("registros_frequencia", [])
                    if r["email"] == aluno_email
                ),
                None,
            )
            frequencias_individuais.append(
                {
                    "email": aluno_email,
                    "presente": aluno_email in alunos_presentes,
                    "hora_entrada": registro["hora_entrada"] if registro else None,
                }
            )

        alunos_ausentes = [a for a in alunos_turma if a not in alunos_presentes]

        registro_frequencia = {
            "id_aula": int(id_aula),
            "id_turma": int(id_turma),
            "turma_nome": turma.get("nome_turma"),
            "data": agora.strftime("%Y-%m-%d"),
            "inicio": aula.get("data_inicio"),
            "fim": aula.get("data_fim"),
            "alunos_presentes": alunos_presentes,
            "alunos_ausentes": alunos_ausentes,
            "total_alunos": len(alunos_turma),
            "frequencias_individuais": frequencias_individuais,
        }

        save_classes(classes)

        todas_frequencias = load_frequencias()
        todas_frequencias.append(registro_frequencia)
        save_frequencias(todas_frequencias)

        todas_aulas = load_aulas()
        for i, a in enumerate(todas_aulas):
            if a["id"] == int(id_aula) and a.get("id_turma") == int(id_turma):
                todas_aulas[i] = aula
                break
        save_aulas(todas_aulas)

        return jsonify(
            {
                "message": "Aula encerrada com sucesso!",
                "frequencia": registro_frequencia,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao encerrar aula: {str(e)}"}), 500


@app.route("/listar_aulas", methods=["GET"])
def listar_aulas():
    try:
        aulas = load_aulas()
        return jsonify(aulas), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar aulas: {str(e)}"}), 500


@app.route("/listar_aulas_turma", methods=["GET"])
def listar_aulas_turma():
    try:
        id_turma = request.args.get("id_turma", "").strip()
        if not id_turma:
            return jsonify({"error": "id_turma é obrigatório"}), 400

        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, "r", encoding="utf-8") as f:
                classes = json.load(f)
        else:
            return jsonify({"error": "Nenhuma turma encontrada"}), 404

        turma = next((t for t in classes if t["id"] == int(id_turma)), None)
        if not turma:
            return jsonify({"error": "Turma não encontrada"}), 404

        return jsonify(turma.get("aulas", [])), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao listar aulas da turma: {str(e)}"}), 500


@app.route("/listar_frequencias", methods=["GET"])
def listar_frequencias():
    try:
        frequencias = load_frequencias()
        return jsonify(frequencias), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar frequências: {str(e)}"}), 500


@app.route("/listar_frequencias_aula", methods=["GET"])
def listar_frequencias_aula():
    try:
        id_turma = request.args.get("id_turma", "").strip()
        id_aula = request.args.get("id_aula", "").strip()

        if not id_turma or not id_aula:
            return jsonify({"error": "id_turma e id_aula são obrigatórios"}), 400

        frequencias = load_frequencias()
        resultado = [
            f
            for f in frequencias
            if str(f.get("id_turma")) == id_turma and str(f.get("id_aula")) == id_aula
        ]

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao listar frequências: {str(e)}"}), 500


@app.route("/buscar_usuario", methods=["GET"])
def buscar_usuario():
    try:
        email = request.args.get("email", "").strip()
        if not email:
            return jsonify({"error": "email é obrigatório"}), 400

        if os.path.exists(USER_FILE):
            with open(USER_FILE, "r", encoding="utf-8") as f:
                usuarios = json.load(f)
        else:
            return jsonify({"error": "Nenhum usuário encontrado"}), 404

        usuario = next((u for u in usuarios if u.get("email") == email), None)
        if not usuario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        return jsonify({
            "nome": usuario.get("nome"),
            "email": usuario.get("email"),
            "tipo": usuario.get("tipo")
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao buscar usuário: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5003)
