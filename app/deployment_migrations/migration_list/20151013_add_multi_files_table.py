# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Add m2m table for document files")

    sqldb.session.close()
    sqldb.engine.execute("""CREATE TABLE doc_files (
    doc_id VARCHAR NOT NULL,
    files_id VARCHAR NOT NULL,
    PRIMARY KEY (doc_id, files_id),
    FOREIGN KEY(doc_id) REFERENCES batch_docs (id) ON DELETE cascade,
    FOREIGN KEY(files_id) REFERENCES files (id) ON DELETE cascade
);""")


def rollback(config, logger):
    pass
