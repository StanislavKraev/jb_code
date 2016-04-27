# -*- coding: utf-8 -*-
from fw.auth.user_manager import UserManager
from manage_commands import BaseManageCommand, get_single


class AddUserCommand(BaseManageCommand):
    NAME = "add_user"

    def run(self):
        self.logger.info(u"Добавление нового пользователя:")
        self.logger.info(u'=' * 50)
        username = get_single(u'username: ')
        password = get_single(u'password: ')
        try:
            UserManager.create_user(u"", u"", username, u"", u"", u"", password, u"")
        except Exception, ex:
            self.logger.exception(u'не удалось создать пользователя')
            exit(-1)
        self.logger.info(u'Пользователь добавлен')
