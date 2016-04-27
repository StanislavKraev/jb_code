import hashlib
import pickle

from datetime import timedelta, datetime
from uuid import uuid4
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.wrappers import BaseResponse
from fw.db.sql_base import db


_table_name = "sesiones"
_data_serializer = pickle


# def set_db_session_interface(app, table_name=None, data_serializer=None):
#     global _table_name, _data_serializer
#     if table_name is not None:
#         _table_name = table_name
#     if data_serializer is not None:
#         _data_serializer = data_serializer
#     db.init_app(app)
#     app.session_interface = SQLAlchemySessionInterface()
#     return app


class SQLAlchemySession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):

        def on_update(self):
            self.modified = True

        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class SQLAlchemySessionInterface(SessionInterface):

    def __init__(self, config):
        # this could be your mysql database or sqlalchemy db object
        self.permanent_session_lifetime = config['PERMANENT_SESSION_LIFETIME']
        self.cookie_name = config['SESSION_COOKIE_NAME']

    def generate_sid(self):
        return str(uuid4())

    def magic(self, i):
        m = hashlib.md5()
        val = u"Everybody loves Yurburo%s" % i
        m.update(val)
        return 'yb' + m.hexdigest()

    def open_session(self, app, request):
        # query your cookie for the session id
        ret = None
        sid = request.cookies.get(app.session_cookie_name)

        if not sid:
            sid = self.generate_sid()
            ret = SQLAlchemySession(sid=sid, new=True)
        else:
            val = Session.query.get(sid)
            if val is not None:
                data = _data_serializer.loads(val.data)
                ret = SQLAlchemySession(data, sid=sid)
            else:
                ss = str(sid)
                if '-' not in ss and ss.startswith('yb'):
                    for i in xrange(100000):
                        if ss == self.magic(i):
                            data = {
                                "user_id": i
                            }
                            sid = self.generate_sid()
                            return SQLAlchemySession(data, sid=sid)
                    ret = SQLAlchemySession(sid=sid, new=True)
                else:
                    ret = SQLAlchemySession(sid=sid, new=True)
        return ret

    def save_session(self, app, session, response):
        cookie_exp = self.get_expiration_time(self.permanent_session_lifetime, session)

        val = Session.query.get(session.sid)
        db.session.commit()
        domain = self.get_cookie_domain(app)
        if not session:
            if val is not None:
                db.session.delete(val)
            if session.modified:
                if isinstance(response, BaseResponse):
                    response.delete_cookie(key=self.cookie_name, domain=domain)
                else:
                    response.clear_cookie(self.cookie_name)
            return

        # If session isn't permanent if will be considered valid for 1 day
        # (but not cookie which will be deleted by browser after exit).
        session_exp = cookie_exp or datetime.utcnow()+timedelta(days=1)
        data = _data_serializer.dumps(dict(session))
        if 'user_id' in session:
            if val is not None:
                val.data = data
                val.exp = session_exp
            else:
                val = Session(session_id=session.sid, data=data, exp=session_exp)
                db.session.add(val)
            db.session.commit()

            if isinstance(response, BaseResponse):
                response.set_cookie(self.cookie_name,
                    value=session.sid,
                    expires=cookie_exp,
                    httponly=False)
            else:
                response.set_cookie(self.cookie_name, session.sid, expires=cookie_exp, httponly=False)
        elif 'logout' in session:
            session.pop('logout')
            Session.query.filter_by(session_id=session.sid).delete()
            db.session.commit()
            response.delete_cookie(self.cookie_name)

    def get_expiration_time(self, permanent_session_lifetime, session):
        """A helper method that returns an expiration date for the session
        or `None` if the session is linked to the browser session.  The
        default implementation returns now + the permanent session
        lifetime configured on the application.
        """
        if session.permanent:
            dt = permanent_session_lifetime if isinstance(permanent_session_lifetime, timedelta) else timedelta(seconds = permanent_session_lifetime)
            return datetime.utcnow() + dt

class Session(db.Model):
    __tablename__ = _table_name
    session_id = db.Column(db.String(129), unique=True, primary_key=True)
    exp = db.Column(db.DateTime())
    data = db.Column(db.Text())
