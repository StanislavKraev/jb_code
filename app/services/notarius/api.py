# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from flask import Blueprint, current_app
from flask_login import login_required, current_user
import pytils
from fw.api import errors
from fw.api.args_validators import validate_arguments, ArgumentValidator, DateTypeValidator, DateTimeValidator
from fw.api.base_handlers import api_view
from fw.auth.social_services import SocialServiceBackends
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.fields.general_doc_fields import DocAddressField
from fw.documents.fields.simple_doc_fields import DocDateTimeField
from services.notarius.data_model.models import NotariusObject, NotariusBookingObject

notarius_bp = Blueprint('notarius', __name__)


@notarius_bp.route('/meeting/notarius/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def notarius_list(batch_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).scalar()
    if not batch:
        raise errors.InvalidParameterValue('batch_id')

    batch_manager = BatchManager.init(batch)
    assert batch_manager

    region = batch_manager.get_batch_region(batch_id)

    if not region:
        return {'result': []}
    query = NotariusObject.query.filter_by(region=region)
    result = [item.get_api_structure() for item in query]
    return {'result': result}


@notarius_bp.route('/meeting/notarius-in-region/', methods=['GET'])
@api_view
@login_required
@validate_arguments(region=ArgumentValidator())
def notarius_list_by_region(region=None):
    if not RFRegionsEnum.validate(region):
        raise errors.InvalidParameterValue('region')

    query = NotariusObject.query.filter_by(region=region)
    result = [item.get_api_structure() for item in query]
    return {'result': result}


@notarius_bp.route('/meeting/notarius/schedule/', methods=['GET'])
@api_view
@login_required
@validate_arguments(notarius_id=ArgumentValidator(required=True),
                    datetime=DateTypeValidator(required=True))
def notarius_schedule(notarius_id=None, **kwargs):
    empty_result = {'result': {"nearest_time": None,"slots": []}}

    dt = kwargs.get('datetime', None)
    if not dt:
        raise errors.InvalidParameterValue('datetime')

    notarius_db = NotariusObject.query.filter_by(id=notarius_id).scalar()
    if not notarius_db:
        raise errors.NotariusNotFound()

    now = datetime.utcnow()
    two_weeks = timedelta(14)

    dt = datetime(dt.year, dt.month, dt.day)
    if dt < now or dt > now + two_weeks:
        return empty_result

    day_from, day_to = dt, dt + timedelta(days=1)

    days = NotariusObject.get_notarius_schedule(notarius_db, day_from=day_from, day_to=day_to)
    days = filter(lambda y: y['slots'], sorted(days, key=lambda x: x['nearest_time']))
    days = filter(lambda x: datetime.strptime(x['nearest_time'], DocDateTimeField.FORMAT).date() == dt.date(), days)
    if not days:
        return empty_result

    return {'result': days[0]}


@notarius_bp.route('/meeting/notarius/create/', methods=['POST'])
@api_view
@login_required
@validate_arguments(
    notarius_id=ArgumentValidator(required=True),
    datetime=DateTimeValidator(required=True),
    batch_id=ArgumentValidator(required=False)
)
def notarius_reserve(notarius_id=None, **kwargs):
    dt = kwargs['datetime']
    batch_id = kwargs.get('batch_id', None)
    batch = None
    if batch_id:
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).scalar()
        if not batch:
            raise errors.BatchNotFound()

    notarius_db = NotariusObject.query.filter_by(id=notarius_id).scalar()
    if not notarius_db:
        raise errors.NotariusNotFound()

    target_day = datetime(dt.year, dt.month, dt.day)

    if NotariusObject.is_weekend(notarius_db, target_day):
        current_app.logger.info(u"NotariusObject.is_weekend -> skip")
        return {'result': None}

    time_slots = NotariusObject.make_slots(notarius_db, target_day, )
    if not time_slots:
        return {'result': None}

    found = False
    for slot in time_slots:
        if slot['slot_start'] == dt.strftime("%H:%M") and slot['slot_end'] == (dt + timedelta(seconds=1800)).strftime(
                "%H:%M"):
            found = True
            break
    if not found:
        current_app.logger.info(u"timeslot not found -> skip")
        return {'result': None}
    address = DocAddressField()
    address.parse_raw_value(notarius_db.address, api_data=False)
    booking = NotariusBookingObject(
        notarius=notarius_db,
        dt=dt,
        address=address.as_string(),
        owner=current_user,
        _discarded=False
    )
    if batch_id:
        NotariusBookingObject.query.filter_by(
            batch_id=batch_id,
            owner=current_user,
            _discarded=False
        ).delete()
        sqldb.session.commit()
        booking.batch_id=batch_id
    sqldb.session.add(booking)

    batch_data = batch.data or {}
    batch_data['lawyer_check'] = True
    DocumentBatchDbObject.query.filter_by(id=batch_id).update({
        'data': batch_data
    })
    sqldb.session.commit()
    result = booking.get_api_structure()
    rec_list = current_app.config['YURIST_EMAIL_LIST']

    if batch:
        attaches = BatchManager.get_shared_links_to_rendered_docs(batch, current_app.config, current_app.logger)
        llc_full_name = batch.data.get('full_name', "")
        social_link = SocialServiceBackends.get_user_social_network_profile_url(current_user.id)

        from fw.async_tasks import send_email
        for recipient in rec_list:
            send_email.send_email.delay(
                recipient,
                'notarius_batch_check',
                email=current_user.email,
                mobile=current_user.mobile,
                social_link=social_link,
                full_name=llc_full_name,
                notarius=unicode(notarius_db.title) or address.as_string(),
                booking_time=pytils.dt.ru_strftime(u"%d %B %Y в %H:%M", inflected=True, date=dt),
                attaches=attaches
            )
    return {'result': result}


