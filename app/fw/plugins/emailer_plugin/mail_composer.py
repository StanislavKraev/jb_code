# -*- coding: utf-8 -*-
from fw.async_tasks import send_email


class EmailComposer(object):
    def __init__(self, email_type, logger):
        self.email_type = email_type
        self.logger = logger

    def send_email(self, target_emails, batch_id, event_data, retry_count, retry_delay=300):
        raise NotImplementedError()


class SomeEmailComposer(EmailComposer):
    def send_email(self, recipients, batch_id, event_data, max_retries, retry_timeout_seconds=None, silent=False,
                   template_data=None):
        assert max_retries >= 0
        for addr in recipients:
            send_email.send_email_plugin.delay(batch_id, event_data, addr, self.email_type, max_retries=max_retries,
                                               retry_timeout_seconds=retry_timeout_seconds, silent=silent,
                                               template_data=template_data)


def create_composer(email_type, logger):
    return SomeEmailComposer(email_type, logger)
