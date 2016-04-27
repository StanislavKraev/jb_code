# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
import jinja2
import os
import pyphen
import pytils
from pytz import timezone
from fw.documents.fields.simple_doc_fields import DocMultiDeclensionField, DocField
from fw.documents.morpher_tools import morph_with_morpher
from common_utils import num_word, word_from_num, int_to_ifns, LazyClassLoader
from jinja2.utils import Markup

msk_timezone = timezone('Europe/Moscow')


def static_url(domain):
    url = "http://" + domain + "/static%s"

    def get_static_url(value):
        return url % value

    return get_static_url


def dt_from_iso(value):
    # transform datetime value from iso format to human readable
    if not value:
        return ""
    dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    return dt.strftime("%Y-%m-%d %H:%M")


def msk_dt_from_iso(value):
    # transform datetime value from iso format to human readable
    if not value:
        return ""
    dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    return msk_timezone.fromutc(dt).strftime("%Y-%m-%d %H:%M")


def msk_dt_from_iso_p30(value):
    # transform datetime value from iso format to human readable
    if not value:
        return ""
    dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f") + datetime.timedelta(30)
    return msk_timezone.fromutc(dt).strftime("%Y-%m-%d")


def js_dt_from_iso(value):
    if not value:
        return ""
    dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    return dt.strftime("new Date(Date.UTC(%Y, %m, %d, %H, %M, %S, %f))")


def countdown_to_date(value):
    if not value:
        return ""
    dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    now = datetime.datetime.utcnow()
    td = dt - now
    return "+%d" % (td.total_seconds())


def num_to_text(value, gender='m', padezh='im'):
    return num_word(value, gender, padezh)


DECL_PYMORPHY = {
    DocMultiDeclensionField.DF_NOMINATIVE: 'nomn',
    DocMultiDeclensionField.DF_GENITIVE: 'gent',
    DocMultiDeclensionField.DF_DATIVUS: 'datv',
    DocMultiDeclensionField.DF_ACCUSATIVUS: 'accs',
    DocMultiDeclensionField.DF_INSTRUMENTALIS: 'ablt',
    DocMultiDeclensionField.DF_PRAEPOSITIONALIS: 'loct',
}


def padezh_and_number(word, padezh, number):
    return word_from_num(word, number, padezh)


def declension_fio(value, case='im'):
    return declension(value, case)


def declension(value, case=DocMultiDeclensionField.DF_NOMINATIVE):
    if isinstance(value, DocMultiDeclensionField):
        value = value.declension('nom')
    if not isinstance(value, basestring):
        if hasattr(value, 'initialized') and not getattr(value, 'initialized', False):
            return u""
        value = unicode(value)
    if case not in DECL_PYMORPHY:
        return value

    new_value = morph_with_morpher(value)
    if not new_value:
        return value

    result = new_value.get(case, value)
    if not result:
        return value
    return result if isinstance(result, unicode) else result.decode('utf-8')


def shorten_fio(full_name):
    parts = filter(lambda x: len(x) > 0, full_name.strip().split(u' '))
    if len(parts) < 2:
        return full_name
    if len(parts) == 2:
        return parts[0] + u' ' + parts[1][0] + u'.'
    if len(parts) == 3:
        return parts[0] + u' ' + parts[1][0] + u'. ' + parts[2][0] + u'.'
    return parts[0] + u' ' + parts[1][0] + u'. ' + u'. '.join(parts[2:]) + u'.'


TEX_SPEC_SYMBOL_MAP = (
    (u'\\', u'\\textbackslash '),
    (u'<', u'\\textless '),
    (u'>', u'\\textgreater '),
    (u'%', u'\\%'),
    (u'$', u'\\$'),
    (u'{', u'\\{'),
    (u'}', u'\\}'),
    (u'_', u'\\_'),
    (u'¶', u'\\P '),
    (u'‡', u'\\ddag '),
    (u'|', u'\\textbar '),
    (u'–', u'\\textendash '),
    (u'—', u'\\textemdash '),
    (u'™', u'\\texttrademark '),
    (u'£', u'\\pounds '),
    (u'#', u'\\#'),
    (u'&', u'\\&'),
    (u'§', u'\\S'),
    (u'®', u'\\textregistered '),
    (u'©', u'\\copyright '),
    (u'¿', u'\\textquestiondown '),
    (u'«', u'<<'),
    (u'»', u'>>'),
    (u'"', u"''"),
    (u'^', u"\^{}"),
)


def texify(val):
    if not val:
        return u""

    if isinstance(val, DocField):
        val = val.api_value() if val.initialized else u""
    if not isinstance(val, unicode) and isinstance(val, basestring):
        val = val.decode('utf-8')
    val = unicode(val)
    if val.count('"') == 2:
        val = val.replace('"', "``", 1).replace('"', "''")
    for from_symbol, to_symbol in TEX_SPEC_SYMBOL_MAP:
        val = val.replace(from_symbol, to_symbol)
    while u'<<<<' in val:
        val = val.replace(u'<<<<', u'<<\empt<<')
    while u'<<"' in val:
        val = val.replace(u'<<"', u'<<\empt"')
    while u'">>' in val:
        val = val.replace(u'">>', u'"\empt>>')
    return val


def skolki(val):
    if val == 1:
        return u"одно"
    if val == 2:
        return u"двух"
    if val == 3:
        return u"трёх"
    if val == 4:
        return u"четырёх"
    if val == 5:
        return u"пяти"
    if val == 6:
        return u"шести"
    if val == 7:
        return u"семи"
    if val == 8:
        return u"восьми"
    if val == 9:
        return u"девяти"
    if val == 10:
        return u"десяти"
    return u""


