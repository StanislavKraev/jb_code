# -*- coding: utf-8 -*-
from async.test_views import TestDbSyncView, TestNetSyncView, TestNetAsyncView, TestDbAsyncView

from async.views import IfnsGetScheduleView, IfnsMakeBookingView, IfnsBookingView, IfnsNameView, IfnsDiscardBookingView

url_patterns = (
    (r"/meeting/ifns/", IfnsBookingView),
    (r"/meeting/ifns/schedule/", IfnsGetScheduleView),
    (r"/meeting/ifns/create/", IfnsMakeBookingView),
    (r"/meeting/ifns/name/", IfnsNameView),
    (r"/meeting/ifns/discard/", IfnsDiscardBookingView),
    (r"/db-sync/", TestDbSyncView),
    (r"/db-async/", TestDbAsyncView),
    (r"/net-sync/", TestNetSyncView),
    (r"/net-async/", TestNetAsyncView)
)
