from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

TIMER_FILE = os.path.join(os.path.dirname(__file__), '../../database/timer.json')


def load_timers():
    if os.path.exists(TIMER_FILE):
        try:
            with open(TIMER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def save_timers(timers):
    os.makedirs(os.path.dirname(TIMER_FILE), exist_ok=True)
    with open(TIMER_FILE, 'w', encoding='utf-8') as f:
        json.dump(timers, f, indent=2, ensure_ascii=False)


@app.route('/timer/iniciar', methods=['POST'])
def timer_iniciar():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400

        id_turma = str(data.get('id_turma', '')).strip()
        id_aula = str(data.get('id_aula', '')).strip()
        duracao = str(data.get('duracao_segundos', '3600')).strip()

        if not id_turma or not id_aula:
            return jsonify({'error': 'id_turma e id_aula são obrigatórios'}), 400

        timers = load_timers()
        chave = timer_key(id_turma, id_aula)

        if chave in timers:
            return jsonify({'error': 'Timer já iniciado para esta aula'}), 400

        agora = datetime.now()

        timers[chave] = {
            'id_turma': int(id_turma),
            'id_aula': int(id_aula),
            'data_inicio': agora.isoformat(),
            'duracao_segundos': int(duracao),
            'alunos_presentes': [],
            'registros_frequencia': []
        }

        save_timers(timers)

        return jsonify({
            'message': 'Timer iniciado com sucesso!',
            'data_inicio': agora.isoformat()
        }), 201

    except Exception as e:
        return jsonify({'error': f'Erro ao iniciar timer: {str(e)}'}), 500


@app.route('/timer/registrar_presenca', methods=['POST'])
def timer_registrar_presenca():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400

        email = str(data.get('email', '')).strip()
        id_turma = str(data.get('id_turma', '')).strip()
        id_aula = str(data.get('id_aula', '')).strip()

        if not email or not id_turma or not id_aula:
            return jsonify({'error': 'email, id_turma e id_aula são obrigatórios'}), 400

        timers = load_timers()
        chave = timer_key(id_turma, id_aula)

        if chave not in timers:
            return jsonify({'error': 'Timer não encontrado para esta aula'}), 404

        timer = timers[chave]
        if email in timer['alunos_presentes']:
            return jsonify({'message': 'Presença já registrada no timer'}), 200

        timer['alunos_presentes'].append(email)
        timer['registros_frequencia'].append({
            'email': email,
            'hora_entrada': datetime.now().isoformat()
        })

        save_timers(timers)

        return jsonify({'message': 'Presença registrada no timer com sucesso!'}), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao registrar presença no timer: {str(e)}'}), 500


@app.route('/timer/encerrar', methods=['POST'])
def timer_encerrar():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400

        id_turma = str(data.get('id_turma', '')).strip()
        id_aula = str(data.get('id_aula', '')).strip()

        if not id_turma or not id_aula:
            return jsonify({'error': 'id_turma e id_aula são obrigatórios'}), 400

        timers = load_timers()
        chave = timer_key(id_turma, id_aula)

        if chave not in timers:
            return jsonify({'error': 'Timer não encontrado para esta aula'}), 404

        timer = timers.pop(chave)
        save_timers(timers)

        return jsonify({
            'message': 'Timer encerrado com sucesso!',
            'data_inicio': timer['data_inicio'],
            'data_fim': datetime.now().isoformat(),
            'alunos_presentes': timer['alunos_presentes'],
            'registros_frequencia': timer['registros_frequencia']
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao encerrar timer: {str(e)}'}), 500


@app.route('/timer/status', methods=['GET'])
def timer_status():
    try:
        id_turma = request.args.get('id_turma', '').strip()
        id_aula = request.args.get('id_aula', '').strip()

        if not id_turma or not id_aula:
            return jsonify({'error': 'id_turma e id_aula são obrigatórios'}), 400

        timers = load_timers()
        chave = timer_key(id_turma, id_aula)

        if chave not in timers:
            return jsonify({'error': 'Timer não encontrado'}), 404

        return jsonify(timers[chave]), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao consultar timer: {str(e)}'}), 500


def timer_key(id_turma, id_aula):
    return f"{id_turma}_{id_aula}"


if __name__ == '__main__':
    app.run(debug=True, port=5004)
