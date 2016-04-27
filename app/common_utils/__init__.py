# -*- coding: utf-8 -*-
import hashlib
from bson.objectid import ObjectId
import os
import sys
import requests
from requests.exceptions import Timeout, ConnectionError

MAX_ITEMS_ON_PAGE = 20

def make_paginator_data(page, total):
    max_possible_page = (total - 1) / MAX_ITEMS_ON_PAGE + 1
    if page > max(max_possible_page, 1):
        page = max_possible_page
        max_possible_page = (total - 1) / MAX_ITEMS_ON_PAGE + 1

    max_page = min(max_possible_page, page + 2)
    min_page = max(1, max_page - 4)
    max_page = min(max_possible_page, min_page + 4)

    pages = range(min_page, max_page + 1)
    paginator = {
        'page' : page,
        'pages' : pages,
        'max_page' : max_page,
        'max_possible_page' : max_possible_page
    }
    return paginator

def get_russian_month_skl(month):
    if month == 1:
        return u"января"
    if month == 2:
        return u"февраля"
    if month == 3:
        return u"марта"
    if month == 4:
        return u"апреля"
    if month == 5:
        return u"мая"
    if month == 6:
        return u"июня"
    if month == 7:
        return u"июля"
    if month == 8:
        return u"августа"
    if month == 9:
        return u"сентября"
    if month == 10:
        return u"октября"
    if month == 11:
        return u"ноября"
    if month == 12:
        return u"декабря"

MONTHS = {
    u'Январь' : 1,
    u'Февраль' : 2,
    u'Март' : 3,
    u'Апрель' : 4,
    u'Май' : 5,
    u'Июнь' : 6,
    u'Июль' : 7,
    u'Август' : 8,
    u'Сентябрь' : 9,
    u'Октябрь' : 10,
    u'Ноябрь' : 11,
    u'Декабрь' : 12,
    }

def get_russian_date(date_val):
    return u"%d %s %s г." % (date_val.day, get_russian_month_skl(date_val.month), date_val.year)

def get_russian_date_time(date_val):
    return u"%s %s" % (get_russian_date(date_val), date_val.strftime(u'%H:%M').decode('utf-8'))

#def get_system_settings(store):
#    cls_info = get_cls_info(SettingsObject)
#    columns = cls_info.columns
#    columns_str = u",".join([column.name for column in columns])
#    settings_list = store.execute(u"SELECT %s from settings ORDER BY id DESC LIMIT 1" % columns_str)
#
#    for settings in settings_list:
#        settings_item = store._load_object(cls_info, settings_list, settings)
#        return settings_item
#

def is32bit():
    return sys.maxsize < 2**32

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


#   padezh / gender        m                     f                    n
#   im                   стол                 табуретка             окно
#   rod                  стола                табуретки             окна
#   dat                  столу                табуретке             окну
#   vin                  стол                 табуретку             окно
#   tvor                 столом               табуреткой            окном
#   predl                о столе              о табуретке           об окне

tens = (
        {'im' : u'',            'rod' : u'',             'dat' : u'',             'vin' : u'',            'tvor' : u'',               'predl' : u''},
        {'im' : u'',            'rod' : u'',             'dat' : u'',             'vin' : u'',            'tvor' : u'',               'predl' : u''},
        {'im' : u'двадцать',    'rod' : u'двадцати',     'dat' : u'двадцати',     'vin' : u'двадцать',    'tvor' : u'двадцатью',      'predl' : u'двадцати'},
        {'im' : u'тридцать',    'rod' : u'тридцати',     'dat' : u'тридцати',     'vin' : u'тридцать',    'tvor' : u'тридцатью',      'predl' : u'тридцати'},
        {'im' : u'сорок',       'rod' : u'сорока',       'dat' : u'сорока',       'vin' : u'сорок',       'tvor' : u'сорока',         'predl' : u'сорока'},
        {'im' : u'пятьдесят',   'rod' : u'пятидесяти',   'dat' : u'пятидесяти',   'vin' : u'пятьдесят',   'tvor' : u'пятьюдесятью',   'predl' : u'пятидесяти'},
        {'im' : u'шестьдесят',  'rod' : u'шестидесяти',  'dat' : u'шестидесяти',  'vin' : u'шестьдесят',  'tvor' : u'шестьюдесятью',  'predl' : u'шестидесяти'},
        {'im' : u'семьдесят',   'rod' : u'семидесяти',   'dat' : u'семидесяти',   'vin' : u'семьдесят',   'tvor' : u'семьюдесятью',   'predl' : u'семидесяти'},
        {'im' : u'восемьдесят', 'rod' : u'восьмидесяти', 'dat' : u'восьмидесяти', 'vin' : u'восемьдесят', 'tvor' : u'восемьюдесятью', 'predl' : u'восьмидесяти'},
        {'im' : u'девяносто',   'rod' : u'девяноста',    'dat' : u'девяноста',    'vin' : u'девяносто',   'tvor' : u'девяноста',      'predl' : u'девяноста'},
    )

