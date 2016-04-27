# -*- coding: utf-8 -*-
from bson.objectid import ObjectId

from sqlalchemy import Column, String, ForeignKey, Unicode
from sqlalchemy.orm import relationship

from fw.db.sql_base import db as sqldb


class CarAssurance(sqldb.Model):
    __tablename__ = 'car_assurance'

    id = Column(String, primary_key=True, default=lambda: str(ObjectId()))

    full_name = Column(Unicode)
    short_name = Column(Unicode)

    address = Column(Unicode, nullable=False)

    connection_name = Column(Unicode, nullable=False, default=u'')


class CarAssuranceBranch(sqldb.Model):
    __tablename__ = 'car_assurance_branch'

    id = Column(String, primary_key=True, default=lambda: str(ObjectId()))

    title = Column(Unicode, nullable=True, default=u'')
    address = Column(Unicode, nullable=True, default=u'')
    phone = Column(Unicode, nullable=True, default=u'')
    region = Column(Unicode, nullable=False)

    car_assurance_id = Column(String, ForeignKey('car_assurance.id'), nullable=False)
    car_assurance = relationship("CarAssurance")

