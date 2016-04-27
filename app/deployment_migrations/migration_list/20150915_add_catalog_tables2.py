# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Create new models")

    sqldb.session.close()
    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS bik_catalog (
    id VARCHAR NOT NULL, 
    name VARCHAR NOT NULL, 
    okpo VARCHAR NOT NULL, 
    bik VARCHAR NOT NULL, 
    phone VARCHAR NOT NULL, 
    address VARCHAR NOT NULL, 
    kor_account VARCHAR NOT NULL, 
    PRIMARY KEY (id)
);""")

def rollback(config, logger):
    pass