ones = (
        {'im' : u'три',             'rod' : u'трёх',            'dat' : u'трём',        'vin' : u'три',             'tvor' : u'тремя',          'predl' : u'трёх'},
        {'im' : u'четыре',          'rod' : u'четырёх',         'dat' : u'четырём',     'vin' : u'четыре',          'tvor' : u'четырьмя',       'predl' : u'четырёх'},
        {'im' : u'пять',            'rod' : u'пяти',            'dat' : u'пяти',        'vin' : u'пять',            'tvor' : u'пятью',          'predl' : u'пяти'},
        {'im' : u'шесть',           'rod' : u'шести',           'dat' : u'шести',       'vin' : u'шесть',           'tvor' : u'шестью',         'predl' : u'шести'},
        {'im' : u'семь',            'rod' : u'семи',            'dat' : u'семи',        'vin' : u'семь',            'tvor' : u'семью',          'predl' : u'семи'},
        {'im' : u'восемь',          'rod' : u'восьми',          'dat' : u'восьми',      'vin' : u'восемь',          'tvor' : u'восемью',        'predl' : u'восьми'},
        {'im' : u'девять',          'rod' : u'девяти',          'dat' : u'девяти',      'vin' : u'девять',          'tvor' : u'девятью',        'predl' : u'девяти'},
        {'im' : u'десять',          'rod' : u'десяти',          'dat' : u'десяти',      'vin' : u'десять',          'tvor' : u'десятью',        'predl' : u'десяти'},
        {'im' : u'одиннадцать',     'rod' : u'одиннадцати',     'dat' : u'одиннадцати', 'vin' : u'одиннадцать',     'tvor' : u'одиннадцатью',   'predl' : u'одиннадцати'},
        {'im' : u'двенадцать',      'rod' : u'двенадцати',      'dat' : u'двенадцати',  'vin' : u'двенадцать',      'tvor' : u'двенадцатью',    'predl' : u'двенадцати'},
        {'im' : u'тринадцать',      'rod' : u'тринадцати',      'dat' : u'тринадцати',  'vin' : u'тринадцать',      'tvor' : u'тринадцатью',    'predl' : u'тринадцати'},
        {'im' : u'четырнадцать',    'rod' : u'четырнадцати',    'dat' : u'четырнадцати','vin' : u'четырнадцать',    'tvor' : u'четырнадцатью',  'predl' : u'четырнадцати'},
        {'im' : u'пятнадцать',      'rod' : u'пятнадцати',      'dat' : u'пятнадцати',  'vin' : u'пятнадцать',      'tvor' : u'пятнадцатью',    'predl' : u'пятнадцати'},
        {'im' : u'шестнадцать',     'rod' : u'шестнадцати',     'dat' : u'шестнадцати', 'vin' : u'шестнадцать',     'tvor' : u'шестнадцатью',   'predl' : u'шестнадцати'},
        {'im' : u'семнадцать',      'rod' : u'семнадцати',      'dat' : u'семнадцати',  'vin' : u'семнадцать',      'tvor' : u'семнадцатью',    'predl' : u'семнадцати'},
        {'im' : u'восемнадцать',    'rod' : u'восемнадцати',    'dat' : u'восемнадцати','vin' : u'восемнадцать',    'tvor' : u'восемнадцатью',  'predl' : u'восемнадцати'},
        {'im' : u'девятнадцать',    'rod' : u'девятнадцати',    'dat' : u'девятнадцати','vin' : u'девятнадцать',    'tvor' : u'девятнадцатью',  'predl' : u'девятнадцати'},
    )

