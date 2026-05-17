from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
import json

app = Flask(__name__, template_folder='../../Views', static_folder='../../Views', static_url_path='/static')
CORS(app)

# URLs dos microsserviços
CADASTRO_SERVICE = 'http://localhost:5001'
LOGIN_SERVICE = 'http://localhost:5002'
CLASSES_SERVICE = 'http://localhost:5003'
TIMER_SERVICE = 'http://localhost:5004'

# ==================== ROTAS DE PÁGINA ====================

@app.route('/', methods=['GET'])
def index():
    """Mostra a página inicial com botões de login e cadastro"""
    return render_template('pag_inicial.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Mostra o dashboard do usuário logado"""
    return render_template('dashboard.html')

@app.route('/turma.html', methods=['GET'])
@app.route('/turma', methods=['GET'])
def turma_view():
    """Mostra os detalhes de uma turma específica"""
    return render_template('turma.html')

@app.route('/aula.html', methods=['GET'])
@app.route('/aula', methods=['GET'])
def aula_view():
    """Mostra os detalhes de uma aula específica"""
    return render_template('aula.html')

# ==================== CADASTRO ====================

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """
    GET: Retorna o formulário de cadastro
    POST: Processa o cadastro chamando o microsserviço
    """
    if request.method == 'GET':
        # Retorna o formulário de cadastro
        return render_template('cadastro.html')
    
    elif request.method == 'POST':
        # Processa o cadastro
        try:
            # Obtém os dados (JSON ou formulário)
            data = request.get_json(silent=True)
            if not data:
                data = request.form.to_dict()
            
            # Faz requisição ao microsserviço de cadastro
            response = requests.post(
                f'{CADASTRO_SERVICE}/cadastro',
                json=data,
                timeout=5
            )
            
            # Retorna a resposta do microsserviço
            return jsonify(response.json()), response.status_code
            
        except requests.exceptions.ConnectionError:
            return jsonify({'error': 'Serviço de cadastro indisponível'}), 503
        except Exception as e:
            return jsonify({'error': f'Erro ao processar cadastro: {str(e)}'}), 500

# ==================== LOGIN ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET: Retorna o formulário de login
    POST: Processa o login chamando o microsserviço
    """
    if request.method == 'GET':
        # Retorna o formulário de login
        return render_template('login.html')
    
    elif request.method == 'POST':
        # Processa o login
        try:
            # Obtém os dados (JSON ou formulário)
            data = request.get_json(silent=True)
            if not data:
                data = request.form.to_dict()
            
            # Faz requisição ao microsserviço de login
            response = requests.post(
                f'{LOGIN_SERVICE}/login',
                json=data,
                timeout=5
            )
            
            # Retorna a resposta do microsserviço
            return jsonify(response.json()), response.status_code
            
        except requests.exceptions.ConnectionError:
            return jsonify({'error': 'Serviço de login indisponível'}), 503
        except Exception as e:
            return jsonify({'error': f'Erro ao processar login: {str(e)}'}), 500

# ==================== ORQUESTRAÇÃO DE APIs ====================

@app.route('/api/cadastro', methods=['POST'])
def api_cadastro():
    """API para cadastro via JSON"""
    try:
        data = request.get_json()
        response = requests.post(
            f'{CADASTRO_SERVICE}/cadastro',
            json=data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de cadastro indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    """API para login via JSON"""
    try:
        data = request.get_json()
        response = requests.post(
            f'{LOGIN_SERVICE}/login',
            json=data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de login indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/registro_turma', methods=['POST'])
def api_registro_turma():
    """API para registrar turma via JSON"""

    try:
        data = request.get_json()
        response = requests.post(
            f'{CLASSES_SERVICE}/registro_turma',
            json = data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        


@app.route('/api/listar_turmas', methods=['GET'])
def api_listar_turmas():
    """API para listar turmas já registradadas no sistema para o professor (NÃO TESTADA AINDA)"""
    try:
        response = requests.get(f'{CLASSES_SERVICE}/listar_turmas', timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500





@app.route('/api/adicionar_aluno_turma', methods=['POST'])
def api_adicionar_aluno_turma():
    """API para adicionar aluno a uma turma via JSON"""
    try:
        data = request.get_json()
        response = requests.post(
            f'{CLASSES_SERVICE}/adicionar_aluno_turma',
            json=data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/buscar_usuario', methods=['GET'])
def api_buscar_usuario():
    """Busca dados de um usuário por email"""
    try:
        email = request.args.get('email', '')
        response = requests.get(
            f'{CLASSES_SERVICE}/buscar_usuario',
            params={'email': email},
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== AULAS ====================

@app.route('/api/iniciar_aula', methods=['POST'])
def api_iniciar_aula():
    """Inicia uma aula em uma turma"""
    try:
        data = request.get_json()
        response = requests.post(
            f'{CLASSES_SERVICE}/iniciar_aula',
            json=data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/registrar_presenca_aula', methods=['POST'])
def api_registrar_presenca_aula():
    """Registra presença de aluno em uma aula"""
    try:
        data = request.get_json()
        response = requests.post(
            f'{CLASSES_SERVICE}/registrar_presenca_aula',
            json=data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/terminar_aula', methods=['POST'])
def api_terminar_aula():
    """Encerra uma aula e gera registro de frequência"""
    try:
        data = request.get_json()
        response = requests.post(
            f'{CLASSES_SERVICE}/terminar_aula',
            json=data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/listar_aulas', methods=['GET'])
def api_listar_aulas():
    """Lista todas as aulas do sistema"""
    try:
        response = requests.get(f'{CLASSES_SERVICE}/listar_aulas', timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/listar_aulas_turma', methods=['GET'])
def api_listar_aulas_turma():
    """Lista aulas de uma turma específica"""
    try:
        id_turma = request.args.get('id_turma', '')
        response = requests.get(
            f'{CLASSES_SERVICE}/listar_aulas_turma',
            params={'id_turma': id_turma},
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/listar_frequencias', methods=['GET'])
def api_listar_frequencias():
    """Lista todos os registros de frequência"""
    try:
        response = requests.get(f'{CLASSES_SERVICE}/listar_frequencias', timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/listar_frequencias_aula', methods=['GET'])
def api_listar_frequencias_aula():
    """Lista frequências de uma aula específica"""
    try:
        id_turma = request.args.get('id_turma', '')
        id_aula = request.args.get('id_aula', '')
        response = requests.get(
            f'{CLASSES_SERVICE}/listar_frequencias_aula',
            params={'id_turma': id_turma, 'id_aula': id_aula},
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de turma indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== TIMER ====================

@app.route('/api/timer/iniciar', methods=['POST'])
def api_timer_iniciar():
    try:
        data = request.get_json()
        response = requests.post(f'{TIMER_SERVICE}/timer/iniciar', json=data, timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de timer indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/timer/registrar_presenca', methods=['POST'])
def api_timer_registrar_presenca():
    try:
        data = request.get_json()
        response = requests.post(f'{TIMER_SERVICE}/timer/registrar_presenca', json=data, timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de timer indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/timer/encerrar', methods=['POST'])
def api_timer_encerrar():
    try:
        data = request.get_json()
        response = requests.post(f'{TIMER_SERVICE}/timer/encerrar', json=data, timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de timer indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/timer/status', methods=['GET'])
def api_timer_status():
    try:
        id_turma = request.args.get('id_turma', '')
        id_aula = request.args.get('id_aula', '')
        response = requests.get(
            f'{TIMER_SERVICE}/timer/status',
            params={'id_turma': id_turma, 'id_aula': id_aula},
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Serviço de timer indisponível'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)