from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import random

app = Flask(__name__)
CORS(app)

USERS_FILE = os.path.join(os.path.dirname(__file__), '../../database/users.json')
CLASS_FILE = os.path.join(os.path.dirname(__file__), '../../database/classes.json')

def save_classes(turma):
    """Salva os usuários no arquivo JSON"""
    os.makedirs(os.path.dirname(CLASS_FILE), exist_ok=True) #se o json existe
    with open(CLASS_FILE, 'w', encoding='utf-8') as f: #abre ele e lê 
        json.dump(turma, f, indent=2, ensure_ascii=False)#SALVA


@app.route('/registro_turma', methods=['POST'])
def registro_turma():

    try:
        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, 'r', encoding='utf-8') as f:
                classes = json.load(f)
        else:
            classes = []

    except Exception as e:
        return jsonify({'error': f'Erro ao carregar turmas: {str(e)}'}), 500


    try:
        
        data = request.get_json(silent=True) #carrega tudo do json
    
        if not data:
            data = request.form.to_dict() #se n tiver do jotason, procura diretamente no form
        
        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400 #se n tiver dados, só retorna um erro
        
        nome_turma = data.get('nome_turma', '').strip() #pega o nome da turma
        professor_email = data.get('professor_email', '').strip()
        
        if any(t['nome_turma'] == nome_turma for t in classes):
            return jsonify({'error': 'Turma já cadastrada'}), 400 #se o nome já for registrado, retorna outro erro
        
        id_turma = classes[-1].get('id', 0) + 1 if classes else 1 #pega o id do ultimo e salva +1 ou, se não tiver nenhum, salva como 1
        
        nova_turma = {
            'nome_turma': nome_turma,
            'professor_email': professor_email,
            'id': id_turma,
            'alunos': [],
            'aulas': []
        }


        #adiciona no json e salva
        classes.append(nova_turma)
        save_classes(classes)

        return jsonify({'message': 'Turma registrada com sucesso!', 'id': id_turma}), 201

        
        
    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500

@app.route('/listar_turmas', methods=['GET'])
def listar_turmas():
    try:
        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, 'r', encoding='utf-8') as f:
                classes = json.load(f)
        else:
            classes = []
        return jsonify(classes), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao listar turmas: {str(e)}'}), 500


@app.route('/adicionar_aluno_turma', methods=['POST'])
def adicionar_aluno_turma():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()

        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400

        email = data.get('email', '').strip()
        id_turma = data.get('id_turma', '').strip()

        if not email or not id_turma:
            return jsonify({'error': 'id da turma é obrigatório'}), 400

        if os.path.exists(CLASS_FILE):
            with open(CLASS_FILE, 'r', encoding='utf-8') as f:
                classes = json.load(f)

        else:
            classes = []

        for turma in classes:
            if turma['id'] == int(id_turma):

                if email in turma['alunos']:
                    return jsonify({'error': 'Aluno já cadastrado na turma'}), 400

                turma['alunos'].append(email)
                save_classes(classes)
                return jsonify({'message': 'Aluno adicionado à turma'}), 200
    
        return jsonify({'error': 'Turma não encontrada'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Erro ao adicionar aluno à turma: {str(e)}'}), 500





if __name__ == '__main__':
    app.run(debug=True, port=5003)