hundreds = (
        {'im' : u'',            'rod' : u'',            'dat' : u'',            'vin' : u'',            'tvor' : u'',               'predl' : u''},
        {'im' : u'сто',         'rod' : u'ста',         'dat' : u'ста',         'vin' : u'сто',         'tvor' : u'ста',            'predl' : u'ста'},
        {'im' : u'двести',      'rod' : u'двухсот',     'dat' : u'двумстам',    'vin' : u'двести',      'tvor' : u'двумястами',     'predl' : u'двухстах'},
        {'im' : u'триста',      'rod' : u'трёхсот',     'dat' : u'трёмстам',    'vin' : u'триста',      'tvor' : u'тремястами',     'predl' : u'трёхстах'},
        {'im' : u'четыреста',   'rod' : u'четырёхсот',  'dat' : u'четырёмстам', 'vin' : u'четыреста',   'tvor' : u'четырьмястами',  'predl' : u'четырёхстах'},
        {'im' : u'пятьсот',     'rod' : u'пятисот',     'dat' : u'пятистам',    'vin' : u'пятьсот',     'tvor' : u'пятьюстами',     'predl' : u'пятистах'},
        {'im' : u'шестьсот',    'rod' : u'шестисот',    'dat' : u'шестистам',   'vin' : u'шестьсот',    'tvor' : u'шестьюстами',    'predl' : u'шестистах'},
        {'im' : u'семьсот',     'rod' : u'семисот',     'dat' : u'семистам',    'vin' : u'семьсот',     'tvor' : u'семьюстами',     'predl' : u'семистах'},
        {'im' : u'восемьсот',   'rod' : u'восьмисот',   'dat' : u'восьмистам',  'vin' : u'восемьсот',   'tvor' : u'восемьюстами',   'predl' : u'восьмистах'},
        {'im' : u'девятьсот',   'rod' : u'девятисот',   'dat' : u'девятистам',  'vin' : u'девятьсот',   'tvor' : u'девятьюстами',   'predl' : u'девятистах'}
    )

razryad_single = (
        {'im' : u'',            'rod' : u'',            'dat' : u'',            'vin' : u'',            'tvor' : u'',               'predl' : u''},
        {'im' : u'тысяча',      'rod' : u'тысячи',      'dat' : u'тысяче',      'vin' : u'тысячу',      'tvor' : u'тысячей',        'predl' : u'тысяче'},
        {'im' : u'миллион',     'rod' : u'миллиона',    'dat' : u'миллиону',    'vin' : u'миллион',     'tvor' : u'миллионом',      'predl' : u'миллионе'},
        {'im' : u'миллиард',    'rod' : u'миллиарда',   'dat' : u'миллиарду',   'vin' : u'миллиард',    'tvor' : u'миллиардом',     'predl' : u'миллиарде'},
        {'im' : u'триллион',    'rod' : u'триллиона',   'dat' : u'триллиону',   'vin' : u'триллион',    'tvor' : u'триллионом',     'predl' : u'триллионе'},
    )

razryad_plural = (
        {'im' : u'',            'rod' : u'',             'dat' : u'',            'vin' : u'',            'tvor' : u'',               'predl' : u''},
        {'im' : u'тысяч',       'rod' : u'тысяч',        'dat' : u'тысячам',     'vin' : u'тысяч',      'tvor' : u'тысячами',       'predl' : u'тысячах'},
        {'im' : u'миллион',     'rod' : u'миллионов',    'dat' : u'миллионам',   'vin' : u'миллион',    'tvor' : u'миллионами',     'predl' : u'миллионах'},
        {'im' : u'миллиард',    'rod' : u'миллиардов',   'dat' : u'миллиардам',  'vin' : u'миллиард',   'tvor' : u'миллиардами',    'predl' : u'миллиардах'},
        {'im' : u'триллион',    'rod' : u'триллионов',   'dat' : u'триллионам',  'vin' : u'триллион',   'tvor' : u'триллионами',    'predl' : u'триллионах'},
    )
