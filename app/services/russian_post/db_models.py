# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, ForeignKey, Unicode, Integer, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func

from fw.db.sql_base import db as sqldb


class PostTrackingStatus(object):

    PTS_UNKNOWN = 'unknown'
    PTS_NOT_FOUND = 'not_found'
    PTS_PROGRESS = 'progress'
    PTS_DELIVERED = 'delivered'
    PTS_FAILED = 'failed'


class RussianPostTrackingItem(sqldb.Model):
    __tablename__ = 'rus_post_tracking'

    id = Column(Integer, primary_key=True)

    tracking = Column(Unicode, nullable=False)

    creation_date = Column(DateTime, default=func.now(), nullable=False)

    batch_id = Column(String, ForeignKey('doc_batch.id'), nullable=True)
    batch = relationship("DocumentBatchDbObject")

    owner_id = Column(Integer, ForeignKey('authuser.id'), nullable=False)
    owner = relationship("AuthUser")

    status = Column(String, default=PostTrackingStatus.PTS_UNKNOWN, nullable=False)
    status_caption = Column(Unicode, nullable=False, default=u"")

    status_change_dt = Column(DateTime, nullable=True)
    last_check_dt = Column(DateTime, nullable=True)

    last_location = Column(Unicode, nullable=True)

    tracking_type = Column(String, nullable=True)                                  # reserved (for batches with multiple tracks)

    __table_args__ = (Index('batch_tracking_index', "tracking", "batch_id"), )
