# -*- coding: utf-8 -*-

from sqlalchemy import Column, Unicode, Integer
from fw.db.sql_base import db as sqldb


class MigrationState(sqldb.Model):
    __tablename__ = 'migration_state'

    id = Column(Integer, primary_key=True)
    value = Column(Unicode, nullable=True)