odna = {
    'im' : u'одна',
    'rod' : u'одной',
    'dat' : u'одной',
    'vin' : u'одну',
    'tvor' : u'одной',
    'predl' : u'одной'
}
odin = {
    'im' : u'один',
    'rod' : u'одного',
    'dat' : u'одному',
    'vin' : u'один',
    'tvor' : u'одним',
    'predl' : u'одном'
}
odno = {
    'im' : u'одно',
    'rod' : u'одно',
    'dat' : u'одному',
    'vin' : u'одно',
    'tvor' : u'одним',
    'predl' : u'одном'
}

dva = {
    'im' : u'два',
    'rod' : u'двух',
    'dat' : u'двум',
    'vin' : u'два',
    'tvor' : u'двумя',
    'predl' : u'двух'
}
dve = {
    'im' : u'две',
    'rod' : u'двух',
    'dat' : u'двум',
    'vin' : u'две',
    'tvor' : u'двумя',
    'predl' : u'двух'
}

def short_num(num, razr, gender = 'm', padezh = 'im'): # f, n
    result = hundreds[num / 100][padezh]
    if result:
        result = u' ' + result

    if not num:
        return u""

    t = (num % 100) / 10            # десятки
    o = num % 10                    # единицы

    if t != 1:                      #   1   2   20  50    100   123
        result += u" " + tens[t][padezh] if t > 1 else u""

        if o == 1:                  #   1   2   0   0       0   3
            if razr == 1:
                result += u' ' + odna[padezh]
            elif razr > 1:
                result += u' ' + odin[padezh]
            else:
                if gender == 'm':
                    result += u' ' + odin[padezh]
                elif gender == 'f':
                    result += u' ' + odna[padezh]
                else:
                    result += u' ' + odno[padezh]
        elif o == 2:
            if razr == 1:
                result += u' ' + dve[padezh]
            elif razr > 1:
                result += u' ' + dva[padezh]
            else:
                if gender == 'm':
                    result += u' ' + dva[padezh]
                elif gender == 'f':
                    result += u' ' + dve[padezh]
                else:
                    result += u' ' + dva[padezh]
        elif 3 <= o <= 9:
            result += u" " + ones[o - 3][padezh]

        if o == 1:
            if razr > 0:                                   # одна тысяча
                result += u" " + razryad_single[razr][padezh]
        elif 2 <= o <= 4:
            if razr == 1:           # две тысячи
                result += u" " + razryad_plural[razr][padezh]
                if padezh in ('im', 'vin'):
                    result += u'и'
            else:
                if razr > 1:        # два миллиона
                    result += u" " + razryad_plural[razr][padezh]
                    if padezh in ('im', 'vin'):
                        result += u'а'
                else:               # два
                    pass
        else:
            if razr > 1:            # пять миллионов
                result += u" " + razryad_plural[razr][padezh]
                if padezh in ('im', 'vin'):
                    result += u"ов"
            elif razr == 1:         # пять тысяч
                result += u" " + razryad_plural[razr][padezh]
            else:                   # пять
                pass
    else: # 10, 11, 12 - 19
        result += u" " + ones[num % 100 - 3][padezh]
        if razr > 0:
            result += u" "
        result += razryad_plural[razr][padezh]
        if razr > 1 and padezh in ('im', 'vin'):
            result += u'ов'

    return result

