# -*- coding: utf-8 -*-
from datetime import datetime
import logging
from tempfile import TemporaryFile, NamedTemporaryFile
from bson import ObjectId
import requests
from fw.auth.models import AuthUser
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject, CompanyDbObject, PrivatePersonDbObject
from fw.documents.enums import PersonTypeEnum, IncorporationFormEnum, CompanyTypeEnum
from fw.storage.models import FileObject


def forward(config, logger):
    logger.debug(u"Add car assurances tables")

    sqldb.session.close()

    sqldb.engine.execute("""
    CREATE TABLE car_assurance (
        id VARCHAR NOT NULL,
        full_name VARCHAR,
        short_name VARCHAR,
        PRIMARY KEY (id)
    );
    """)

    sqldb.engine.execute("""
    CREATE TABLE car_assurance_branch (
        id VARCHAR NOT NULL,
        full_name VARCHAR,
        short_name VARCHAR,
        address VARCHAR,
        car_assurance_id VARCHAR NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY(car_assurance_id) REFERENCES car_assurance (id)
    );
    """)


def rollback(config, logger):
    pass
