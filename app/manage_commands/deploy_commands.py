# -*- coding: utf-8 -*-
from deployment_migrations.migrations import MigrationManager
from manage_commands import BaseManageCommand


class MigrateCommand(BaseManageCommand):
    NAME = "migrate"

    def run(self):
        self.logger.info(u"Запуск миграции")
        self.logger.info(u'=' * 50)

        current_version = MigrationManager.migrate_to(self.config, self.logger)

        self.logger.info(u"Система мигрирована до версии %s" % current_version)