def num_word(s, gender = 'm', padezh = 'im'):
    zeros = {
        "im" : u"ноль",
        "rod" : u"ноля",
        "dat" : u"нолю",
        "vin" : u"ноль",
        "tvor" : u"нолём",
        "predl" : u"ноле"
    }
    s = unicode(s)
    if len(s) <= 0 or s == u'0':
        return zeros[padezh]

    count = (len(s) + 2) / 3
    if count > 5:
        return s

    result = u""
    s = u'00' + s

    for i in xrange(1, count + 1):
        result = short_num(int(s[len(s) - 3 * i: len(s) - 3 * i + 3]), i - 1, gender, padezh) + result

    if len(result) > 0 and result[0] == u" ":
        result = result[1:]

    return result

WORD_NUM_DATA = {
    #                  1         2, 3, 4    5, 6, 7, 8, 9, 10, 11-20
    u"рубль" : (
        {'im' : u'рубль',   'rod' : u'рубля',   'dat' : u'рублю',   'vin' : u'рубль',   'tvor' : u'рублём',  'predl' : u'рубле'},   # 1
        {'im' : u'рубля',   'rod' : u'рублей',  'dat' : u'рублям',  'vin' : u'рубля',   'tvor' : u'рублями', 'predl' : u'рублях'},  # 2 - 4
        {'im' : u'рублей',  'rod' : u'рублей',  'dat' : u'рублям',  'vin' : u'рублей',  'tvor' : u'рублями', 'predl' : u'рублях'},  # 5 - 20
    ),
    u"копейка" : (
        {'im' : u'копейка', 'rod' : u'копейки', 'dat' : u'копейке',   'vin' : u'копейку', 'tvor' : u'копейкой',  'predl' : u'копейке'},   # 1
        {'im' : u'копейки', 'rod' : u'копеек',  'dat' : u'копейкам',  'vin' : u'копейки', 'tvor' : u'копейками', 'predl' : u'копейках'},  # 2 - 4
        {'im' : u'копеек',  'rod' : u'копеек',  'dat' : u'копейкам',  'vin' : u'копеек',  'tvor' : u'копейками', 'predl' : u'копейках'},  # 5 - 20
    ),
    u"доллар США" : (
        {'im' : u'доллар США',  'rod' : u'доллара США', 'dat' : u'доллару США',   'vin' : u'доллар США',  'tvor' : u'долларом США',  'predl' : u'долларе США'},   # 1
        {'im' : u'доллара США', 'rod' : u'долларов США','dat' : u'долларам США',  'vin' : u'доллара США', 'tvor' : u'долларами США', 'predl' : u'долларах США'},  # 2 - 4
        {'im' : u'долларов США','rod' : u'долларов США','dat' : u'долларам США',  'vin' : u'долларов США','tvor' : u'долларами США', 'predl' : u'долларах США'},  # 5 - 20
    ),
    u"цент" : (
        {'im' : u'цент',  'rod' : u'цента', 'dat' : u'центу',   'vin' : u'цент',  'tvor' : u'центом',  'predl' : u'центе'},   # 1
        {'im' : u'цента', 'rod' : u'центов','dat' : u'центам',  'vin' : u'цента', 'tvor' : u'центами', 'predl' : u'центах'},  # 2 - 4
        {'im' : u'центов','rod' : u'центов','dat' : u'центам',  'vin' : u'центов','tvor' : u'центами', 'predl' : u'центах'},  # 5 - 20
    ),
    #u"евро" : lambda x: lambda y: u'евро',
    u"евроцент" : (
        {'im' : u'евроцент',  'rod' : u'евроцента', 'dat' : u'евроценту',   'vin' : u'евроцент',  'tvor' : u'евроцентом',  'predl' : u'евроценте'},   # 1
        {'im' : u'евроцента', 'rod' : u'евроцентов','dat' : u'евроцентам',  'vin' : u'евроцента', 'tvor' : u'евроцентами', 'predl' : u'евроцентах'},  # 2 - 4
        {'im' : u'евроцентов','rod' : u'евроцентов','dat' : u'евроцентам',  'vin' : u'евроцентов','tvor' : u'евроцентами', 'predl' : u'евроцентах'},  # 5 - 20
    ),
    u"день" : (
        {'im' : u'день',  'rod' : u'дня',   'dat' : u'дню',   'vin' : u'день',  'tvor' : u'днём',  'predl' : u'дне'},   # 1
        {'im' : u'дня',   'rod' : u'дней',  'dat' : u'дням',  'vin' : u'дня',   'tvor' : u'днями', 'predl' : u'днях'},  # 2 - 4
        {'im' : u'дней',  'rod' : u'дней',  'dat' : u'дням',  'vin' : u'дней',  'tvor' : u'днями', 'predl' : u'днях'},  # 5 - 20
    ),
    u"год" : (
            {'im' : u'год', 'rod' : u'года',   'dat' : u'году',   'vin' : u'год',  'tvor' : u'годом',  'predl' : u'годе'},   # 1
            {'im' : u'года','rod' : u'лет',   'dat' : u'годам',  'vin' : u'года', 'tvor' : u'годами', 'predl' : u'годах'},  # 2 - 4
            {'im' : u'лет', 'rod' : u'лет',   'dat' : u'годам',  'vin' : u'лет',  'tvor' : u'годами', 'predl' : u'годах'},  # 5 - 20
        ),
    u"месяц" : (
            {'im' : u'месяц', 'rod' : u'месяца',   'dat' : u'месяцу',   'vin' : u'месяц',  'tvor' : u'месяцем',  'predl' : u'месяце'},   # 1
            {'im' : u'месяца','rod' : u'месяцев',   'dat' : u'месяцам',  'vin' : u'месяца', 'tvor' : u'месяцами', 'predl' : u'месяцах'},  # 2 - 4
            {'im' : u'месяцев', 'rod' : u'месяцев',   'dat' : u'месяцам',  'vin' : u'месяцев',  'tvor' : u'месяцами', 'predl' : u'месяцах'},  # 5 - 20
    ),
    u"член" : (
        {'im' : u'член',  'rod' : u'члена',   'dat' : u'члену',   'vin' : u'член',  'tvor' : u'членом',  'predl' : u'члене'},   # 1
        {'im' : u'члена', 'rod' : u'членов',  'dat' : u'членам',  'vin' : u'члена', 'tvor' : u'членами', 'predl' : u'членах'},  # 2 - 4
        {'im' : u'членов','rod' : u'членов',  'dat' : u'членам',  'vin' : u'членов','tvor' : u'членами', 'predl' : u'членах'},  # 5 - 20
    ),
    u"процент" : (
        {'im' : u'процент',  'rod' : u'процента',   'dat' : u'проценту',   'vin' : u'процент',  'tvor' : u'процентом',  'predl' : u'проценте'},   # 1
        {'im' : u'процента', 'rod' : u'процентов',  'dat' : u'процентам',  'vin' : u'процента', 'tvor' : u'процентами', 'predl' : u'процентах'},  # 2 - 4
        {'im' : u'процентов','rod' : u'процентов',  'dat' : u'процентам',  'vin' : u'процентов','tvor' : u'процентами', 'predl' : u'процентах'},  # 5 - 20
    ),
    u"доля" : (
        {'im' : u'доля', 'rod' : u'доли', 'dat' : u'доле',   'vin' : u'долю', 'tvor' : u'долей',  'predl' : u'доле'},   # 1
        {'im' : u'доли', 'rod' : u'долей',  'dat' : u'долям',  'vin' : u'доли', 'tvor' : u'долями', 'predl' : u'долях'},  # 2 - 4
        {'im' : u'долей',  'rod' : u'долей',  'dat' : u'долям',  'vin' : u'долей',  'tvor' : u'долями', 'predl' : u'долях'},  # 5 - 20
    ),
    u"час" : (
        {'im' : u'час', 'rod' : u'часа', 'dat' : u'часу',   'vin' : u'час', 'tvor' : u'часом',  'predl' : u'часе'},   # 1
        {'im' : u'часа', 'rod' : u'часа',  'dat' : u'часам',  'vin' : u'часа', 'tvor' : u'часами', 'predl' : u'часах'},  # 2 - 4
        {'im' : u'часов',  'rod' : u'часов',  'dat' : u'часам',  'vin' : u'часов',  'tvor' : u'часами', 'predl' : u'часах'},  # 5 - 20
    ),
    u"минута" : (
        {'im' : u'минута', 'rod' : u'минуты', 'dat' : u'минуте',   'vin' : u'минуту', 'tvor' : u'минутой',  'predl' : u'минуте'},   # 1
        {'im' : u'минуты', 'rod' : u'минут',  'dat' : u'минутам',  'vin' : u'минуты', 'tvor' : u'минутами', 'predl' : u'минутах'},  # 2 - 4
        {'im' : u'минут',  'rod' : u'минут',  'dat' : u'минутам',  'vin' : u'минуты', 'tvor' : u'минутами', 'predl' : u'минутах'},  # 5 - 20
    ),
}

