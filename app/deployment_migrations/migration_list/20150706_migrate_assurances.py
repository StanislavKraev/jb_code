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
    logger.debug(u"Modify car assurances tables")

    sqldb.session.close()

    sqldb.engine.execute("ALTER TABLE car_assurance_branch DROP COLUMN full_name;")
    sqldb.engine.execute("ALTER TABLE car_assurance_branch DROP COLUMN short_name;")
    sqldb.engine.execute("ALTER TABLE car_assurance_branch ADD COLUMN title VARCHAR NOT NULL DEFAULT '';")
    sqldb.engine.execute("ALTER TABLE car_assurance_branch ADD COLUMN phone VARCHAR NOT NULL DEFAULT '';")
    sqldb.engine.execute("ALTER TABLE car_assurance_branch ADD COLUMN region VARCHAR NOT NULL DEFAULT '';")


def rollback(config, logger):
    pass
