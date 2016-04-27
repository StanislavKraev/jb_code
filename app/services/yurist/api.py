# -*- coding: utf-8 -*-

from datetime import datetime
import json
from flask import Blueprint, current_app
from flask_login import login_required, current_user
from fw.api import errors
from fw.api.args_validators import validate_arguments, BoolTypeValidator, ArgumentValidator
from fw.api.base_handlers import api_view
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from fw.storage.file_storage import FileStorage
from services.yurist import yurist_manager
from services.yurist.data_model.enums import YuristBatchCheckStatus
from services.yurist.data_model.fields import YuristBatchCheck
from services.yurist.data_model.models import YuristBatchCheckObject, YuristCheckFilesObject

yurist_bp = Blueprint('yurist', __name__)


@yurist_bp.route('/batch/yurist/set/', methods=['POST'])
@api_view
@login_required
@validate_arguments(
    batch_id=ArgumentValidator(required=True),
    check=BoolTypeValidator(required=True),
    file_list=ArgumentValidator(required=False),
    typos_correction=BoolTypeValidator(required=False)
)
def yurist_set(batch_id=None, check=None, file_list=None, typos_correction=False):
    typos_correction = bool(typos_correction)
    batch_db = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch_db:
        raise errors.BatchNotFound()

    if check:
        new = True
        # search for any active check
        cur_check_obj = YuristBatchCheckObject.query.filter(
            YuristBatchCheckObject.batch_id == batch_id,
            YuristBatchCheckObject.status.notin_(YuristBatchCheckStatus.FINAL_STATUSES)
        ).order_by(YuristBatchCheckObject.create_date.desc()).first()

        if cur_check_obj:
            new = False

        real_file_list = []
        file_descr = []
        if file_list:
            try:
                file_list_data = json.loads(file_list)
                for file_obj in file_list_data:
                    file_id = file_obj['id']
                    file_obj = FileStorage.get_file(file_id)
                    if file_obj:
                        real_file_list.append(file_obj)
                    else:
                        current_app.logger.warn(u"Failed to find file with id %s" % file_id)
            except Exception:
                current_app.logger.exception(u"Failed to parse file list: %s" % file_list)
        # Insert new check
        if new:
            yurist_batch_check = YuristBatchCheckObject(**{
                'batch_id': batch_id,
                'create_date': datetime.utcnow(),
                'status': YuristBatchCheckStatus.YBS_WAIT,
                'typos_correction': typos_correction
            })
            sqldb.session.add(yurist_batch_check)
            for file_obj in real_file_list:
                attach = YuristCheckFilesObject()
                attach.files_id = file_obj.id
                yurist_batch_check.attached_files.append(attach)
        else:
            YuristCheckFilesObject.query.filter_by(check_id=cur_check_obj.id).delete()
            for file_obj in real_file_list:
                attach = YuristCheckFilesObject()
                attach.files_id = file_obj.id
                cur_check_obj.attached_files.append(attach)
            cur_check_obj.create_date = datetime.utcnow()
            cur_check_obj.typos_correction = typos_correction
            cur_check_obj.status = YuristBatchCheckStatus.YBS_WAIT

        sqldb.session.commit()
        yurist_manager.yurist_check(current_app.config, batch_db, real_file_list, current_app.logger)
    else:
        # search for active check
        cur_check_obj = YuristBatchCheckObject.query.filter(
            YuristBatchCheckObject.batch_id == batch_id,
            YuristBatchCheckObject.status.notin_(YuristBatchCheckStatus.FINAL_STATUSES)
        ).order_by(YuristBatchCheckObject.create_date.desc()).first()
        # If found any: set status to refused
        if cur_check_obj:
            cur_check_obj.status = YuristBatchCheckStatus.YBS_REFUSED
            sqldb.session.commit()
            return {'result': True}

    return {'result': True}


@yurist_bp.route('/batch/yurist/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(required=True))
def yurist_get(batch_id=None):
    batch_db = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch_db:
        raise errors.BatchNotFound()
    # get active or last refused
    check_obj = YuristBatchCheckObject.query.filter(
        YuristBatchCheckObject.batch_id == batch_id,
        YuristBatchCheckObject.status.notin_(YuristBatchCheckStatus.FINAL_STATUSES)
    ).first()
    if not check_obj:
        # get the last one
        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_id).order_by(
            YuristBatchCheckObject.create_date.desc()
        ).first()

    if check_obj:
        booking = YuristBatchCheck.db_obj_to_field(check_obj).get_api_structure()
        if booking['status'] == YuristBatchCheckStatus.YBS_WAIT:
            booking['status'] = YuristBatchCheckStatus.YBS_IN_PROGRESS
        return {'result': booking}

    return {'result': {
        'batch_id': batch_id,
        'attached_files': [],
        'typos_correction': False,
        'status': YuristBatchCheckStatus.YBS_NEW
    }}


@yurist_bp.route('/batch/yurist/commit/', methods=['GET'])
@api_view
@validate_arguments(
    batch_check_id=ArgumentValidator(required=True),
    success=BoolTypeValidator(required=True),
)
def yurist_commit(batch_check_id=None, success=None):
    if success:
        for i in YuristBatchCheckObject.query.filter(
            YuristBatchCheckObject.id == batch_check_id,
            YuristBatchCheckObject.status.in_([
                YuristBatchCheckStatus.YBS_IN_PROGRESS,
                YuristBatchCheckStatus.YBS_FAILED,
                YuristBatchCheckStatus.YBS_WAIT])
        ):
            i.status = YuristBatchCheckStatus.YBS_SUCCESS

        for i in YuristBatchCheckObject.query.filter(
            YuristBatchCheckObject.batch_id == batch_check_id,
            YuristBatchCheckObject.status.in_([
                YuristBatchCheckStatus.YBS_IN_PROGRESS,
                YuristBatchCheckStatus.YBS_FAILED,
                YuristBatchCheckStatus.YBS_WAIT])
        ):
            i.status = YuristBatchCheckStatus.YBS_SUCCESS
    else:
        for i in YuristBatchCheckObject.query.filter(
            YuristBatchCheckObject.id == batch_check_id,
            YuristBatchCheckObject.status.in_([
                YuristBatchCheckStatus.YBS_IN_PROGRESS,
                YuristBatchCheckStatus.YBS_SUCCESS,
                YuristBatchCheckStatus.YBS_WAIT])
        ):
            i.status = YuristBatchCheckStatus.YBS_FAILED

        for i in YuristBatchCheckObject.query.filter(
            YuristBatchCheckObject.batch_id == batch_check_id,
            YuristBatchCheckObject.status.in_([
                YuristBatchCheckStatus.YBS_IN_PROGRESS,
                YuristBatchCheckStatus.YBS_SUCCESS,
                YuristBatchCheckStatus.YBS_WAIT])
        ):
            i.status = YuristBatchCheckStatus.YBS_FAILED
    sqldb.session.commit()

    return {'new_status': YuristBatchCheckStatus.YBS_SUCCESS if success else YuristBatchCheckStatus.YBS_FAILED}