def word_from_num(word, num, padezh = 'im'):
    from fw.documents.fields.simple_doc_fields import DocField, DocIntField
    if isinstance(word, DocField):
        word = unicode(word)
    if isinstance(num, DocIntField):
        num = num.value
#    if num == 1500121 and padezh == 'rod':
#        a = 1 + 2
    if word not in WORD_NUM_DATA:
        return word
    item = WORD_NUM_DATA[word]
    if not word:
        return item[2][padezh]
    if 5 <= num <= 19:
        return item[2][padezh]
    num_str = str(num)
    if not num_str:
        num_str = '0'
    if num > 100:
        if num_str[-2:] in ('11', '12', '13', '14'):
            return item[2][padezh]
    if num_str[-1] == '1':
        return item[0][padezh]
    if num_str[-1] in ('2', '3', '4'):
        return item[1][padezh]
    return item[2][padezh]


class LazyClassLoader(object):

    POSSIBLE_LOCATIONS = ['fw.documents.fields.simple_doc_fields',
                          'fw.documents.fields.complex_doc_fields',
                          'fw.documents.fields.general_doc_fields',
                          'fw.documents.db_fields',
                          'fw.documents.fields.doc_fields',
                          'fw.documents.enums',
                          'fw.documents.address_enums',
                          'fw.api.args_validators'
                          #'adapters.llc_gov_forms_adapters',
                          #'db.meeting_doc_fields',
                          #'external_validators'
        ]

    def __init__(self, cls_name):
        self.cls_name = cls_name
        self.cls = None

    def __unicode__(self):
        return self.cls_name

    def load(self):
        if not self.cls:
            self.__load_class()
        return self.cls

    def __load_class(self):
        if self.cls:
            return

        try:
            self.cls = getattr(sys.modules[__name__], self.cls_name)
            return
        except Exception:
            if '.' not in self.cls_name:
                for item in LazyClassLoader.POSSIBLE_LOCATIONS:
                    try:
                        module = __import__(item, fromlist=[self.cls_name])
                        self.cls = getattr(module, self.cls_name)
                        return
                    except Exception:
                        pass
            else:
                try:
                    module = __import__('.'.join(self.cls_name.split('.')[:-1]), fromlist=[self.cls_name.split('.')[-1]])
                    self.cls = getattr(module, self.cls_name.split('.')[-1])
                    return
                except Exception:
                    for item in LazyClassLoader.POSSIBLE_LOCATIONS:
                        try:
                            module = __import__(item + '.' + '.'.join(self.cls_name.split('.')[:-1]), fromlist=[self.cls_name.split('.')[-1]])
                            self.cls = getattr(module, self.cls_name.split('.')[-1])
                            return
                        except Exception:
                            pass

        try:
            module = __import__(self.cls_name)
            self.cls = getattr(module, self.cls_name)
        except ImportError:
            pass

        raise ImportError(u"Class name: %s. path: << %s >>. __name__: %s" % (self.cls_name, unicode(sys.path), __name__))

    def __call__(self, *args, **kwargs):
        if not self.cls:
            self.__load_class()
        return self.cls(*args, **kwargs)

    def __getattr__(self, item):
        if item.startswith('_'):
            try:
                return self.__dict__[item]
            except KeyError:
                raise AttributeError(item)

        if not self.cls:
            self.__load_class()
        return getattr(self.cls, item)