@notarius_bp.route('/meeting/notarius/discard/', methods=['POST'])
@api_view
@login_required
@validate_arguments(booking_id=ArgumentValidator(required=True))
def notarius_discard(booking_id=None):
    result = NotariusBookingObject.query.filter_by(
        id=booking_id,
        owner=current_user,
        _discarded=False).update({
        '_discarded': True
    })
    sqldb.session.commit()

    if not result:
        raise errors.NotariusBookingNotFound()

    booking = NotariusBookingObject.query.filter_by(id=booking_id).scalar()
    if not booking:
        raise errors.NotariusBookingNotFound()

    notarius_id = booking.notarius_id
    dt = booking.dt
    address = booking.address
    rec_list = current_app.config['YURIST_EMAIL_LIST']
    company_full_name = u""
    batch_id = booking.batch_id
    if batch_id:
        try:
            batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
            if not batch:
                raise Exception()
            company_full_name = batch.data.get('full_name', '')
            batch_data = batch.data or {}
            batch_data['lawyer_check'] = False
            DocumentBatchDbObject.query.filter_by(id=batch_id).update({
                'data': batch_data
            })
            sqldb.session.commit()
        except Exception:
            current_app.logger.exception(u"Failed to get company name from batch")

    from fw.async_tasks import send_email
    for recipient in rec_list:
        send_email.send_email.delay(
            recipient,
            'notarius_discard',
            email=current_user.email,
            notarius_id=notarius_id,
            booking_time=pytils.dt.ru_strftime(u"%d %B %Y в %H:%M", inflected=True, date=dt) if dt else u"<неизвестно>",
            address=address,
            company_full_name=company_full_name
        )

    return {'result': True}


@notarius_bp.route('/meeting/notarius/booking/', methods=['GET'])
@api_view
@login_required
@validate_arguments(
    batch_id=ArgumentValidator(required=False)
)
def get_batch_notarius_booking(batch_id=None):
    result_list = []
    cur = NotariusBookingObject.query.filter_by(
        batch_id=batch_id,
        owner=current_user,
        _discarded=False) if batch_id else NotariusBookingObject.query.filter_by(
        owner=current_user,
        _discarded=False
    )
    for notarius_book in cur:
        result_list.append(notarius_book.get_api_structure())
    return {"result": result_list}
