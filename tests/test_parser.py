"""Tests for leyline parser"""
from leyline.parser import Parser
from leyline.ast import (Document, Text, TextBlock, Bold, Italics,
    Underline, Strikethrough, With, RenderFor)

import pytest


PARSER = Parser(lexer_optimize=False, yacc_optimize=False, yacc_debug=True)

PARSE_CASES = {
    '': Document(lineno=1, column=1),
    'hello world': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            Text(lineno=1, column=1, text='hello world')])
        ]),
    'hello **world**': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            Text(lineno=1, column=1, text='hello '),
            Bold(lineno=1, column=7, body=[
                Text(lineno=1, column=9, text='world')])
            ])
        ]),
    '~~hello **world**~~': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            Italics(lineno=1, column=1, body=[
                Text(lineno=1, column=3, text='hello '),
                Bold(lineno=1, column=9, body=[
                    Text(lineno=1, column=11, text='world')])
                ])
            ])
        ]),
    '--hello __world__--': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            Strikethrough(lineno=1, column=1, body=[
                Text(lineno=1, column=3, text='hello '),
                Underline(lineno=1, column=9, body=[
                    Text(lineno=1, column=11, text='world')])
                ])
            ])
        ]),
    'rend x::\n  some text\n': Document(lineno=1, column=1, body=[
        RenderFor(lineno=1, column=1, targets=set(['x']), body=[
            TextBlock(lineno=2, column=3, body=[
                Text(lineno=2, column=3, text='some text')
                ])
            ])
        ]),
    'rend x y::\n  some text\n': Document(lineno=1, column=1, body=[
        RenderFor(lineno=1, column=1, targets=set(['x', 'y']), body=[
            TextBlock(lineno=2, column=3, body=[
                Text(lineno=2, column=3, text='some text')
                ])
            ])
        ]),
    'rend x y::\n  some text\n  rend x::\n    only in x\n  in x & y\n': Document(lineno=1, column=1, body=[
        RenderFor(lineno=1, column=1, targets=set(['x', 'y']), body=[
            TextBlock(lineno=2, column=3, body=[
                Text(lineno=2, column=3, text='some text\n  '),
                ]),
            RenderFor(lineno=3, column=3, targets=set(['x']), body=[
                TextBlock(lineno=4, column=5, body=[
                    Text(lineno=4, column=5, text='only in x'),
                    ]),
                ]),
            TextBlock(lineno=5, column=3, body=[
                Text(lineno=5, column=3, text='in x & y'),
                ]),
            ])
        ]),
    'with::\n  x = (\n    1, 2,\n  )\n': Document(lineno=1, column=1, body=[
        With(lineno=1, column=1, ctx='', text='x = (\n  1, 2,\n)'),
        ]),
    'with meta::\n  x = (\n    1, 2,\n  )\n': Document(lineno=1, column=1, body=[
        With(lineno=1, column=1, ctx='meta', text='x = (\n  1, 2,\n)'),
        ]),
    'with table::\n  x = (\n    1, 2,\n  )\n': Document(lineno=1, column=1, body=[
        With(lineno=1, column=1, ctx='table', text='x = (\n  1, 2,\n)'),
        ]),
}


@pytest.mark.parametrize('doc, exp', PARSE_CASES.items())
def test_parse(doc, exp):
    obs = PARSER.parse(doc)
    assert exp == obs
