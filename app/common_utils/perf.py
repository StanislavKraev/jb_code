# -*- coding: utf-8 -*-
import StringIO
import cProfile
import pstats
from time import time

class TimeCalculator(object):

    def __init__(self, name, logger = None, use_profile = False, min_time = None):
        self.logger = logger
        self.t1 = None
        self.t2 = None
        self.name = name
        self.use_profile = use_profile
        self.min_time = min_time
        if self.use_profile:
            self.pr = cProfile.Profile()

    def __enter__(self):
        self.t1 = time()
        if self.use_profile:
            self.pr.enable(builtins=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.t2 = time()
        if self.use_profile:
            self.pr.disable()
        if self.min_time is not None and (self.t2 - self.t1) < self.min_time:
            return
        if self.use_profile:
            if self.logger:
                s = StringIO.StringIO()
                sortby = 'cumulative'
                ps = pstats.Stats(self.pr, stream=s).sort_stats(sortby)
                ps.print_stats()
                self.logger.debug(s.getvalue())
        else:
            if self.logger:
                self.logger.debug("%s: %s" % (self.name, unicode(self.t2 - self.t1)))
