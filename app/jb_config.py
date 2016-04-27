# -*- coding: utf-8 -*-
from fw.settings import Configuration


class JBConfiguration(Configuration):
    def __init__(self, service_description, default_config_path, **kwargs):
        super(JBConfiguration, self).__init__(service_description, default_config_path)
        self.init_general_settings()
        self.init_web_server_settings()
        self.init_db_settings()
        self.init_mail_settings()
        self.init_sms_settings()
        self.init_social_settings()

    def init_general_settings(self):
        self.settings['MEMCACHED_HOST'] = self.get_from_config('GENERAL:MEMCACHED_HOST')
        self.settings['log_file_path'] = self.get_from_config('GENERAL:LOG_FILE_PATH', '/var/log/jb/jb.log')
        self.settings['bind_addr'] = self.get_from_config('GENERAL:BIND_ADDR', '/var/run/jb/app.sock')

        self.settings['DEBUG'] = self.get_from_config('GENERAL:DEBUG', 'False') == 'True'
        self.settings['STAGING'] = self.get_from_config('GENERAL:STAGING', 'False') == 'True'
        self.settings['TEST'] = self.get_from_config('GENERAL:TEST', 'False') == 'True'

        self.settings['PROD'] = not self.settings['DEBUG'] and not self.settings['STAGING'] and not self.settings['TEST']
        self.settings['LOG_LEVEL'] = self.LEVEL_NAME_VALUE_DICT[self.get_from_config('GENERAL:FILE_LOGGING_LEVEL', 'ERROR')]
        self.settings['CELERY_LOG_LEVEL'] = self.LEVEL_NAME_VALUE_DICT[self.get_from_config('GENERAL:CELERY_LOG_LEVEL', 'WARN')]
        self.settings['resources_path'] = self.get_from_config('GENERAL:RESOURCES_PATH')
        self.settings['PDF_BUILDER_PATH'] = self.get_from_config('GENERAL:PDF_BUILDER_PATH')
        self.settings['PDFTK_PATH'] = self.get_from_config('GENERAL:PDFTK_PATH')
        self.settings['DOCUMENT_STORAGE'] = self.get_from_config('GENERAL:DOCUMENT_STORAGE')
        self.settings['PRIVATE_STORAGE'] = self.get_from_config('GENERAL:PRIVATE_STORAGE')
        yurist_email_list = self.get_from_config('GENERAL:YURIST_EMAIL_LIST')
        yurist_email_list = [item.strip() for item in yurist_email_list.split(',') if item]
        self.settings['YURIST_EMAIL_LIST'] = yurist_email_list
        notarius_email_list = self.get_from_config('GENERAL:NOTARIUS_EMAIL_LIST')
        notarius_email_list = [item.strip() for item in notarius_email_list.split(',') if item]
        self.settings['NOTARIUS_EMAIL_LIST'] = notarius_email_list
        self.settings['CELERY_CONFIG_MODULE'] = self.get_from_config('GENERAL:CELERY_CONFIG_MODULE')
        self.settings['pdf_preview_watermark'] = self.get_from_config('GENERAL:PDF_PREVIEW_WATERMARK')
        self.settings['PDF_STAMPER_PATH'] = self.get_from_config('GENERAL:PDF_STAMPER_PATH')
        self.settings['celery_tasks_dir'] = self.get_from_config('GENERAL:CELERY_TASKS_DIR')
        self.settings['service_name'] = self.get_from_config('GENERAL:SERVICE_NAME')
        self.settings['ifns_admin_email'] = self.get_from_config('GENERAL:IFNS_ADMIN_EMAIL')
        self.settings['SITE_ROOT'] = self.get_from_config('GENERAL:SITE_ROOT')
        admin_email_list = self.get_from_config('GENERAL:ADMIN_EMAIL_LIST')
        admin_email_list = [item.strip() for item in admin_email_list.split(',') if item]
        self.settings['ADMIN_EMAIL_LIST'] = admin_email_list
        self.settings['RAISE_RIGHT_OFF'] = self.get_from_config('GENERAL:RAISE_RIGHT_OFF', 'False') == 'True'

        self.settings['YAD_ESHOP_PASSWORD'] = self.get_from_config('GENERAL:YAD_ESHOP_PASSWORD')
        yad_ip_list = self.get_from_config('GENERAL:YAD_IP_LIST')
        yad_ip_list = [item.strip() for item in yad_ip_list.split(',') if item]
        self.settings['YAD_IP_LIST'] = yad_ip_list

        self.settings['SEND_DOCS_TO_YURIST_DELAY_SECONDS'] = self.get_int_from_config('GENERAL:SEND_DOCS_TO_YURIST_DELAY_SECONDS', 60 * 60 * 2)
        self.settings['NOT_PAID_BATCH_NOTIFY_TIMEOUT_SECONDS'] = self.get_int_from_config('GENERAL:NOT_PAID_BATCH_NOTIFY_TIMEOUT_SECONDS', 3600 * 24)
        self.settings['NOT_PAID_BATCH_NOTIFY_DESIRED_TIME'] = self.get_from_config('GENERAL:NOT_PAID_BATCH_NOTIFY_DESIRED_TIME', '')

        self.settings['RUSSIAN_POST_API_LOGIN'] = self.get_from_config('GENERAL:RUSSIAN_POST_API_LOGIN')
        self.settings['RUSSIAN_POST_API_PASSWORD'] = self.get_from_config('GENERAL:RUSSIAN_POST_API_PASSWORD')

    def init_web_server_settings(self):
        self.settings['secret_key'] = self.get_from_config('WEB_SERVER:SECRET_KEY')
        self.settings['cookie_name'] = self.get_from_config('WEB_SERVER:SESSION_COOKIE_NAME')
        self.settings['SESSION_COOKIE_NAME'] = self.settings['cookie_name']
        self.settings['auth_session_lifetime'] = self.get_int_from_config('WEB_SERVER:PERMANENT_SESSION_LIFETIME', 86400)
        self.settings['PERMANENT_SESSION_LIFETIME'] = self.settings['auth_session_lifetime']

        self.settings['domain'] = self.get_from_config('WEB_SERVER:DOMAIN')
        self.settings['site_domain'] = self.settings['domain']
        self.settings['DOMAIN'] = self.get_from_config('WEB_SERVER:DOMAIN')
        self.settings['api_url'] = self.get_from_config('WEB_SERVER:API_URL')
        self.settings['UPLOAD_FOLDER'] = self.get_from_config('WEB_SERVER:UPLOAD_FOLDER')
        self.settings['STORAGE_URL'] = self.get_from_config('WEB_SERVER:STORAGE_URL')
        self.settings['socks_version'] = self.get_from_config('WEB_SERVER:PROXY_SOCKS_VERSION', u"5")

        self.settings['max_activation_link_length'] = self.get_int_from_config('API:MAX_ACTIVATION_LINK_LENGTH', 20)
        self.settings['digital_activation_link_length'] = self.get_int_from_config('API:DIGITAL_ACTIVATION_LINK_LENGTH', 4)
        self.settings['digital_activation_code_timeout'] = self.get_int_from_config('API:DIGITAL_ACTIVATION_CODE_TIMEOUT', 900)
        self.settings['email_activation_code_timeout'] = self.get_int_from_config('API:EMAIL_ACTIVATION_CODE_TIMEOUT', 86400)
        self.settings['max_activation_attempts_count'] = self.get_int_from_config('API:MAX_ACTIVATION_ATTEMPTS_COUNT', 3)

        self.settings['user_by_code_tries_count'] = self.get_int_from_config('API:USER_BY_CODE_TRIES_COUNT', 5)

        self.settings['WEB_SCHEMA'] = self.get_from_config('WEB_SERVER:WEB_SCHEMA', u'http')

        self.settings['SERVICE_NALOG_RU_URL'] = self.get_from_config('WEB_SERVER:SERVICE_NALOG_RU_URL', u"https://service.nalog.ru")
        self.settings['ORDER_NALOG_RU_URL'] = self.get_from_config('WEB_SERVER:ORDER_NALOG_RU_URL', u"http://order.nalog.ru")

        self.settings['MAX_CONTENT_LENGTH'] = self.get_int_from_config('API:MAX_CONTENT_LENGTH', 20 * 1024 * 1024)

    def init_db_settings(self):
        self.settings['db_user_name'] = self.get_from_config('DB:USER_NAME')
        self.settings['db_user_password'] = self.get_from_config('DB:PASSWORD')
        self.settings['db_host'] = self.get_from_config('DB:HOST')
        self.settings['db_name'] = self.get_from_config('DB:NAME')
        self.settings['SQLALCHEMY_DATABASE_URI'] = self.get_from_config('DB:POSTGRES')

    def init_mail_settings(self):
        self.settings['mailer_server'] = self.get_from_config('MAIL:SERVER')
        self.settings['mailer_smtp_user'] = self.get_from_config('MAIL:SMTP_USER')
        self.settings['mailer_reply_to'] = self.get_from_config('MAIL:REPLY_TO', self.settings['mailer_smtp_user']).decode('utf-8')
        self.settings['mailer_smtp_password'] = self.get_from_config('MAIL:SMTP_PASSWORD')

    def init_sms_settings(self):
        self.settings['sms_gate_address'] = self.get_from_config('SMS_GATE:SMS_GATE_ADDRESS')
        self.settings['sms_gate_user'] = self.get_from_config('SMS_GATE:SMS_GATE_USER')
        self.settings['sms_gate_password'] = self.get_from_config('SMS_GATE:SMS_GATE_PASSWORD')
        self.settings['sms_gate_sender'] = self.get_from_config('SMS_GATE:SMS_GATE_SENDER')

    def init_social_settings(self):
        self.settings['vk_api_version'] = self.get_from_config('SOCIAL_NETWORKS:VK_API_VERSION')
        self.settings['vk_app_id'] = self.get_int_from_config('SOCIAL_NETWORKS:VK_APP_ID')
        self.settings['vk_app_secret'] = self.get_from_config('SOCIAL_NETWORKS:VK_APP_SECRET')
        self.settings['vk_app_permissions'] = self.get_int_from_config('SOCIAL_NETWORKS:VK_APP_PERMISSIONS')
        self.settings['vk_auth_redirect_url'] = self.get_from_config('SOCIAL_NETWORKS:VK_AUTH_REDIRECT_URL')

        self.settings['facebook_app_id'] = self.get_int_from_config('SOCIAL_NETWORKS:FACEBOOK_APP_ID')
        self.settings['facebook_app_secret'] = self.get_from_config('SOCIAL_NETWORKS:FACEBOOK_APP_SECRET')
        self.settings['facebook_app_permissions'] = self.get_from_config('SOCIAL_NETWORKS:FACEBOOK_APP_PERMISSIONS')
        self.settings['facebook_auth_redirect_url'] = self.get_from_config('SOCIAL_NETWORKS:FACEBOOK_AUTH_REDIRECT_URL')
