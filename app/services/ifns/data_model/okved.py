# -*- coding: utf-8 -*-


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


class OkvedEnum(object):

    @staticmethod
    def get_name(code):
        if len(code) > 2 and '.' not in code:
            code = ''.join(chunks(code, 2))
            if len(code) < 6:
                code += u" " * (6 - len(code))
        elif len(code) > 2 and '.' in code:
            code_parts = [part for part in code.split('.')]
            while len(code_parts) < 3:
                code_parts.append(None)

            parts_str_array = []
            for part in code_parts:
                if part is not None:
                    part_str = unicode(part)
                    if len(part_str) < 2:
                        part_str += u" "
                    parts_str_array.append(part_str)
                else:
                    parts_str_array.append(u"  ")
            code = u"".join(parts_str_array)
        return code

    @staticmethod
    def get_title(code):
        from fw.catalogs.models import OkvadObject
        okvad = OkvadObject.query.filter_by(okved=code).first()
        return okvad.caption if okvad else u""

    # noinspection PyUnusedLocal
    @classmethod
    def validate(cls, value):
        return True
