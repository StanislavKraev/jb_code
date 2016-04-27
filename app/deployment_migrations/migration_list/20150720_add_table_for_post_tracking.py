# -*- coding: utf-8 -*-
from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Add table for post tracking")

    sqldb.session.close()
    sqldb.engine.execute(u"""CREATE TABLE rus_post_tracking (
    id SERIAL NOT NULL,
    tracking VARCHAR NOT NULL,
    creation_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    batch_id VARCHAR,
    owner_id INTEGER NOT NULL,
    status VARCHAR NOT NULL,
    status_caption VARCHAR NOT NULL,
    status_change_dt TIMESTAMP WITHOUT TIME ZONE,
    last_check_dt TIMESTAMP WITHOUT TIME ZONE,
    last_location VARCHAR,
    tracking_type VARCHAR,
    PRIMARY KEY (id),
    FOREIGN KEY(batch_id) REFERENCES doc_batch (id),
    FOREIGN KEY(owner_id) REFERENCES authuser (id)
)""")


def rollback(config, logger):
    sqldb.session.close()
    sqldb.engine.execute("DROP table rus_post_tracking;")
