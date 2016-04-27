# -*- coding: utf-8 -*-

import os
import tempfile
from bson import ObjectId
from bson.errors import InvalidId

from flask import json, request, current_app, Response, abort, Blueprint
from flask_login import login_required, current_user

from fw.api.views import not_authorized
from fw.storage.file_storage import FileStorage
from fw.storage.models import FileObject

files_bp = Blueprint('files', __name__)


@files_bp.route('/storage/put/', methods=['POST'])
@login_required
def upload_file():
    file_obj = request.files['file']
    if file_obj and file_obj.filename and len(os.path.splitext(file_obj.filename)) > 1:
        t_file_out = tempfile.NamedTemporaryFile(mode="w+", delete=True, suffix=os.path.splitext(file_obj.filename)[-1])
        full_name = t_file_out.name
        t_file_out.close()
        file_obj.save(full_name)
        file_obj = FileStorage.add_file_from_disk(full_name, current_app.config, current_user.id, file_name=file_obj.filename)

        result = {
            "id": unicode(file_obj.id),
            "size": os.path.getsize(full_name),
            "file_name": file_obj.file_name,
            "url": FileStorage.get_url(file_obj, current_app.config)
        }
        os.unlink(full_name)
        resp = Response(json.dumps({"result": result}), content_type="application/json")
        resp.headers.add('Access-Control-Allow-Credentials', "true")
        resp.headers.add('Access-Control-Allow-Origin', "http://%s" % current_app.config['site_domain'])
        return resp

    abort(400)


@files_bp.route('/storage/<path:file_path>/', methods=['GET'], strict_slashes=False)
def get_private_file(file_path):
    if not current_user.is_authenticated:
        return not_authorized(current_app.config['site_domain'])

    current_app.logger.info(u'file: %s' % file_path)
    content_type = 'application/octet-stream' if ('download/' in file_path) else ''
    file_id = None
    try:
        for part in file_path.split('/'):
            try:
                ObjectId(part)
                file_id = part
                break
            except InvalidId:
                pass
        if not file_id:
            raise ValueError()
    except ValueError:
        current_app.logger.exception(u"Invalid file id")
        abort(400)
        return

    file_obj = FileObject.query.filter_by(id=file_id).first()
    if not file_obj:
        current_app.logger.exception(u"No such file in db with id %s" % unicode(file_id))
        abort(404)
        return

    if file_obj._owner and current_user != file_obj._owner:
        current_app.logger.exception(u"File is not yours with id %s" % unicode(file_id))
        abort(403)
        return

    if file_obj._original_file:
        file_id = file_obj._original_file
        file_obj = FileObject.query.filter_by(id=file_obj._original_file).first()
        if not file_obj:
            current_app.logger.exception(u"No such file in db with id %s" % file_id)
            abort(404)
            return

#    current_app.logger.info(u" file 4")
    file_full_path = FileStorage.get_path(file_obj, current_app.config)
    if not os.path.exists(file_full_path):
        current_app.logger.exception(u"File with id %s not found at %s" % (unicode(file_id), file_full_path))
        abort(404)
        return
#    current_app.logger.info(u" file 5")
    resp = Response(u"", headers={'X-Accel-Redirect': file_full_path}, content_type=content_type)
    if 'download/' in file_path:
        try:
            from email.header import decode_header, Header
            parts = file_path.split('/')
            fname = u""
            if len(parts) > 1:
                fname = parts[-1]
            if not fname and len(parts) > 2:
                fname = parts[-2]
            fname = filter(lambda x: x in u"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVQXYZ0123456789-=`!@#$%^&*()_+\\|[]{}абвгдеёжзийклмнопрстуфхцчшщьыъэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ.,;':\"/? ", fname)
            current_app.logger.info(u"  fname:%s" % fname)
            if fname:
                header_val = str(Header(fname, 'utf-8', maxlinelen=10000)).replace('?=\n =?utf-8?b?', '')
                current_app.logger.info(u"  header_val:%s" % header_val)
                resp.headers.add("Content-Disposition", u"attachment; filename=%s" % header_val)
        except Exception, ex:
            current_app.logger.exception(u"Failed to add header")
    resp.headers.add('Access-Control-Allow-Credentials', "true")
    resp.headers.add('Access-Control-Allow-Origin', "http://%s" % current_app.config['site_domain'])
    return resp