def remove_task_id_run_file(config, task_id):
    file_name = os.path.join(os.path.dirname(config['celery_tasks_dir']), unicode(task_id))
    if os.path.exists(file_name):
        try:
            os.unlink(file_name)
        except Exception:
            pass

def as_dumpable(val):
    if isinstance(val, dict):
        tmp_dict = {}
        for k, v in val.items():
            if isinstance(v, ObjectId):
                tmp_dict[k] = unicode(v)
            elif type(v) in (tuple, dict, list):
                tmp_dict[k] = as_dumpable(v)
            else:
                tmp_dict[k] = v
        return tmp_dict
    elif type(val) in (list, tuple):
        tmp_list = []
        for i in val:
            if isinstance(i, ObjectId):
                tmp_list.append(unicode(i))
            elif type(i) in (tuple, dict, list):
                tmp_list.append(as_dumpable(i))
            else:
                tmp_list.append(i)
        return tmp_list
    elif isinstance(val, ObjectId):
        return unicode(val)
    return val

def day_name(day):
    if day == 1:
        return u"понедельник"
    if day == 2:
        return u"вторник"
    if day == 3:
        return u"среда"
    if day == 4:
        return u"четверг"
    if day == 5:
        return u"пятница"
    if day == 6:
        return u"суббота"
    if day == 7:
        return u"воскресенье"

