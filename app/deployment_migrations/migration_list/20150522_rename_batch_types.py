# -*- coding: utf-8 -*-
from fw.documents.db_fields import DocumentBatchDbObject


def forward(config, logger):
    logger.debug(u"rename batch types (new_llc -> llc, new_ip -> ie)")

    DocumentBatchDbObject.get_collection(db).update({'batch_type': 'new_llc'}, {'$set': {'batch_type': 'llc'}}, multi=True)
    DocumentBatchDbObject.get_collection(db).update({'batch_type': 'new_ip'}, {'$set': {'batch_type': 'ie'}}, multi=True)


def rollback(config, logger):
    logger.debug(u"Rolling back migration")

    DocumentBatchDbObject.get_collection(db).update({'batch_type': 'llc'}, {'$set': {'batch_type': 'new_llc'}}, multi=True)
    DocumentBatchDbObject.get_collection(db).update({'batch_type': 'ie'}, {'$set': {'batch_type': 'new_ip'}}, multi=True)
