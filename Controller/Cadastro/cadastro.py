from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from werkzeug.security import generate_password_hash

app = Flask(__name__)
CORS(app)  # Permite requisições de outras origens

# Caminho do arquivo users.json
USERS_FILE = os.path.join(os.path.dirname(__file__), '../../database/users.json')

def load_users():
    """Carrega os usuários do arquivo JSON"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_users(users):
    """Salva os usuários no arquivo JSON"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# ======== ROTAS PARA PROCESSAR DADOS ========

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    try:
        # Tenta receber JSON primeiro (para requisições via JavaScript/Fetch)
        data = request.get_json(silent=True)
        
        # Se não houver JSON, tenta receber dados do formulário HTML
        if not data:
            data = request.form.to_dict()
        
        #validação dos dados
        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400
        
        nome = data.get('nome', '').strip()
        email = data.get('email', '').strip()
        senha = data.get('senha', '').strip()
        
        if not nome or not email or not senha:
            return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400
        
        #validação básica de email
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({'error': 'Email inválido'}), 400
        
        #carrega usuários existentes
        users = load_users()
        
        #verifica se o email já existe
        if any(user['email'] == email for user in users):
            return jsonify({'error': 'Este email já está cadastrado'}), 409
        
        #cria novo usuário com senha hasheada
        novo_usuario = {
            'nome': nome,
            'email': email,
            'tipo': 'aluno',  #sempre "aluno" para auto-cadastro
            'senha': generate_password_hash(senha),
            'notas': []
        }
        
        #adiciona o novo usuário na lista
        users.append(novo_usuario)
        
        #salva no arquivo
        save_users(users)
        
        return jsonify({'message': 'Cadastro realizado com sucesso!', 'email': email}), 201
    
    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)