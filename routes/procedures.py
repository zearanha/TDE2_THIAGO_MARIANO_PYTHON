from flask import Blueprint, request, jsonify
from app import db
from models.procedure_model import Procedure
from models.appointment_model import AppointmentProcedure, Appointment
from utils.jwt_util import auth_required
from utils.pagination import paginate_query

procedures_bp = Blueprint('procedures_bp', __name__)

@procedures_bp.route('/', methods=['POST'])
@auth_required
def create_procedure():
    if request.user.get('tipo') != 'admin':
        return jsonify({'erro':'Apenas admin pode criar procedimentos'}), 403
    data = request.get_json() or {}
    required = ['nome','descricao','valor_plano','valor_particular']
    for f in required:
        if not data.get(f):
            return jsonify({'erro':f'Campo {f} obrigatório'}), 400
    if Procedure.query.filter_by(nome=data['nome']).first():
        return jsonify({'erro':'nome de procedimento já existe'}), 400
    proc = Procedure(
        nome=data['nome'],
        descricao=data['descricao'],
        valor_plano=float(data['valor_plano']),
        valor_particular=float(data['valor_particular'])
    )
    db.session.add(proc)
    db.session.commit()
    return jsonify(proc.to_dict()), 201

@procedures_bp.route('/<int:proc_id>', methods=['PUT'])
@auth_required
def update_procedure(proc_id):
    if request.user.get('tipo') != 'admin':
        return jsonify({'erro':'Apenas admin pode editar procedimentos'}), 403
    proc = Procedure.query.get_or_404(proc_id)
    data = request.get_json() or {}
    if data.get('nome') and data.get('nome') != proc.nome:
        if Procedure.query.filter_by(nome=data['nome']).first():
            return jsonify({'erro':'nome de procedimento já existe'}), 400
        proc.nome = data['nome']
    for f in ['descricao','valor_plano','valor_particular']:
        if data.get(f) is not None:
            setattr(proc, f, data.get(f))
    db.session.commit()
    return jsonify(proc.to_dict()), 200

@procedures_bp.route('/<int:proc_id>', methods=['DELETE'])
@auth_required
def delete_procedure(proc_id):
    if request.user.get('tipo') != 'admin':
        return jsonify({'erro':'Apenas admin pode remover procedimentos'}), 403
    # do not remove if used in atendimentos
    used = AppointmentProcedure.query.filter_by(procedimento_id=proc_id).first()
    if used:
        return jsonify({'erro':'Procedimento já utilizado em atendimentos e não pode ser removido'}), 400
    proc = Procedure.query.get_or_404(proc_id)
    db.session.delete(proc)
    db.session.commit()
    return jsonify({'mensagem':'Procedimento removido'}), 200

@procedures_bp.route('/<int:proc_id>', methods=['GET'])
@auth_required
def get_procedure(proc_id):
    proc = Procedure.query.get_or_404(proc_id)
    return jsonify(proc.to_dict()), 200

@procedures_bp.route('/', methods=['GET'])
@auth_required
def list_procedures():
    query = Procedure.query.order_by(Procedure.id)
    return jsonify(paginate_query(query, lambda p: p.to_dict())), 200
