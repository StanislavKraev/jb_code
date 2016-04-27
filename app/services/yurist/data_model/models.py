# -*- coding: utf-8 -*-

from bson import ObjectId
from sqlalchemy import Column, Unicode, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func

from fw.db.sql_base import db as sqldb


class YuristBatchCheckObject(sqldb.Model):
    __tablename__ = "yurist_batch_check"

    id = Column(String, primary_key=True, default=lambda: str(ObjectId()))
    batch_id = Column(String, ForeignKey('doc_batch.id'), nullable=True)
    batch = relationship("DocumentBatchDbObject", uselist=False)

    status = Column(Unicode, nullable=False, default="new")

    create_date=Column(DateTime, nullable=False, default=func.now())
    typos_correction=Column(Boolean, nullable=False)

    attached_files = relationship("YuristCheckFilesObject")


class YuristCheckFilesObject(sqldb.Model):
    __tablename__ = 'yurist_check_files'

    check_id = Column(String, ForeignKey('yurist_batch_check.id'), primary_key=True)
    files_id = Column(String, ForeignKey('files.id'), primary_key=True)

    child = relationship("FileObject")




