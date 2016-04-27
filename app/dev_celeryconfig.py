# -*- coding: utf-8 -*-
from datetime import timedelta
import sys
import os
import external_tools
from fw.async_tasks.celery_utils import make_app
from fw.transport.mail import Mailer
from fw.transport.sms_gate import SmsSender
from jb_config import JBConfiguration

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


CELERY_IMPORTS = (
    "fw.async_tasks.rendering",
    "fw.async_tasks.send_email",
    "fw.async_tasks.test_task",
    "fw.async_tasks.send_sms_task",
    "fw.async_tasks.periodic_tasks",
    "fw.async_tasks.not_paid_check_send",
    "fw.async_tasks.core_tasks",
    "fw.async_tasks.scheduler",

    "services.ifns.async_tasks.ifns_booking_tasks",
    "services.car_assurance.async_tasks",
    "services.yurist.async_tasks.yurist_check_send",
    "services.russian_post.async_tasks"
)

CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "postgresql://postgres:postgres@localhost/jb"
BROKER_URL = 'sqla+postgresql://postgres:postgres@localhost/jb'

CELERY_TASK_RESULT_EXPIRES = None

CELERY_IGNORE_RESULT = True
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = False

CELERY_QUEUE_HA_POLICY = 'all'

CELERY_DISABLE_RATE_LIMITS = True

CELERY_SEND_EVENTS = True

CELERY_SEND_TASK_SENT_EVENT = True

DEFAULT_CONFIG_PATH = '/etc/jurbureau/config.cfg'

config = JBConfiguration('Jur bureau async tasks service', DEFAULT_CONFIG_PATH)

SETTINGS_STORAGE = config

MAILER = Mailer(config['mailer_server'], config['mailer_smtp_user'], config['mailer_smtp_password'])
SMS_SENDER = SmsSender(config['sms_gate_address'], config['sms_gate_user'], config['sms_gate_password'], config['sms_gate_sender'])

CELERYD_TASK_TIME_LIMIT = 60
CELERYD_TASK_SOFT_TIME_LIMIT = 45

CELERY_TIMEZONE = 'UTC'

EXTERNAL_TOOLS = external_tools

CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'fw.async_tasks.periodic_tasks.check_frozen_batch_finalisation',
        'schedule': timedelta(seconds=150)
    },
    'post-items-track': {
        'task': 'services.russian_post.async_tasks.get_tracking_info_async',
        'schedule': timedelta(seconds=30)
    },
    'check-scheduled-tasks': {
        'task': 'fw.async_tasks.core_tasks.check_scheduled_tasks',
        'schedule': timedelta(seconds=5)
    },
    'check_doc_group_render': {
        'task': 'fw.async_tasks.rendering.batch_group_gen_check_task',
        'schedule': timedelta(seconds=600)
    },
    'get_fss_task': {
        'task': 'fw.async_tasks.periodic_tasks.get_fss_task',
        'schedule': timedelta(seconds=111)
    },
    'clean_kombu_messages': {
        'task': 'fw.async_tasks.periodic_tasks.clean_kombu_messages',
        'schedule': timedelta(hours=4)
    }
}

flask_app = make_app(config, external_tools)