# -*- coding: utf-8 -*-
from datetime import datetime

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from services.partners.models import StampPartnersObject, AccountantPartnersObject, BankPartnersObject, \
    BankPartnersServiceObject, BankPartnerRequestObject


def forward(config, logger):
    logger.debug(u"Migrate partners models")

    stamp_partners = db['stamp_partners']
    StampPartnersObject.query.delete()
    sqldb.session.commit()
    for old_partner in stamp_partners.find():
        new_partner = StampPartnersObject(
            id=str(old_partner['_id']),
            region=old_partner.get('region'),
            enabled=old_partner.get('enabled', False),
            sort_index=old_partner.get('sort_index', 1),
            link=old_partner.get('region', ''),
            banner=old_partner.get('banner', ''),
            title=old_partner.get('title', ''),
            created=old_partner.get('created', datetime.utcnow())
        )
        sqldb.session.add(new_partner)
    sqldb.session.commit()

    accountant_partners = db['accountant_partners']
    AccountantPartnersObject.query.delete()
    sqldb.session.commit()
    for old_partner in accountant_partners.find():
        new_partner = AccountantPartnersObject(
            id=str(old_partner['_id']),
            type=old_partner['type'],
            created=old_partner.get('created', datetime.utcnow()),
            link=old_partner.get('region', ''),
            title=old_partner.get('title', ''),
            banner=old_partner.get('banner', ''),
            enabled=old_partner.get('enabled', False),
            sort_index=old_partner.get('sort_index', 1),
            region=old_partner.get('region'),
            city=old_partner.get('city')
        )
        sqldb.session.add(new_partner)
    sqldb.session.commit()

    BankPartnerRequestObject.query.delete()
    BankPartnersServiceObject.query.delete()
    BankPartnersObject.query.delete()
    sqldb.session.commit()

    bank_partners = db['bank_partners']
    for old_partner in bank_partners.find():
        new_partner = BankPartnersObject(
            id=str(old_partner['_id']),
            created=old_partner.get('created', datetime.utcnow()),
            link=old_partner.get('region', ''),
            title=old_partner.get('title', ''),
            banner=old_partner.get('banner', ''),
            enabled=old_partner.get('enabled', False),
            sort_index=old_partner.get('sort_index', 1),
            region=old_partner.get('region'),
            city=old_partner.get('city'),
            conditions=old_partner.get('conditions')
        )
        sqldb.session.add(new_partner)
    sqldb.session.commit()

    bank_partners_service = db['bank_partners_service']
    for old_svc in bank_partners_service.find():
        bank_partner_id = str(old_svc.get('bank_partner_id', '')) if old_svc.get('bank_partner_id') else ''
        if not bank_partner_id:
            continue
        bp = BankPartnersObject.query.filter_by(id=bank_partner_id).first()
        if not bp:
            continue
        new_svc = BankPartnersServiceObject(
            id=str(old_svc['_id']),
            type=old_svc['type'],
            fields=old_svc['fields'],
            email=old_svc.get('email'),
            template_name=old_svc.get('template_name'),
            config=old_svc.get('config'),
            bank_partner_id=bank_partner_id
        )
        sqldb.session.add(new_svc)
    sqldb.session.commit()

    bank_partners_request = db['bank_partners_request']
    for old_req in bank_partners_request.find():
        batch_id = str(old_req['batch_id'])
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
        if not batch:
            continue

        bank_partner_id=str(old_req.get('bank_partner_id', ''))
        if not bank_partner_id:
            continue
        bp = BankPartnersObject.query.filter_by(id=bank_partner_id).first()
        if not bp:
            continue

        new_req = BankPartnerRequestObject(
            bank_partner_id=bank_partner_id,
            batch_id=batch_id,
            bank_partner_caption=old_req.get('bank_partner_caption'),
            sent_date=old_req['sent_date'],
            status=old_req['status'],
            bank_contact_phone_general_manager=old_req.get('bank_contact_phone_general_manager'),
            bank_contact_phone=old_req.get('bank_contact_phone'),
            send_private_data=old_req.get('send_private_data')
        )
        sqldb.session.add(new_req)
    sqldb.session.commit()

def rollback(config, logger):
    pass
