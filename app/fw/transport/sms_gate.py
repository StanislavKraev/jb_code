# -*- coding: utf-8 -*-
import requests

class SmsSender(object):

    def __init__(self, sms_gate_url, sms_gate_login, sms_gate_password_md5, sender):
        self.sms_gate_url = sms_gate_url
        self.sms_gate_login = sms_gate_login
        self.sms_gate_password_md5 = sms_gate_password_md5
        self.sender = sender

    def get_sms_cost(self, data):
        values_cost = data.copy()
        values_cost['cost'] = 1
        values_cost['login'] = self.sms_gate_login
        values_cost['psw'] = self.sms_gate_password_md5

        result = requests.post(self.sms_gate_url, data=values_cost, timeout=20)
        json_result = result.json()
        if not json_result or 'cost' not in json_result:
            raise Exception('Invalid answer: %s' % str(result.text))
        return float(json_result['cost'])

    def send(self, data):
        values = data.copy()
        values['login'] = self.sms_gate_login
        values['psw'] = self.sms_gate_password_md5
        values['sender'] = self.sender
        result = requests.post(self.sms_gate_url, data=values, timeout=20)

        json_result = result.json()
        if "error" in json_result and "error_code" in json_result:
            raise RuntimeError("Error sending sms: %s" % str(json_result['error_code']))
