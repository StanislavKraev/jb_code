# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Create new models")

    sqldb.session.close()
    sqldb.engine.execute(u"""CREATE TABLE pay_info (
    id SERIAL NOT NULL,
    user_id INTEGER,
    batch_id VARCHAR NOT NULL,
    pay_record_id INTEGER NOT NULL,
    payment_provider INTEGER NOT NULL,
    dt TIMESTAMP WITHOUT TIME ZONE,
    service_type VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES authuser (id),
    FOREIGN KEY(batch_id) REFERENCES doc_batch (id)
);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_pay_info_user_id;""")
    sqldb.engine.execute(u"""CREATE INDEX ix_pay_info_user_id ON pay_info (user_id);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_pay_info_pay_record_id;""")
    sqldb.engine.execute(u"""CREATE INDEX ix_pay_info_pay_record_id ON pay_info (pay_record_id);""")


def rollback(config, logger):
    pass
