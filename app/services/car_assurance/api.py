# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_login import login_required

from fw.api import errors
from fw.api.args_validators import validate_arguments, ArgumentValidator, IntValidator
from fw.api.base_handlers import api_view
from services.car_assurance.db_models import CarAssurance, CarAssuranceBranch

car_assurance_bp = Blueprint('car_assurance', __name__)


@car_assurance_bp.route('/structures/insurances/', methods=['GET'])
@api_view
@login_required
@validate_arguments(
    type=ArgumentValidator(required=True),
    search=ArgumentValidator(required=False),
    limit=IntValidator(required=False, min_val=1, max_val=100500),
    offset=IntValidator(required=False, min_val=0, max_val=100500)
)
def get_car_insurances(search=None, limit=100, offset=0, **kwargs):
    if 'type' not in kwargs:
        raise errors.MissingRequiredParameter('type')
    type_arg = kwargs['type']
    if type_arg != 'osago':
        raise errors.InvalidParameterValue('type')

    if search:
        query = CarAssurance.query.filter_by(full_name=search).order_by(CarAssurance.full_name)
    else:
        query = CarAssurance.query.filter().order_by(CarAssurance.short_name)

    total = query.count()
    query = query.limit(limit).offset(offset)
    count = query.count()

    result = {
        'total': total,
        'count': count,
        'insurances': [{
            "id": i.id,
            "short_name": i.short_name,
            "full_name": i.full_name
        } for i in query]
    }
    return {'result': result}


@car_assurance_bp.route('/structures/insurances/branches/', methods=['GET'])
@api_view
@login_required
@validate_arguments(
    id=ArgumentValidator(required=True),
    region=ArgumentValidator(required=False),
    limit=IntValidator(required=False, min_val=1, max_val=100500),
    offset=IntValidator(required=False, min_val=0, max_val=100500)
)
def get_car_insurance_branches(region=None, limit=None, offset=None, **kwargs):
    if 'id' not in kwargs:
        raise errors.MissingRequiredParameter('id')
    id_arg = kwargs['id']

    if region:
        query = CarAssuranceBranch.query.filter_by(car_assurance_id=id_arg, region=region).order_by(CarAssuranceBranch.region).order_by(CarAssuranceBranch.title)
    else:
        query = CarAssuranceBranch.query.filter_by(car_assurance_id=id_arg).order_by(CarAssuranceBranch.region).order_by(CarAssuranceBranch.title)

    total = query.count()
    query = query.limit(limit).offset(offset)
    count = query.count()

    result = {
        'total': total,
        'count': count,
        'branches': [{
            "id": i.id,
            "title": i.title,
            "phone": i.phone,
            "address": i.address,
            "region": i.region
        } for i in query]
    }
    return {'result': result}
