"""Tests for leyline parser"""
import difflib

import pytest

from leyline.parser import Parser
from leyline.ast import (Document, PlainText, TextBlock, Bold, Italics,
    Underline, Strikethrough, With, RenderFor, List, Table, Comment,
    CodeBlock, InlineCode, Equation, InlineMath, CorporealMacro,
    IncorporealMacro, Figure, Superscript, Subscript)


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
            PlainText(lineno=1, column=1, text='hello world')])
        ]),
    'hello **world**': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            PlainText(lineno=1, column=1, text='hello '),
            Bold(lineno=1, column=7, body=[
                PlainText(lineno=1, column=9, text='world')])
            ])
        ]),
    'hello {^world^}': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            PlainText(lineno=1, column=1, text='hello '),
            Superscript(lineno=1, column=7, body=[
                PlainText(lineno=1, column=9, text='world')])
            ])
        ]),
    'hello {_world_}': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            PlainText(lineno=1, column=1, text='hello '),
            Subscript(lineno=1, column=7, body=[
                PlainText(lineno=1, column=9, text='world')])
            ])
        ]),
    '~~hello **world**~~': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            Italics(lineno=1, column=1, body=[
                PlainText(lineno=1, column=3, text='hello '),
                Bold(lineno=1, column=9, body=[
                    PlainText(lineno=1, column=11, text='world')])
                ])
            ])
        ]),
    '--hello __world__--': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            Strikethrough(lineno=1, column=1, body=[
                PlainText(lineno=1, column=3, text='hello '),
                Underline(lineno=1, column=9, body=[
                    PlainText(lineno=1, column=11, text='world')])
                ])
            ])
        ]),
    'hello `world`': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            PlainText(lineno=1, column=1, text='hello '),
            InlineCode(lineno=1, column=7, lang='', text='world')
            ])
        ]),
    'hello $\kappa$': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            PlainText(lineno=1, column=1, text='hello '),
            InlineMath(lineno=1, column=7, lang='', text='\kappa')
            ])
        ]),
    'hello {{"{{world}}"}}': Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
            PlainText(lineno=1, column=1, text='hello '),
            IncorporealMacro(lineno=1, column=7, lang='', text='"{{world}}"')
            ])
        ]),
    '{% repeat 10 %}hello world{%}': Document(lineno=1, column=1, body=[
        CorporealMacro(lineno=1, column=1, name='repeat', args='10', body=[
            TextBlock(lineno=1, column=16, body=[
                PlainText(lineno=1, column=16, text='hello world'),
                ])
            ])
        ]),
    'rend x::\n  some text\n': Document(lineno=1, column=1, body=[
        RenderFor(lineno=1, column=1, targets=set(['x']), body=[
            TextBlock(lineno=2, column=3, body=[
                PlainText(lineno=2, column=3, text='some text')
                ])
            ])
        ]),
    'rend x y::\n  some text\n': Document(lineno=1, column=1, body=[
        RenderFor(lineno=1, column=1, targets=set(['x', 'y']), body=[
            TextBlock(lineno=2, column=3, body=[
                PlainText(lineno=2, column=3, text='some text')
                ])
            ])
        ]),
    'rend x y::\n  some text\n  rend x::\n    only in x\n  in x & y\n': Document(lineno=1, column=1, body=[
        RenderFor(lineno=1, column=1, targets=set(['x', 'y']), body=[
            TextBlock(lineno=2, column=3, body=[
                PlainText(lineno=2, column=3, text='some text\n  '),
                ]),
            RenderFor(lineno=3, column=3, targets=set(['x']), body=[
                TextBlock(lineno=4, column=5, body=[
                    PlainText(lineno=4, column=5, text='only in x'),
                    ]),
                ]),
            TextBlock(lineno=5, column=3, body=[
                PlainText(lineno=5, column=3, text='in x & y'),
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
                PlainText(lineno=1, column=3, text='x'),
                ])],
            [TextBlock(lineno=2, column=3, body=[
                PlainText(lineno=2, column=3, text='y'),
                ])],
            [TextBlock(lineno=3, column=3, body=[
                PlainText(lineno=3, column=3, text='z'),
                ])],
            ]),
        ]),
    '1. x\n2. y\n3. z': Document(lineno=1, column=1, body=[
        List(lineno=1, column=1, bullets=[1, 2, 3], items=[
            [TextBlock(lineno=1, column=4, body=[
                PlainText(lineno=1, column=4, text='x'),
                ])],
            [TextBlock(lineno=2, column=4, body=[
                PlainText(lineno=2, column=4, text='y'),
                ])],
            [TextBlock(lineno=3, column=4, body=[
                PlainText(lineno=3, column=4, text='z'),
                ])],
            ]),
        ]),
    # nested list
    '1. x\n   * y\n2. z': Document(lineno=1, column=1, body=[
        List(lineno=1, column=1, bullets=[1, 2], items=[
            [TextBlock(lineno=1, column=4, body=[
                PlainText(lineno=1, column=4, text='x\n   '),
                ]),
             List(lineno=2, column=4, bullets='*', items=[
                [TextBlock(lineno=2, column=6, body=[
                    PlainText(lineno=2, column=6, text='y'),
                    ]),
                ]]),
             ],
            [TextBlock(lineno=3, column=4, body=[
                PlainText(lineno=3, column=4, text='z'),
                ])],
            ]),
        ]),
    # double list
    '- * a\n  * b\n  * c\n- * x\n  * y\n  * z': Document(lineno=1, column=1, body=[
        List(lineno=1, column=1, bullets='-', items=[
            [
            List(lineno=1, column=3, bullets='*', items=[
                [TextBlock(lineno=1, column=5, body=[
                    PlainText(lineno=1, column=5, text='a'),
                    ])],
                [TextBlock(lineno=2, column=5, body=[
                    PlainText(lineno=2, column=5, text='b'),
                    ])],
                [TextBlock(lineno=3, column=5, body=[
                    PlainText(lineno=3, column=5, text='c'),
                   ])],
                ]),
            ],
            [
            List(lineno=4, column=3, bullets='*', items=[
                [TextBlock(lineno=4, column=5, body=[
                    PlainText(lineno=4, column=5, text='x'),
                    ])],
                [TextBlock(lineno=5, column=5, body=[
                    PlainText(lineno=5, column=5, text='y'),
                    ])],
                [TextBlock(lineno=6, column=5, body=[
                    PlainText(lineno=6, column=5, text='z'),
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
                    PlainText(lineno=2, column=7, text='a'),
                    ])],
                [TextBlock(lineno=3, column=7, body=[
                    PlainText(lineno=3, column=7, text='b'),
                    ])],
                [TextBlock(lineno=4, column=7, body=[
                    PlainText(lineno=4, column=7, text='c'),
                   ])],
            ],
            [
                [TextBlock(lineno=5, column=7, body=[
                    PlainText(lineno=5, column=7, text='x'),
                    ])],
                [TextBlock(lineno=6, column=7, body=[
                    PlainText(lineno=6, column=7, text='y'),
                    ])],
                [TextBlock(lineno=7, column=7, body=[
                    PlainText(lineno=7, column=7, text='z'),
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
                    PlainText(lineno=5, column=7, text='a'),
                    ])],
                [TextBlock(lineno=6, column=7, body=[
                    PlainText(lineno=6, column=7, text='z'),
                   ])],
            ],
            ]),
        ]),
    # text, simple comment, text
    ('hello\n'
     '# such comment, much wow\n'
     'world'): Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
                  PlainText(lineno=1, column=1, text='hello\n'),
                  ]),
        Comment(lineno=2, column=1, text='such comment, much wow'),
        TextBlock(lineno=3, column=1, body=[
                  PlainText(lineno=3, column=1, text='world'),
                  ]),
        ]),
    # text, merged comment, text
    ('hello\n'
     '# such comment\n'
     '# much wow\n'
     'world'): Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
                  PlainText(lineno=1, column=1, text='hello\n'),
                  ]),
        Comment(lineno=2, column=1, text='such comment\nmuch wow'),
        TextBlock(lineno=4, column=1, body=[
                  PlainText(lineno=4, column=1, text='world'),
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
                  PlainText(lineno=1, column=1, text='hello\n'),
                  ]),
        Comment(lineno=2, column=1, text='\nsuch comment\nmuch wow\n'),
        TextBlock(lineno=6, column=1, body=[
                  PlainText(lineno=6, column=1, text='world'),
                  ]),
        ]),
    # text, code block, text
    ('hello\n'
     '```json\n'
     '{"such": "code",\n'
     ' "much": ["wow"]}\n'
     '```\n'
     'world'): Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
                  PlainText(lineno=1, column=1, text='hello\n'),
                  ]),
        CodeBlock(lineno=2, column=1, lang='json',
                  text='{"such": "code",\n "much": ["wow"]}\n'),
        TextBlock(lineno=6, column=1, body=[
                  PlainText(lineno=6, column=1, text='world'),
                  ]),
        ]),
    # text, equation, text
    ('hello\n'
     '$$$\n'
     '\kappa =\n'
     'e^{i\pi}\n'
     '$$$\n'
     'world'): Document(lineno=1, column=1, body=[
        TextBlock(lineno=1, column=1, body=[
                  PlainText(lineno=1, column=1, text='hello\n'),
                  ]),
        Equation(lineno=2, column=1,
                  text='\n\kappa =\ne^{i\pi}\n'),
        TextBlock(lineno=6, column=1, body=[
                  PlainText(lineno=6, column=1, text='world'),
                  ]),
        ]),
    # figure
    ('figure:: my file.png\n'
     '  Captions suck'): Document(lineno=1, column=1, body=[
        Figure(lineno=1, column=1, align='center', scale=1.0,
               path='my file.png', caption=[
                TextBlock(lineno=2, column=3, body=[
                    PlainText(lineno=2, column=3, text='Captions suck'),
                    ]),
            ]),
        ]),
    # figure with meta data
    ('figure:: my file.png\n'
     '  align = left\n'
     '  scale = 0.5\n'
     '\n'
     '  Captions suck'): Document(lineno=1, column=1, body=[
        Figure(lineno=1, column=1, align='left', scale=0.5,
               path='my file.png', caption=[
                TextBlock(lineno=2, column=3, body=[
                    PlainText(lineno=2, column=3, text='Captions suck'),
                    ]),
            ]),
        ]),
}


@pytest.mark.parametrize('doc, exp', PARSE_CASES.items())
def test_parse(doc, exp):
    obs = PARSER.parse(doc, debug_level=0)
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
