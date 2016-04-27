# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Add indexes")

    sqldb.session.close()
    sqldb.engine.execute(u"""CREATE TABLE test_web_requests (
    id SERIAL NOT NULL,
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    data JSONB,
    url VARCHAR NOT NULL,
    PRIMARY KEY (id)
);""")


def rollback(config, logger):
    pass
