# -*- coding: utf-8 -*-
from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Add table for celery scheduler")

    sqldb.session.close()
    sqldb.engine.execute(u"""CREATE TABLE celery_scheduled_task (
    id VARCHAR NOT NULL,
    task_name VARCHAR,
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    eta TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    sent BOOLEAN,
    args JSONB,
    kwargs JSONB,
    PRIMARY KEY (id)
)""")


def rollback(config, logger):
    sqldb.session.close()
    sqldb.engine.execute("DROP table celery_scheduled_task;")
