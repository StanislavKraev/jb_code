# -*- coding: utf-8 -*-

from base_test_case import BaseTestCase
from template_filters import texify


class TexTestCase(BaseTestCase):

    def test_texify(self):
        self.maxDiff = None
        self.assertEqual(texify(u'<>%${}_¶‡|–—™£#&§\\®©¿«»'), ur'\textless\textgreater\%\$\{\}\_\P\ddag\textbar\textendash\textemdash'
                                                              ur'\texttrademark\pounds\#\&\S\textbackslash\textregistered\copyright\textquestiondown<<>>')