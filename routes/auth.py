from flask import Blueprint, request, jsonify
from app import db
from models.user_model import User
from utils.jwt_util import generate_token
from datetime import datetime
auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    senha = data.get('senha')
    if not email or not senha:
        return jsonify({'erro':'email e senha obrigatórios'}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_senha(senha):
        return jsonify({'erro':'credenciais inválidas'}), 401
    token = generate_token(user.id, user.tipo)
    return jsonify({'token': token, 'usuario': user.to_dict()}), 200

@auth_bp.route('/accountregistration', methods=['POST'])
def register():
    data = request.get_json() or {}

    email = data.get('email')
    nome = data.get('nome')
    tipo = data.get('tipo', 'default')  # default se não enviar
    senha = data.get('senha')

    # validação
    if not all([email, nome, tipo, senha]):
        return jsonify({'erro': 'email, nome, tipo e senha são obrigatórios'}), 400

    if tipo not in ['admin', 'default']:
        return jsonify({'erro': 'tipo inválido (use admin ou default)'}), 400

    # check se email já existe
    if User.query.filter_by(email=email).first():
        return jsonify({'erro': 'email já cadastrado'}), 400

    # cria user
    user = User(
        email=email,
        nome=nome,
        tipo=tipo
    )
    user.set_senha(senha)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'mensagem': 'Usuário criado com sucesso',
        'usuario': user.to_dict()
    }), 201