# -*- coding: utf-8 -*-
from sqlalchemy.orm import relationship

from sqlalchemy.sql.functions import func
from sqlalchemy import Column, Unicode, String, DateTime, Boolean, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from fw.db.sql_base import db as sqldb


class AccountantPartnersObject(sqldb.Model):
    __tablename__ = "accountant_partners"

    id = Column(String, primary_key=True)
    type = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=func.now())
    link = Column(Unicode, nullable=True)
    title = Column(Unicode, nullable=False)
    banner = Column(Unicode, nullable=False)
    enabled = Column(Boolean, default=True)
    sort_index = Column(Integer, nullable=False, default=1)
    region = Column(ARRAY(Text), nullable=True)
    city = Column(ARRAY(Text), nullable=True)


class BankPartnersObject(sqldb.Model):
    __tablename__ = "bank_partners"

    id = Column(String, primary_key=True)
    created = Column(DateTime, nullable=False, default=func.now())
    link = Column(Unicode, nullable=True)
    title = Column(Unicode, nullable=False)
    banner = Column(Unicode, nullable=False)
    enabled = Column(Boolean, default=True)
    sort_index = Column(Integer, nullable=False, default=1)
    region = Column(ARRAY(Text), nullable=True)
    city = Column(ARRAY(Text), nullable=True)
    conditions = Column(ARRAY(Text), nullable=True)


class BankPartnerRequestObject(sqldb.Model):
    __tablename__ = "bank_partners_request"

    id = Column(Integer, primary_key=True)

    bank_partner_id = Column(String, ForeignKey('bank_partners.id'), nullable=False)
    bank_partner = relationship("BankPartnersObject")

    batch_id = Column(String, ForeignKey('doc_batch.id'), nullable=False)
    batch = relationship("DocumentBatchDbObject", uselist=False)

    bank_partner_caption = Column(Unicode, nullable=True)
    sent_date = Column(DateTime, nullable=False, default=func.now())
    status = Column(Unicode, nullable=False)
    bank_contact_phone_general_manager = Column(Unicode, nullable=True)
    bank_contact_phone = Column(Unicode, nullable=True)
    send_private_data = Column(Boolean, default=True)


class BankPartnersServiceObject(sqldb.Model):
    __tablename__ = "bank_partners_service"

    id = Column(String, primary_key=True)
    type = Column(Unicode, nullable=False)
    fields = Column(JSONB, nullable=True)

    email = Column(Unicode, nullable=True)
    template_name = Column(Unicode, nullable=True)
    config = Column(JSONB, nullable=True)

    bank_partner_id = Column(String, ForeignKey('bank_partners.id'), nullable=False)
    bank_partner = relationship("BankPartnersObject")


class StampPartnersObject(sqldb.Model):
    __tablename__ = "stamp_partners"

    id = Column(String, primary_key=True)
    region = Column(ARRAY(Text), nullable=True)
    enabled = Column(Boolean, default=True)
    sort_index = Column(Integer, nullable=False, default=1)
    link = Column(Unicode, nullable=True)
    banner = Column(Unicode, nullable=False)
    title = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=func.now())
