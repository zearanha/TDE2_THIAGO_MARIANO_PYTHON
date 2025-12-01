from flask import Blueprint, request, jsonify
from app import db
from models.appointment_model import Appointment, AppointmentProcedure
from models.procedure_model import Procedure
from models.patient_model import Patient
from models.user_model import User
from utils.jwt_util import auth_required
from utils.pagination import paginate_query
from datetime import datetime

appointments_bp = Blueprint('appointments_bp', __name__)

def calc_valor_total(proc_objs, tipo):
    total = 0.0
    for p in proc_objs:
        if tipo == 'plano':
            total += p.valor_plano
        else:
            total += p.valor_particular
    return total

@appointments_bp.route('/', methods=['POST'])
@auth_required
def create_appointment():
    data = request.get_json() or {}
    required = ['data_hora','paciente_id','procedimentos','tipo']
    for f in required:
        if not data.get(f):
            return jsonify({'erro':f'Campo {f} obrigatório'}), 400
    # parse date
    try:
        data_hora = datetime.fromisoformat(data['data_hora'])
    except Exception:
        return jsonify({'erro':'data_hora formato ISO (YYYY-MM-DDTHH:MM:SS) esperado'}), 400
    paciente = Patient.query.get(data['paciente_id'])
    if not paciente:
        return jsonify({'erro':'Paciente não encontrado'}), 404
    proc_ids = data['procedimentos']
    if not isinstance(proc_ids, list) or len(proc_ids)==0:
        return jsonify({'erro':'Deve existir pelo menos um procedimento associado'}), 400
    proc_objs = []
    for pid in proc_ids:
        p = Procedure.query.get(pid)
        if not p:
            return jsonify({'erro':f'Procedimento id {pid} não encontrado'}), 404
        proc_objs.append(p)
    tipo = data['tipo']
    if tipo not in ['plano','particular']:
        return jsonify({'erro':'tipo deve ser "plano" ou "particular"'}), 400
    if tipo == 'plano' and not data.get('numero_carteira'):
        return jsonify({'erro':'numero_carteira obrigatório para tipo plano'}), 400
    # create appointment
    usuario_id = request.user.get('id')
    valor_total = calc_valor_total(proc_objs, tipo)
    ap = Appointment(
        data_hora=data_hora,
        tipo=tipo,
        numero_carteira=data.get('numero_carteira'),
        valor_total=valor_total,
        usuario_id=usuario_id,
        paciente_id=paciente.id
    )
    db.session.add(ap)
    db.session.flush()  # get id
    for p in proc_objs:
        ap_proc = AppointmentProcedure(atendimento_id=ap.id, procedimento_id=p.id)
        db.session.add(ap_proc)
    db.session.commit()
    return jsonify(ap.to_dict()), 201

@appointments_bp.route('/<int:ap_id>', methods=['GET'])
@auth_required
def get_appointment(ap_id):
    ap = Appointment.query.get_or_404(ap_id)
    return jsonify(ap.to_dict()), 200

@appointments_bp.route('/', methods=['GET'])
@auth_required
def list_appointments():
    query = Appointment.query.order_by(Appointment.id)
    return jsonify(paginate_query(query, lambda a: a.to_dict())), 200

@appointments_bp.route('/<int:ap_id>', methods=['PUT'])
@auth_required
def update_appointment(ap_id):
    ap = Appointment.query.get_or_404(ap_id)
    # only creator or admin can edit
    if request.user.get('tipo') != 'admin' and request.user.get('id') != ap.usuario_id:
        return jsonify({'erro':'Apenas criador ou admin pode editar atendimento'}), 403
    data = request.get_json() or {}
    # allow changing procedimentos, data_hora, tipo, numero_carteira, paciente
    if data.get('data_hora'):
        try:
            ap.data_hora = datetime.fromisoformat(data['data_hora'])
        except:
            return jsonify({'erro':'data_hora formato ISO (YYYY-MM-DDTHH:MM:SS) esperado'}), 400
    if data.get('paciente_id'):
        p = Patient.query.get(data['paciente_id'])
        if not p:
            return jsonify({'erro':'Paciente não encontrado'}), 404
        ap.paciente_id = p.id
    if data.get('procedimentos') is not None:
        proc_ids = data['procedimentos']
        if not isinstance(proc_ids, list) or len(proc_ids)==0:
            return jsonify({'erro':'Deve existir pelo menos um procedimento associado'}), 400
        # remove old links
        AppointmentProcedure.query.filter_by(atendimento_id=ap.id).delete()
        proc_objs = []
        for pid in proc_ids:
            p = Procedure.query.get(pid)
            if not p:
                return jsonify({'erro':f'Procedimento id {pid} não encontrado'}), 404
            proc_objs.append(p)
        for p in proc_objs:
            ap_proc = AppointmentProcedure(atendimento_id=ap.id, procedimento_id=p.id)
            db.session.add(ap_proc)
        ap.valor_total = calc_valor_total(proc_objs, ap.tipo)
    if data.get('tipo'):
        if data['tipo'] not in ['plano','particular']:
            return jsonify({'erro':'tipo deve ser "plano" ou "particular"'}), 400
        ap.tipo = data['tipo']
    if ap.tipo == 'plano' and (not ap.numero_carteira) and not data.get('numero_carteira'):
        return jsonify({'erro':'numero_carteira obrigatório para tipo plano'}), 400
    if data.get('numero_carteira'):
        ap.numero_carteira = data.get('numero_carteira')
    db.session.commit()
    return jsonify(ap.to_dict()), 200

@appointments_bp.route('/<int:ap_id>', methods=['DELETE'])
@auth_required
def delete_appointment(ap_id):
    ap = Appointment.query.get_or_404(ap_id)
    # only creator or admin
    if request.user.get('tipo') != 'admin' and request.user.get('id') != ap.usuario_id:
        return jsonify({'erro':'Apenas criador ou admin pode remover atendimento'}), 403
    # delete linked procedures then appointment
    from models.appointment_model import AppointmentProcedure
    AppointmentProcedure.query.filter_by(atendimento_id=ap.id).delete()
    db.session.delete(ap)
    db.session.commit()
    return jsonify({'mensagem':'Atendimento removido'}), 200

@appointments_bp.route('/between', methods=['GET'])
@auth_required
def list_between_dates():
    # expects ?start=YYYY-MM-DD&end=YYYY-MM-DD
    start = request.args.get('start')
    end = request.args.get('end')
    if not start or not end:
        return jsonify({'erro':'Parâmetros start e end obrigatórios'}), 400
    try:
        s = datetime.fromisoformat(start)
        e = datetime.fromisoformat(end)
    except:
        return jsonify({'erro':'Formato de data inválido, use ISO (YYYY-MM-DD)'}), 400
    query = Appointment.query.filter(Appointment.data_hora >= s, Appointment.data_hora <= e).order_by(Appointment.data_hora)
    return jsonify(paginate_query(query, lambda a: a.to_dict())), 200
