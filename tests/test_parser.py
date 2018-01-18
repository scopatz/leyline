"""Tests for leyline parser"""
from leyline.parser import Parser
from leyline.ast import Document, Text

import pytest


PARSER = Parser(lexer_optimize=False, yacc_optimize=False, yacc_debug=True)

PARSE_CASES = {
    '': Document(lineno=1, column=1),
}


@pytest.mark.parametrize('doc, exp', PARSE_CASES.items())
def test_parse(doc, exp):
    obs = PARSER.parse(doc)
    assert exp == obs