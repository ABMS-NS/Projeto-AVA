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
        with open(CLASS_FILE, 'r') as f:
            classes = json.load(f)
    except:
        return jsonify({'error': 'Não foi possivel carregar o Json (ou não existe)'}), 404

    try:
        
        data = request.get_json(silent=True) #carrega tudo do json
    
        if not data:
            data = request.form.to_dict() #se n tiver do jotason, procura diretamente no form
        
        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400 #se n tiver dados, só retorna um erro
        
        nome_turma = data.get('nome_turma', '').strip() #pega o nome da turma
        
        if nome_turma in classes:
            return jsonify({'error': 'Turma já cadastrada'}), 400 #se o nome já for registrado, retorna outro erro
        
        id_turma = classes[-1].get('id_turma', 0) + 1 if classes else 1 #pega o id do ultimo e salva +1 ou, se não tiver nenhum, salva como 1
        
        nova_turma = {
            'nome_turma': nome_turma,
            'id': id_turma,
            'alunos': [],
            'aulas': []
        }


        #adiciona no json e salva
        classes.append(nova_turma)
        save_classes(classes)

        
        
    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)