from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from werkzeug.security import check_password_hash

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

@app.route('/login', methods=['POST'])
def login():
    """Processa o login do usuário"""
    try:
        data = request.get_json(silent=True)
        
        if not data:
            data = request.form.to_dict()
        
        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400
        
        email = data.get('email', '').strip()
        senha = data.get('senha', '').strip()
        
        if not email or not senha:
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        # Carrega usuários do arquivo
        users = load_users()
        
        # Procura o usuário pelo nome
        usuario = None
        for user in users:
            if user['email'] == email:
                usuario = user
                break
        
        # Se não encontrou o usuário
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Verifica se a senha está correta
        if not check_password_hash(usuario['senha'], senha):
            return jsonify({'error': 'Senha incorreta'}), 401
        
        # Login bem-sucedido
        return jsonify({
            'message': 'Login realizado com sucesso!',
            'usuario': {
                'nome': usuario['nome'],
                'email': usuario['email'],
                'tipo': usuario.get('tipo', 'aluno')  # Retorna o tipo do usuário
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5002)
