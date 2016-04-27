# -*- coding: utf-8 -*-
from datetime import datetime
import json

from celery.exceptions import SoftTimeLimitExceeded
from celery import current_app as celery
import requests

from fw.documents.db_fields import DocumentBatchDbObject
from services.car_assurance.db_models import CarAssurance

celery.config_from_envvar('CELERY_CONFIG_MODULE')

@celery.task()
def get_policy_info_async(policy_series, policy_number, event_data, batch_id, async=True, logger = None):
    from fw.documents.batch_manager import BatchManager
    app = celery.conf['flask_app']()
    logger = logger or celery.log.get_default_logger()
    if not policy_number or not policy_series:
        return
    with app.app_context():
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id, deleted=False).scalar()
        try:
            try:
                result_data = app.external_tools.check_car_policy(policy_series, policy_number, timeout=2.0 if not async else 20.0)
            except requests.exceptions.RequestException, ex:
                BatchManager.handle_event(batch_id, "on_policy_info_receive_timeout", event_data, logger, config=app.config)
                return False

            if not result_data:
                BatchManager.handle_event(batch_id, "on_policy_info_receive_fail", event_data, logger, config=app.config)
                return False

            logger.info(u"get policy info returned: %s" % json.dumps(result_data, default=lambda x: unicode(x)))
            insurance_name = result_data.get('insCompanyName', u"")
            if not insurance_name:
                raise Exception(u"Failed to get insurance: empty name returned")

            insurance = CarAssurance.query.filter_by(connection_name=insurance_name).first()
            if not insurance:
                raise Exception(u"Failed to get insurance from db by name: %s" % insurance_name)
            insurance_id = insurance.id

            policy_date = result_data['policyBeginDate'] or None
            policy_date_str = ""
            if policy_date:
                policy_date_dt = datetime.strptime(policy_date, "%d.%m.%Y")
                policy_date_str = policy_date_dt.strftime("%Y-%m-%d")
            returned_policy_series = result_data['bsoSeries']
            returned_policy_number = result_data['bsoNumber']
            if not policy_date_str or not returned_policy_number or not returned_policy_series:
                BatchManager.handle_event(batch_id, "on_policy_info_receive_fail", event_data, logger, config=app.config)
                return False

            event_data = {
                'policy_series': result_data['bsoSeries'],
                'policy_number': result_data['bsoNumber'],
                'insurance_id': insurance_id,
                'insurance_name': insurance_name,
                'policy_date': policy_date_str
            }
            BatchManager.handle_event(batch_id, "on_policy_info_received", event_data, logger, config=app.config)
        except SoftTimeLimitExceeded:
            BatchManager.handle_event(batch_id, "on_policy_info_receive_fail", event_data, logger, config=app.config)
        except Exception:
            BatchManager.handle_event(batch_id, "on_policy_info_receive_fail", event_data, logger, config=app.config)
            raise
