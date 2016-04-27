# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Create new models")

    sqldb.session.close()

    sqldb.engine.execute(u"""ALTER TABLE payment_subscription
    ADD COLUMN pay_record_id INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN payment_provider INTEGER NOT NULL DEFAULT 0
;""")


def rollback(config, logger):
    pass
