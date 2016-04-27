# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from fw.storage.file_storage import FileStorage
from services.ifns.data_model.models import IfnsCatalogObject, IfnsBookingObject
from services.notarius.data_model.models import NotariusObject, NotariusBookingObject
from services.yurist.data_model.models import YuristBatchCheckObject, YuristCheckFilesObject


def forward(config, logger):
    logger.debug(u"Migrate ifns models")

    ifns_cat_col = db['ifns_catalog']
    IfnsCatalogObject.query.delete()
    sqldb.session.commit()
    for old_cat in ifns_cat_col.find():
        new_cat = IfnsCatalogObject(
            id=str(old_cat['_id']),
            updated=old_cat['updated'],
            code=old_cat['code'],
            comment=old_cat.get('comment'),
            tel=old_cat.get('tel', []),
            name=old_cat.get('name'),
            rof=old_cat.get('rof'),
            rou=old_cat.get('rou'),
            plat=old_cat.get('plat'),
            address=old_cat.get('address'),
            region=old_cat.get('region')
        )
        sqldb.session.add(new_cat)
    sqldb.session.commit()

    ifns_booking_col = db['ifns_booking']
    IfnsBookingObject.query.delete()
    sqldb.session.commit()
    for old_book in ifns_booking_col.find():
        batch_id = old_book.get('batch_id')
        if batch_id:
            batch_id = str(batch_id)
        if 'code' not in old_book or 'date' not in old_book or 'service' not in old_book:
            continue

        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
        if not batch:
            continue

        new_book = IfnsBookingObject(
            id=str(old_book['_id']),
            batch_id=batch_id,
            code=old_book['code'],
            date=old_book['date'],
            service=old_book['service'],
            _discarded=old_book['_discarded'],
            phone=old_book.get('phone'),
            window=old_book.get('window'),
            address=old_book.get('address'),
            service_id=old_book['service_id'],
            ifns=old_book.get('ifns'),
            how_to_get=old_book.get('how_to_get'),
            reg_info=old_book.get('reg_info')
        )
        sqldb.session.add(new_book)
    sqldb.session.commit()


def rollback(config, logger):
    pass
