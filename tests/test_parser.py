"""Tests for leyline parser"""
from leyline.parser import Parser
from leyline.ast import (Document, Text, TextBlock, Bold, Italics,
    Underline, Strikethrough, With)

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
    'with:\n  x = (\n    1, 2,\n  )\n': Document(lineno=1, column=1, body=[
        With(lineno=1, column=1, ctx='', text='x = (\n  1, 2,\n)'),
        ]),
    'with meta:\n  x = (\n    1, 2,\n  )\n': Document(lineno=1, column=1, body=[
        With(lineno=1, column=1, ctx='meta', text='x = (\n  1, 2,\n)'),
        ]),
    'with table:\n  x = (\n    1, 2,\n  )\n': Document(lineno=1, column=1, body=[
        With(lineno=1, column=1, ctx='table', text='x = (\n  1, 2,\n)'),
        ]),
}


@pytest.mark.parametrize('doc, exp', PARSE_CASES.items())
def test_parse(doc, exp):
    obs = PARSER.parse(doc)
    assert exp == obs