def strftime(val, format):
    return val.strftime(format)


def select_byattr(target_list, attr_name, attr_val):
    if not isinstance(attr_val, (tuple, list)):
        attr_val = [attr_val]
    return filter(lambda x: getattr(x, attr_name) in attr_val, target_list)


def utm_args(value, link_name, user_id=None):
    from flask import current_app
    # if current_app.config['DEBUG'] or current_app.config['STAGING']:
    #        return value
    if value is None:
        return value
    value = unicode(value)
    last_symbol = value[-1] if value else ''
    suffix = u""
    if '#' in value:
        try:
            value, suffix = value.split('#')
            suffix = "#" + suffix if suffix else ""
        except Exception:
            return value
    if user_id:
        return Markup("%s%s%s" % (
            value,
            '&' if last_symbol not in '&?' else '',
            "utm_source=%s&utm_medium=email&utm_term=%s%s" % (link_name, user_id, suffix)
        ))

    return Markup("%s%s%s" % (
        value, '&' if last_symbol not in '&?' else '', "utm_source=%s&utm_medium=email%s" % (link_name, suffix)))

def number_as_currency_text(value, case = "im"):
    from common_utils import word_from_num, num_word, chunks
    if isinstance(value, dict):
        decival = Decimal(value['value'])
    elif isinstance(value, DocField):
        decival = value.db_value()
    else:
        decival = Decimal(value)
    is_minus = decival < 0
    if is_minus:
        decival = -decival
    decival_str = str(decival)
    rubles = int(decival_str.split('.')[0] if '.' in decival_str else decival_str)
    rubles_splited = u' '.join([_ for _ in chunks(unicode(rubles)[::-1], 3)])[::-1]
    rubles_text = num_word(rubles, padezh=case)
    cur_word_maj = u"рубль"
    cur_word_min = u"копейка"

    min_str = decival_str.split('.')[1] if '.' in decival_str else '0'
    if len(min_str) < 2:
        min_str += u"0"
    currency_minor = int(min_str)

    rubles_word = word_from_num(cur_word_maj, rubles, padezh=case)
    copeek_word = word_from_num(cur_word_min, currency_minor, padezh=case)
    copeek_num = unicode(currency_minor)
    if len(copeek_num) < 2:
        copeek_num = u"0" + copeek_num
    if is_minus:
        return u"минус %s (%s) %s %s %s" % (rubles_splited, rubles_text, rubles_word, copeek_num, copeek_word)
    return u"%s (%s) %s %s %s" % (rubles_splited, rubles_text, rubles_word, copeek_num, copeek_word)

def tex_hyphenize(val):
    if not val:
        return u""
    if isinstance(val, DocField):
        val = val.db_value()

    dic = pyphen.Pyphen(lang='ru_RU')

    return u" ".join([dic.inserted(word, hyphen=u'\\-') for word in val.split(u" ")])

def rus_full_date(val):
    return pytils.dt.ru_strftime(u"%d" + u" %B %Y", inflected=True, date=val) if val else u""

def make_auth_url(val, user_uuid):
    from fw.auth.user_manager import UserManager, AuthUser
    user = AuthUser.query.filter_by(uuid=user_uuid).scalar()
    if not user:
        return val   # fallback
    return UserManager.make_auth_url(val, user)

def md5_filter(val):
    import hashlib
    m = hashlib.md5()
    m.update(unicode(val))
    return m.hexdigest()

def enum_to_name(value, cls_name):
    try:
        if isinstance(value, DocField):
            return unicode(value)
        cls_loader = LazyClassLoader(cls_name)
        cls = cls_loader.load()
        val = cls.get_name(value)
        return val
    except:
        return u""

def timeshift(value, days, seconds=0):
    return value + datetime.timedelta(days=days, seconds=seconds)

def load_filters(env, config):
    env.filters['declension_fio'] = declension_fio
    env.filters['declension'] = declension
    env.filters['utc_datetime'] = dt_from_iso
    env.filters['answer_due_date'] = msk_dt_from_iso_p30
    env.filters['js_datetime'] = js_dt_from_iso
    env.filters['countdown_to'] = countdown_to_date
    env.filters['num_to_text'] = num_to_text
    env.filters['padezh_and_number'] = padezh_and_number
    env.filters['shorten_fio'] = shorten_fio
    env.filters['texify'] = texify
    env.filters['int_to_ifns'] = int_to_ifns
    env.filters['skolki'] = skolki
    env.filters['strftime'] = strftime
    env.filters['byattr'] = select_byattr
    env.filters['utm_args'] = utm_args
    env.filters['capitalize_true'] = lambda x: "" if not unicode(x) else (unicode(x)[0].upper() + unicode(x)[1:])
    env.filters['number_as_currency_text'] = number_as_currency_text
    env.filters['float'] = float
    env.filters['Decimal'] = Decimal
    env.filters['tex_hyphenize'] = tex_hyphenize
    env.filters['rus_full_date'] = rus_full_date
    env.filters['make_auth_url'] = make_auth_url
    env.filters['md5'] = md5_filter
    env.filters['T'] = lambda val, t, f: t if val else f
    env.filters['enum_to_name'] = enum_to_name
    env.filters['timeshift'] = timeshift

def set_template_loader(jinja):
    _search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"fw/templates"))
    jinja.loader = jinja2.ChoiceLoader([jinja2.FileSystemLoader(_search_path)])

