# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Add indexes")

    sqldb.session.close()
    sqldb.engine.execute(u"create index doc_batch_owner_idx on doc_batch (_owner_id);")
    sqldb.engine.execute(u"create index private_person_owner_idx on private_person (_owner_id);")
    sqldb.engine.execute(u"create index company_object_owner_idx on company_object (_owner_id);")
    sqldb.engine.execute(u"create index batch_docs_owner_idx on batch_docs (_owner_id);")


def rollback(config, logger):
    pass

