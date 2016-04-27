# -*- coding: utf-8 -*-

from bson import ObjectId
from sqlalchemy import Column, Unicode, String, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from fw.db.sql_base import db as sqldb


class IfnsBookingTaskStatus(object):
    BTS_NEW = "new"
    BTS_PROGRESS = "progress"
    BTS_FAIL = "fail"
    BTS_SUCCESS = "success"

    BTS_ALL = (BTS_NEW, BTS_PROGRESS, BTS_FAIL, BTS_SUCCESS)


class IfnsBookingObject(sqldb.Model):
    __tablename__ = "ifns_booking"

    id = Column(String, primary_key=True, default=lambda: str(ObjectId()))
    batch_id = Column(String, ForeignKey('doc_batch.id'), nullable=True)
    batch = relationship("DocumentBatchDbObject", uselist=False)
    code = Column(Unicode, nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    service = Column(Unicode, nullable=False)
    _discarded = Column(Boolean, default=False)
    phone = Column(Unicode, nullable=True)
    window = Column(Unicode, nullable=True)
    address = Column(Unicode, nullable=True)
    service_id = Column(Integer, nullable=False)
    ifns = Column(Unicode, nullable=True)
    how_to_get = Column(Unicode, nullable=True)
    reg_info = Column(JSONB, nullable=True)


class IfnsCatalogObject(sqldb.Model):
    __tablename__ = "ifns_catalog"

    id = Column(String, primary_key=True)

    updated = Column(DateTime, nullable=True)
    code = Column(Integer, nullable=False, index=True)
    comment = Column(Unicode, nullable=True)
    tel = Column(ARRAY(String), nullable=True)
    name = Column(Unicode, nullable=True)
    rof = Column(JSONB, nullable=True)
    rou = Column(JSONB, nullable=True)
    plat = Column(JSONB, nullable=True)
    address = Column(JSONB, nullable=True)
    region = Column(Unicode, nullable=True, index=True)