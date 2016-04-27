# -*- coding: utf-8 -*-

_plugins_library = dict()

def get_plugin(plugin_id):
    return _plugins_library[plugin_id]

def register(plugin_id, plugin_module, class_loader=None):
    assert class_loader
    plugin_module.register(class_loader)
    _plugins_library[plugin_id] = plugin_module
