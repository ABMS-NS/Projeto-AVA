from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db import execute, query_one

app = Flask(__name__)
CORS(app)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    try:
        data = request.get_json(silent=True)

        if not data:
            data = request.form.to_dict()

        if not data:
            return jsonify({'error': 'Nenhum dado foi enviado'}), 400

        nome = data.get('nome', '').strip()
        email = data.get('email', '').strip()
        senha = data.get('senha', '').strip()

        if not nome or not email or not senha:
            return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400

        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({'error': 'Email inválido'}), 400

        existente = query_one(
            "SELECT email FROM usuarios WHERE email = ?", (email,)
        )
        if existente:
            return jsonify({'error': 'Este email já está cadastrado'}), 409

        senha_hash = generate_password_hash(senha)
        execute(
            "INSERT INTO usuarios (nome, email, tipo, senha, notas) VALUES (?, ?, 'aluno', ?, '[]')",
            (nome, email, senha_hash)
        )

        return jsonify({'message': 'Cadastro realizado com sucesso!', 'email': email}), 201

    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)