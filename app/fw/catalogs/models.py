# -*- coding: utf-8 -*-

from sqlalchemy import Column, Unicode, Integer, String, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from fw.db.sql_base import db as sqldb


class BikCatalog(sqldb.Model):
    __tablename__ = 'bik_catalog'

    id = Column(String, primary_key=True)
    name = Column(Unicode, nullable=False)
    okpo = Column(Unicode, nullable=False)
    bik = Column(Unicode, nullable=False, index=True)
    phone = Column(Unicode, nullable=False)
    address = Column(Unicode, nullable=False)
    kor_account = Column(Unicode, nullable=False)


class OkvadObject(sqldb.Model):
    __tablename__ = "okvad"

    id = Column(String, primary_key=True)
    caption = Column(Unicode, nullable=False)
    okved = Column(Unicode, nullable=False, index=True, unique=True)
    nalog = Column(Unicode, nullable=False)
    parent = Column(Unicode, nullable=True)


class OkvedCatalogObject(sqldb.Model):
    __tablename__ = "okved_catalog"

    id = Column(String, primary_key=True)
    name = Column(Unicode, nullable=False)
    departments = Column(JSONB)


class GeoCities(sqldb.Model):
    __tablename__ = "geo_cities"

    name = Column(Unicode, nullable=False)
    cid = Column(Integer, nullable=False, unique=True, primary_key=True)
    region = Column(Unicode, nullable=False)
    lat = Column(Unicode, nullable=False)
    lng = Column(Unicode, nullable=False)


class GeoRanges(sqldb.Model):
    __tablename__ = "geo_ranges"

    cid = Column(Integer, nullable=False, primary_key=True)
    start = Column(BigInteger, nullable=False)
    end = Column(BigInteger, nullable=False)
