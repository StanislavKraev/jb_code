# -*- coding: utf-8 -*-
import codecs
import os

from flask import Blueprint, current_app, Response, abort
from guppy import hpy
from fw.api import errors
from fw.api.args_validators import validate_arguments, ArgumentValidator
from fw.api.base_handlers import api_view

from fw.async_tasks import test_task
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject
from fw.storage.file_storage import FileStorage

system_bp = Blueprint('system', __name__)


@system_bp.route('/test/task/', methods=['POST'])
def run_test_task():
    test_task.test_task.apply_async(task_id="test_task_id", countdown=10)
    result = Response(u"Ok", status=200)
    return result


hp = hpy()
hp.setref()


@system_bp.route('/sys/get_mem_stat/', methods=['GET'])
def get_mem_stat():
    pid = os.getpid()
    result = u"Process: %s\n" % unicode(pid)
    res = hp.heap()
    result += unicode(res)

    result += u"\n\n"

    for i in xrange(min(len(res), 10)):
        result += "\n%s" % unicode(res[i].byvia)
    result += u"\n\n"
    for i in xrange(min(len(res), 10)):
        result += "\n%s" % unicode(res[i].bysize)
    result += u"\n\n"
    for i in xrange(min(len(res), 10)):
        result += "\n%s" % unicode(res[i].byclodo)
    result += u"\n\n"
    for i in xrange(min(len(res), 10)):
        result += "\n%s" % unicode(res[i].byid)

    return u"<html><body><pre>%s</pre></body></html>" % result


@system_bp.route('/sys/get_batch_doc/', methods=['GET'])
@api_view
@validate_arguments(batch_id=ArgumentValidator(required=True), document_id=ArgumentValidator(required=True))
def get_batch_doc(batch_id=None, document_id=None):
    config = current_app.config
    if not config['STAGING'] and not config['DEBUG']:
        abort(404)
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
    if not batch:
        raise errors.BatchNotFound()

    doc = BatchDocumentDbObject.query.filter_by(id=document_id).first()

    file_obj = doc.file
    if file_obj:
        file_path = FileStorage.get_path(file_obj, current_app.config)
        if os.path.exists(file_path) and file_path.endswith('.pdf'):
            file_path = file_path[:-4] + '.text-src'
            if os.path.exists(file_path):
                with codecs.open(file_path, 'r', 'utf-8') as ff:
                    content = ff.read()
                    return {'result': content}
    raise errors.BatchNotFound()
