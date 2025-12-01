from flask import Blueprint, request, jsonify
from app import db
from models.user_model import User
from utils.jwt_util import auth_required, admin_required
from utils.pagination import paginate_query

users_bp = Blueprint('users_bp', __name__)

@users_bp.route('/', methods=['GET'])
@auth_required
def list_users():
    # only admin
    from flask import request
    if request.user.get('tipo') != 'admin':
        return jsonify({'erro':'Acesso negado'}), 403
    query = User.query
    return jsonify(paginate_query(query, lambda u: u.to_dict())), 200

@users_bp.route('/', methods=['POST'])
@auth_required
def create_user():

    from flask import request
    # only admin can create
    if request.user.get('tipo') != 'admin':
        return jsonify({'erro':'Apenas admin pode cadastrar usuários'}), 403
    data = request.get_json() or {}
    email = data.get('email')
    nome = data.get('nome')
    tipo = data.get('tipo', 'default')
    senha = data.get('senha')
    if not all([email, nome, tipo, senha]):
        return jsonify({'erro':'email,nome,tipo,senha obrigatórios'}), 400
    if tipo not in ['admin','default']:
        return jsonify({'erro':'tipo inválido'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'erro':'email já cadastrado'}), 400
    user = User(email=email, nome=nome, tipo=tipo)
    user.set_senha(senha)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@users_bp.route('/<int:user_id>', methods=['PUT'])
@auth_required
def update_user(user_id):
    from flask import request
    data = request.get_json() or {}
    user = User.query.get_or_404(user_id)
    # only admin or the user themself can edit
    if request.user.get('tipo') != 'admin' and request.user.get('id') != user.id:
        return jsonify({'erro':'Permitido apenas editar próprio usuário ou admin'}), 403
    nome = data.get('nome')
    email = data.get('email')
    if email and email != user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'erro':'email já cadastrado'}), 400
        user.email = email
    if nome:
        user.nome = nome
    db.session.commit()
    return jsonify(user.to_dict()), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@auth_required
def delete_user(user_id):
    from models.appointment_model import Appointment
    user = User.query.get_or_404(user_id)
    # only admin can delete and only if no atendimentos
    if request.user.get('tipo') != 'admin':
        return jsonify({'erro':'Apenas admin pode remover usuários'}), 403
    linked = Appointment.query.filter_by(usuario_id=user.id).first()
    if linked:
        return jsonify({'erro':'Usuário possui atendimentos vinculados e não pode ser removido'}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({'mensagem':'Usuário removido'}), 200

@users_bp.route('/<int:user_id>/reset-senha', methods=['POST'])
@auth_required
def reset_senha(user_id):
    # only admin can reset senhas
    if request.user.get('tipo') != 'admin':
        return jsonify({'erro':'Apenas admin pode resetar senhas'}), 403
    data = request.get_json() or {}
    new = data.get('senha')
    if not new:
        return jsonify({'erro':'senha nova obrigatória'}), 400
    user = User.query.get_or_404(user_id)
    user.set_senha(new)
    db.session.commit()
    return jsonify({'mensagem':'senha resetada'}), 200

@users_bp.route('/me/alterar-senha', methods=['POST'])
@auth_required
def change_senha():
    from flask import request
    data = request.get_json() or {}
    old = data.get('senha_antiga')
    new = data.get('senha_nova')
    if not all([old,new]):
        return jsonify({'erro':'senha_antiga e senha_nova obrigatórias'}), 400
    user = User.query.get_or_404(request.user.get('id'))
    if not user.check_senha(old):
        return jsonify({'erro':'senha antiga incorreta'}), 400
    user.set_senha(new)
    db.session.commit()
    return jsonify({'mensagem':'senha alterada'}), 200

@users_bp.route('/buscar', methods=['GET'])
@auth_required
def get_by_email():
    from flask import request
    email = request.args.get('email')
    if not email:
        return jsonify({'erro':'email é obrigatório'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'erro':'Usuário não encontrado'}), 404
    # only admin or own user
    if request.user.get('tipo') != 'admin' and request.user.get('id') != user.id:
        return jsonify({'erro':'Acesso negado'}), 403
    return jsonify(user.to_dict()), 200
