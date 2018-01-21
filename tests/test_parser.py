"""Tests for leyline parser"""
import difflib

import pytest

from leyline.parser import Parser
from leyline.ast import (Document, Text, TextBlock, Bold, Italics,
    Underline, Strikethrough, With, RenderFor, List, Table, Comment)


def difftree(x, y, xname='expected', yname='observed'):
    s = str(x).splitlines(True)
    t = str(y).splitlines(True)
    d = ''.join(difflib.unified_diff(s, t, fromfile=xname, tofile=yname))
    return d


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
    '* x\n* y\n* z': Document(lineno=1, column=1, body=[
        List(lineno=1, column=1, bullets='*', items=[
            [TextBlock(lineno=1, column=3, body=[
                Text(lineno=1, column=3, text='x\n'),
                ])],
            [TextBlock(lineno=2, column=3, body=[
                Text(lineno=2, column=3, text='y\n'),
                ])],
            [TextBlock(lineno=3, column=3, body=[
                Text(lineno=3, column=3, text='z'),
                ])],
            ]),
        ]),
    '1. x\n2. y\n3. z': Document(lineno=1, column=1, body=[
        List(lineno=1, column=1, bullets=[1, 2, 3], items=[
            [TextBlock(lineno=1, column=4, body=[
                Text(lineno=1, column=4, text='x\n'),
                ])],
            [TextBlock(lineno=2, column=4, body=[
                Text(lineno=2, column=4, text='y\n'),
                ])],
            [TextBlock(lineno=3, column=4, body=[
                Text(lineno=3, column=4, text='z'),
                ])],
            ]),
        ]),
    # nested list
    '1. x\n  * y\n2. z': Document(lineno=1, column=1, body=[
        List(lineno=1, column=1, bullets=[1, 2], items=[
            [TextBlock(lineno=1, column=4, body=[
                Text(lineno=1, column=4, text='x'),
                ]),
             List(lineno=2, column=3, bullets='*', items=[
                [TextBlock(lineno=2, column=5, body=[
                    Text(lineno=2, column=5, text='y'),
                    ]),
                ]]),
             ],
            [TextBlock(lineno=3, column=4, body=[
                Text(lineno=3, column=4, text='z'),
                ])],
            ]),
        ]),
    # double list
    '- * a\n  * b\n  * c\n- * x\n  * y\n  * z': Document(lineno=1, column=1, body=[
        List(lineno=1, column=1, bullets='-', items=[
            [
            List(lineno=1, column=3, bullets='*', items=[
                [TextBlock(lineno=1, column=5, body=[
                    Text(lineno=1, column=5, text='a\n  '),
                    ])],
                [TextBlock(lineno=2, column=5, body=[
                    Text(lineno=2, column=5, text='b\n  '),
                    ])],
                [TextBlock(lineno=3, column=5, body=[
                    Text(lineno=3, column=5, text='c'),
                   ])],
                ]),
            ],
            [
            List(lineno=4, column=3, bullets='*', items=[
                [TextBlock(lineno=4, column=5, body=[
                    Text(lineno=4, column=5, text='x\n  '),
                    ])],
                [TextBlock(lineno=5, column=5, body=[
                    Text(lineno=5, column=5, text='y\n  '),
                    ])],
                [TextBlock(lineno=6, column=5, body=[
                    Text(lineno=6, column=5, text='z'),
                   ])],
                ]),
            ],
            ]),
        ]),
    # table
    ('table::\n'
     '  - * a\n'
     '    * b\n'
     '    * c\n'
     '  - * x\n'
     '    * y\n'
     '    * z'): Document(lineno=1, column=1, body=[
        Table(lineno=1, column=1, header_rows=1,
              header_cols=0, widths='auto', rows=[
            [
                [TextBlock(lineno=2, column=7, body=[
                    Text(lineno=2, column=7, text='a\n    '),
                    ])],
                [TextBlock(lineno=3, column=7, body=[
                    Text(lineno=3, column=7, text='b\n    '),
                    ])],
                [TextBlock(lineno=4, column=7, body=[
                    Text(lineno=4, column=7, text='c'),
                   ])],
            ],
            [
                [TextBlock(lineno=5, column=7, body=[
                    Text(lineno=5, column=7, text='x\n    '),
                    ])],
                [TextBlock(lineno=6, column=7, body=[
                    Text(lineno=6, column=7, text='y\n    '),
                    ])],
                [TextBlock(lineno=7, column=7, body=[
                    Text(lineno=7, column=7, text='z'),
                   ])],
            ],
            ]),
        ]),
    # Table with metadata
    ('table::\n'
     '  header_rows = 42\n'
     '  header_cols = 6\n'
     '  widths = 1 3\n'
     '  - * a\n'
     '    * z'): Document(lineno=1, column=1, body=[
        Table(lineno=1, column=1, header_rows=42,
              header_cols=6, widths=[0.25, 0.75], rows=[
            [
                [TextBlock(lineno=5, column=7, body=[
                    Text(lineno=5, column=7, text='a\n    '),
                    ])],
                [TextBlock(lineno=6, column=7, body=[
                    Text(lineno=6, column=7, text='z'),
                   ])],
            ],
            ]),
        ]),
    # text, simple comment, text
    ('hello\n'
     '# such comment, much wow\n'
     'world'): Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
                  Text(lineno=1, column=1, text='hello\n'),
                  ]),
        Comment(lineno=2, column=1, text='such comment, much wow'),
        TextBlock(lineno=3, column=1, body=[
                  Text(lineno=3, column=1, text='world'),
                  ]),
        ]),
    # text, merged comment, text
    ('hello\n'
     '# such comment\n'
     '# much wow\n'
     'world'): Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
                  Text(lineno=1, column=1, text='hello\n'),
                  ]),
        Comment(lineno=2, column=1, text='such comment\nmuch wow'),
        TextBlock(lineno=4, column=1, body=[
                  Text(lineno=4, column=1, text='world'),
                  ]),
        ]),
    # text, multilinecomment, text
    ('hello\n'
     '###\n'
     'such comment\n'
     'much wow\n'
     '###\n'
     'world'): Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
                  Text(lineno=1, column=1, text='hello\n'),
                  ]),
        Comment(lineno=2, column=1, text='\nsuch comment\nmuch wow\n'),
        TextBlock(lineno=6, column=1, body=[
                  Text(lineno=6, column=1, text='world'),
                  ]),
        ]),
}


@pytest.mark.parametrize('doc, exp', PARSE_CASES.items())
def test_parse(doc, exp):
    obs = PARSER.parse(doc, debug_level=0)
    #PARSER.lexer.input(doc)
    #print(list(PARSER.lexer))
    assert exp == obs, difftree(exp, obs)


BAD_PARSE_CASES = [
    "with  two_spaces::\n  yes",
    "rend t0   t1::\n  no",
    "rend   t0 t1::\n  no",
]


@pytest.mark.parametrize('doc', BAD_PARSE_CASES)
def test_bad_parse(doc):
    with pytest.raises(SyntaxError):
        obs = PARSER.parse(doc)
