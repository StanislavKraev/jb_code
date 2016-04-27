# -*- coding: utf-8 -*-

class Migration(object):
    def __init__(self, name, forward, rollback):
        self.name = name
        self._forward = forward
        self._rollback = rollback

    def run(self, config, logger):
        self._forward(config, logger)

    def rollback(self, config, logger):
        self._rollback(config, logger)

    @property
    def version(self):
        return self.name.split('_')[0]

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name