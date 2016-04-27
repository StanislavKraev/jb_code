# -*- coding: utf-8 -*-
from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Add table for authorization url")

    sqldb.session.close()
    sqldb.engine.execute(u"""CREATE TABLE authorization_url (
    id VARCHAR NOT NULL,
    url VARCHAR,
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    expire_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    used_times INTEGER NOT NULL,
    owner_id INTEGER,
    PRIMARY KEY (id),
    FOREIGN KEY(owner_id) REFERENCES authuser (id)
)""")


def rollback(config, logger):
    sqldb.session.close()
    sqldb.engine.execute("DROP table authorization_url;")

