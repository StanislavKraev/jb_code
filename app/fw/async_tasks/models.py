# -*- coding: utf-8 -*-
from bson.objectid import ObjectId
from sqlalchemy.sql.functions import func
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from fw.db.sql_base import db


class CeleryScheduledTask(db.Model):

    __tablename__ = 'celery_scheduled_task'

    id = Column(String, primary_key=True, default=lambda: unicode(ObjectId()))
    task_name = Column(String)
    created = Column(DateTime, default=func.now(), nullable=False)
    eta = Column(DateTime, nullable=False)
    sent = Column(Boolean, default=False)
    args = Column(JSONB, nullable=True)
    kwargs = Column(JSONB, nullable=True)
