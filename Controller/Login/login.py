from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
from werkzeug.security import check_password_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db import query_one

app = Flask(__name__)
CORS(app)

@app.route('/login', methods=['POST'])
def login():
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

        usuario = query_one(
            "SELECT nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)
        )

        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        if not check_password_hash(usuario['senha'], senha):
            return jsonify({'error': 'Senha incorreta'}), 401

        return jsonify({
            'message': 'Login realizado com sucesso!',
            'usuario': {
                'nome': usuario['nome'],
                'email': usuario['email'],
                'tipo': usuario.get('tipo', 'aluno')
            }
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5002)
