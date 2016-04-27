# -*- coding: utf-8 -*-
from bson.objectid import ObjectId

from sqlalchemy import Column, String, ForeignKey, Unicode, Integer
from sqlalchemy.orm import relationship

from fw.db.sql_base import db as sqldb


class FileObject(sqldb.Model):
    __tablename__ = 'files'

    id = Column(String, primary_key=True, default=lambda: str(ObjectId()))
    file_name = Column(Unicode)
    file_path = Column(String)

    _owner_id = Column(Integer, ForeignKey('authuser.id'), nullable=True)
    _owner = relationship("AuthUser")

    _original_file = Column(String, nullable=True)
