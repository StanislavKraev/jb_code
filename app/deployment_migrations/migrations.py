# -*- coding: utf-8 -*-

import os
import sys
from fw.db.sql_base import db as sqldb
from deployment_migrations.data import Migration
from deployment_migrations.models import MigrationState


class MigrationManager(object):
    @staticmethod
    def migrate_to(config, logger, version=None):
        sqldb.engine.execute(u"create table if not exists migration_state (id SERIAL NOT NULL, value VARCHAR NULL);")
        cur_state = MigrationState.query.filter_by(id=1).scalar()
        assert cur_state
        current_version = cur_state.value

        migration_list = MigrationManager.load_migration_list(config)
        migration_list = sorted(migration_list, key=lambda x: unicode(x))

        for migration in migration_list:
            if current_version < migration.version:
                # noinspection PyBroadException
                try:
                    migration.run(config, logger)
                except Exception:
                    logger.exception(u"Failed to run migration %s. Break." % migration.version)
                    return

                # noinspection PyBroadException
                try:
                    MigrationState.query.filter_by(id=1).update({
                        'value': unicode(migration.version)
                    })
                    sqldb.session.commit()
                    current_version = migration.version
                except Exception:
                    logger.exception(
                        u"Failed to set current version after successfull migration %s. Break." % migration.version)
                    return
        return current_version

    @staticmethod
    def load_migration_list(config):
        migrations = []
        migrations_list_dir = config.get('MIGRATION_LIST_DIR', os.path.normpath(
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'migration_list'))))
        sys.path.append(migrations_list_dir)
        for file_name in os.listdir(migrations_list_dir):
            if not os.path.splitext(file_name)[1] == '.py' or not file_name[0].isdigit():
                continue
            module_name = os.path.splitext(file_name)[0]
            module = __import__(module_name)
            forward_migration = getattr(module, 'forward')
            rollback_migration = getattr(module, 'rollback')
            is_skip = getattr(module, 'skip', False)
            if is_skip:
                continue
            migrations.append(Migration(module_name, forward_migration, rollback_migration))
        return migrations
