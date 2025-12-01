from flask import Blueprint, request, jsonify
from app import db
from models.patient_model import Patient
from utils.jwt_util import auth_required
from utils.pagination import paginate_query
from datetime import datetime

patients_bp = Blueprint('patients_bp', __name__)

def parse_date(date_str):
    return datetime.fromisoformat(date_str).date()

def field_is_missing(data, field):
    value = data.get(field)
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


@patients_bp.route('/', methods=['POST'])
@auth_required
def create_patient():
    data = request.get_json() or {}
    # all fields mandatory
    required = ['cpf','nome','email','telefone','data_nascimento','estado','cidade','bairro','cep','rua','numero']
    
    for f in required:
        if field_is_missing(data, f):
            return jsonify({'erro': f'Campo {f} obrigatório'}), 400

    # prevent duplicates
    if Patient.query.filter_by(cpf=data['cpf']).first():
        return jsonify({'erro':'CPF já cadastrado'}), 400
    if Patient.query.filter_by(email=data['email']).first():
        return jsonify({'erro':'Email já cadastrado'}), 400
    # create
    try:
        pn = parse_date(data['data_nascimento'])
    except Exception:
        return jsonify({'erro':'data_nascimento formato ISO (YYYY-MM-DD) esperado'}), 400
    patient = Patient(
        cpf=data['cpf'],
        nome=data['nome'],
        email=data['email'],
        telefone=data['telefone'],
        data_nascimento=pn,
        estado=data['estado'],
        cidade=data['cidade'],
        bairro=data['bairro'],
        cep=data['cep'],
        rua=data['rua'],
        numero=data['numero']
    )
    # if minor, responsible data required
    from datetime import date
    age = (date.today() - pn).days//365
    if age < 18:
        rfields = ['resp_cpf','resp_nome','resp_data_nascimento','resp_email','resp_telefone']
        for f in rfields:
            if not data.get(f):
                return jsonify({'erro':f'Paciente menor: campo {f} do responsável obrigatório'}), 400
        try:
            rd = parse_date(data['resp_data_nascimento'])
        except Exception:
            return jsonify({'erro':'resp_data_nascimento formato ISO (YYYY-MM-DD) esperado'}), 400
        # responsible cannot be minor
        r_age = (date.today() - rd).days//365
        if r_age < 18:
            return jsonify({'erro':'Responsável não pode ser menor de idade'}), 400
        patient.resp_cpf = data['resp_cpf']
        patient.resp_nome = data['resp_nome']
        patient.resp_data_nascimento = rd
        patient.resp_email = data['resp_email']
        patient.resp_telefone = data['resp_telefone']
    db.session.add(patient)
    db.session.commit()
    return jsonify(patient.to_dict()), 201

@patients_bp.route('/<int:patient_id>', methods=['PUT'])
@auth_required
def update_patient(patient_id):
    data = request.get_json() or {}
    patient = Patient.query.get_or_404(patient_id)
    # update allowed by any user
    # prevent duplicates on cpf/email if changing
    if data.get('cpf') and data.get('cpf') != patient.cpf:
        if Patient.query.filter_by(cpf=data['cpf']).first():
            return jsonify({'erro':'CPF já cadastrado'}), 400
        patient.cpf = data['cpf']
    if data.get('email') and data.get('email') != patient.email:
        if Patient.query.filter_by(email=data['email']).first():
            return jsonify({'erro':'Email já cadastrado'}), 400
        patient.email = data['email']
    # update other fields if provided
    for field in ['nome','telefone','estado','cidade','bairro','cep','rua','numero']:
        if data.get(field):
            setattr(patient, field, data.get(field))
    if data.get('data_nascimento'):
        try:
            patient.data_nascimento = parse_date(data['data_nascimento'])
        except:
            return jsonify({'erro':'data_nascimento formato ISO (YYYY-MM-DD) esperado'}), 400
    # handle responsible removal only if patient adult
    if 'remove_responsavel' in data and data.get('remove_responsavel')==True:
        if patient.is_minor():
            return jsonify({'erro':'Não é possível remover responsável enquanto paciente for menor'}), 400
        patient.resp_cpf = None
        patient.resp_nome = None
        patient.resp_data_nascimento = None
        patient.resp_email = None
        patient.resp_telefone = None
    db.session.commit()
    return jsonify(patient.to_dict()), 200

@patients_bp.route('/<int:patient_id>', methods=['DELETE'])
@auth_required
def delete_patient(patient_id):
    from models.appointment_model import Appointment
    patient = Patient.query.get_or_404(patient_id)
    linked = Appointment.query.filter_by(paciente_id=patient.id).first()
    if linked:
        return jsonify({'erro':'Paciente possui atendimentos vinculados e não pode ser removido'}), 400
    db.session.delete(patient)
    db.session.commit()
    return jsonify({'mensagem':'Paciente removido'}), 200

@patients_bp.route('/<int:patient_id>', methods=['GET'])
@auth_required
def get_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(patient.to_dict()), 200

@patients_bp.route('/', methods=['GET'])
@auth_required
def list_patients():
    query = Patient.query.order_by(Patient.id)
    return jsonify(paginate_query(query, lambda p: p.to_dict())), 200
