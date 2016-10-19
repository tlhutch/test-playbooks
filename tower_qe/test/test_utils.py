# -*- coding: utf-8 -*-

import pytest

from qe import utils


@pytest.mark.parametrize('inp, out',
                         [['', ''],
                          [(), '()'],
                          [[], '[]'],
                          [{}, '{}'],
                          [123, '123'],
                          [-123, '-123'],
                          [True, 'True'],
                          [False, 'False'],
                          [b'åå∫∫çç∂∂´´ƒƒ\xff\xff',
                           '\xc3\xa5\xc3\xa5\xe2\x88\xab\xe2\x88\xab\xc3\xa7\xc3\xa7\xe2\x88'
                           '\x82\xe2\x88\x82\xc2\xb4\xc2\xb4\xc6\x92\xc6\x92\xff\xff'],
                          [u'åå∫∫çç∂∂´´ƒƒ\xff\xff',
                           '\\xe5\\xe5\\u222b\\u222b\\xe7\\xe7\\u2202\\u2202\\xb4\\xb4'
                           '\\u0192\\u0192\\xff\\xff'],
                          [b'زه شيشه خوړلې شم، هغه ما نه خوږوي',
                           '\xd8\xb2\xd9\x87 \xd8\xb4\xd9\x8a\xd8\xb4\xd9\x87 '
                           '\xd8\xae\xd9\x88\xda\x93\xd9\x84\xdb\x90 \xd8\xb4\xd9\x85\xd8\x8c '
                           '\xd9\x87\xd8\xba\xd9\x87 \xd9\x85\xd8\xa7 \xd9\x86\xd9\x87 '
                           '\xd8\xae\xd9\x88\xda\x96\xd9\x88\xd9\x8a'],
                          [u'زه شيشه خوړلې شم، هغه ما نه خوږوي',
                           '\\u0632\\u0647 \\u0634\\u064a\\u0634\\u0647 '
                           '\\u062e\\u0648\\u0693\\u0644\\u06d0 \\u0634\\u0645\\u060c '
                           '\\u0647\\u063a\\u0647 \\u0645\\u0627 \\u0646\\u0647 '
                           '\\u062e\\u0648\\u0696\\u0648\\u064a']])
def test_to_str(inp, out):
    assert(utils.to_str(inp) == out)
