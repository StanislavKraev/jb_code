# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_login import login_required, current_user
from fw.api import errors

from fw.api.args_validators import validate_arguments, ArgumentValidator
from fw.api.base_handlers import api_view
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from services.russian_post.db_models import RussianPostTrackingItem

russian_post_bp = Blueprint('russian_post_bp', __name__)


@russian_post_bp.route('/external/russianpost/mail/status/', methods=['GET'])
@api_view
@login_required
@validate_arguments(
    batch_id=ArgumentValidator(required=True),
    #tracking=ArgumentValidator(required=True)
)
def get_mail_status(batch_id=None):
    tracking = RussianPostTrackingItem.query.filter(
        RussianPostTrackingItem.batch_id == batch_id,
        RussianPostTrackingItem.owner_id != 111111
    ).first()    # not scalar
    if not tracking:
        raise errors.PostTrackingItemNotFound()

    return {'result': {
        'status': tracking.status,
        'status_caption': tracking.status_caption
    }}


@russian_post_bp.route('/external/russianpost/mail/track/', methods=['POST'])
@api_view
@login_required
@validate_arguments(
    batch_id=ArgumentValidator(required=True),
    tracking=ArgumentValidator(required=True)
)
def track_mail_status(batch_id=None, tracking=None):
    tracking = tracking.strip()
    if not tracking:
        raise errors.InvalidParameterValue('tracking')

    tracking_item = RussianPostTrackingItem.query.filter(
        RussianPostTrackingItem.batch_id == batch_id,
        RussianPostTrackingItem.tracking == tracking,
        RussianPostTrackingItem.owner_id != 111111
    ).first()

    if tracking_item:
        return {
            'result': True
        }

    RussianPostTrackingItem.query.filter(
        RussianPostTrackingItem.batch_id == batch_id,
        RussianPostTrackingItem.owner == current_user
    ).delete()
    sqldb.session.commit()

    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, deleted=False).scalar()
    if not batch:
        raise errors.BatchNotFound()

    new_tracking = RussianPostTrackingItem(
        batch=batch,
        owner=current_user,
        tracking=tracking
    )

    sqldb.session.add(new_tracking)
    sqldb.session.commit()

    from services.russian_post.async_tasks import get_tracking_info_async
    get_tracking_info_async.delay(batch_id=batch.id)

    return {'result': True}