def day_short_name(day):
    if day == 1:
        return u"пн"
    if day == 2:
        return u"вт"
    if day == 3:
        return u"ср"
    if day == 4:
        return u"чт"
    if day == 5:
        return u"пт"
    if day == 6:
        return u"сб"
    if day == 7:
        return u"вс"


def try_several_requests(url, tries, method, *args, **kwargs):
    method = method or requests.get
    last_error = None
    for x in xrange(tries):
        try:
            return method(url, *args, **kwargs)
        except (ConnectionError, Timeout), ex:
            last_error = ex
    raise last_error

def make_cache_key(some_string):
    m = hashlib.md5()
    if isinstance(some_string, unicode):
        m.update(some_string.encode('utf-8'))
    else:
        m.update(some_string)
    return m.hexdigest()

def int_to_ifns(val):
    val = unicode(val)[:4]
    return val if len(val) == 4 else "0" * (4 - len(val)) + val

DDS = {
    0: u"нулевое",
    1: u"первое",
    2: u"второе",
    3: u"третье",
    4: u"четвертое",
    5: u"пятое",
    6: u"шестое",
    7: u"седьмое",
    8: u"восьмое",
    9: u"девятое",
    10: u"десятое",
    11: u"одиннадцатое",
    12: u"двенадцатое",
    13: u"тринадцатое",
    14: u"четырнадцатое",
    15: u"пятнадцатое",
    16: u"шестнадцатое",
    17: u"семнадцатое",
    18: u"восемнадцатое",
    19: u"девятнадцатое",
    20: u"двадцатое",
    21: u"двадцать первое",
    22: u"двадцать второе",
    23: u"двадцать третье",
    24: u"двадцать четвертое",
    25: u"двадцать пятое",
    26: u"двадцать шестое",
    27: u"двадцать седьмое",
    28: u"двадцать восьмое",
    29: u"двадцать девятое",
    30: u"тридцатое",
    31: u"тридцать первое",
    32: u"тридцать второе"
}

def day_for_date_str(day):
    return DDS.get(day, u"")

YDS = {
    2010: u"две тысячи десятого",
    2011: u"две тысячи одиннадцатого",
    2012: u"две тысячи двенадцатого",
    2013: u"две тысячи тринадцатого",
    2014: u"две тысячи четырнадцатого",
    2015: u"две тысячи пятнадцатого",
    2016: u"две тысячи шестнадцатого",
    2017: u"две тысячи семнадцатого",
    2018: u"две тысячи восемнадцатого",
    2019: u"две тысячи девятнадцатого",
    2020: u"две тысячи двадцатого"
}

def year_for_date_str(year):
    assert year >= 2010
    return YDS.get(year, u"две тысячи пятнадцатого")
