from pprint import pformat
from collections.abc import Sequence

import pytest
from ply.lex import LexToken

from leyline.lexer import Lexer

LEXER_ARGS = {'lextab': 'lexer_test_table', 'debug': 0}
TOKTEMPLATE = 'LexToken({0!r}, {1!r}, {2}, {3}, {4})'


def tokstr(x):
    if isinstance(x, LexToken):
        x = (x.type, x.value, x.lineno, x.column, x.lexpos)
    s = TOKTEMPLATE.format(*x)
    return s

def ensure_tuple(x):
    if isinstance(x, LexToken):
        x = (x.type, x.value, x.lineno, x.column, x.lexpos)
        # line numbers can no longer be solely determined from the lexer
        #x = (x.type, x.value, x.lexpos)
    elif isinstance(x, tuple):
        pass
    elif isinstance(x, Sequence):
        x = tuple(x)
    else:
        raise TypeError('{0} is not a sequence'.format(x))
    return x


def tokens_equal(x, y):
    """Tests whether two token are equal."""
    xtup = ensure_tuple(x)
    ytup = ensure_tuple(y)
    return xtup == ytup


def assert_token_equal(x, y):
    """Asserts that two tokens are equal."""
    if not tokens_equal(x, y):
        msg = 'The tokens differ: {x} != {y}'.format(x=tokstr(x), y=tokstr(y))
        pytest.fail(msg)
    return True


def assert_tokens_equal(x, y):
    """Asserts that two token sequences are equal."""
    if len(x) != len(y):
        msg = 'The tokens sequences have different lengths: {0!r} != {1!r}\n'
        msg += '# x\n{2}\n\n# y\n{3}'
        xstr = '[' + ',\n '.join(map(tokstr, x)) + ']'
        ystr = '[' + ',\n '.join(map(tokstr, y)) + ']'
        pytest.fail(msg.format(len(x), len(y), xstr, ystr))
    diffs = [(i, a, b) for i, (a, b) in enumerate(zip(x, y)) if not tokens_equal(a, b)]
    if len(diffs) > 0:
        msg = ['The token sequences differ: ']
        for i, a, b in diffs:
            msg += ['', 'Index ' + str(i), '- ' + tokstr(a), '+ ' + tokstr(b)]
        msg = '\n'.join(msg)
        pytest.fail(msg)
    return True


def check_token(inp, exp):
    l = Lexer()
    l.input(inp)
    obs = list(l)
    if len(obs) != 1:
        msg = 'The observed sequence does not have length-1: {0!r} != 1\n'
        msg += '# obs\n{1}'
        pytest.fail(msg.format(len(obs), pformat(obs)))
    return assert_token_equal(exp, obs[0])


def check_tokens(inp, exp):
    l = Lexer()
    l.input(inp)
    obs = list(l)
    return assert_tokens_equal(exp, obs)


TOKEN_CASES = {
    # code: [token type, str, line, col, lexpos]
    '**': ['DOUBLESTAR', '**', 1, 1, 0],
    '--': ['DOUBLEDASH', '--', 1, 1, 0],
    '~~': ['DOUBLETILDE', '~~', 1, 1, 0],
    '__': ['DOUBLEUNDER', '__', 1, 1, 0],
    '{{': ['DOUBLELBRACE', '{{', 1, 1, 0],
    '}}': ['DOUBLERBRACE', '}}', 1, 1, 0],
    '{%': ['LBRACEPERCENT', '{%', 1, 1, 0],
    '%}': ['PERCENTRBRACE', '%}', 1, 1, 0],
    '{%}': ['LBRACEPERCENTRBRACE', '{%}', 1, 1, 0],
    'rend x y::': ['REND', set(['x', 'y']), 1, 1, 0],
    'with::': ['WITH', '', 1, 1, 0],
    'table::': ['TABLE', 'table::', 1, 1, 0],
    'Please stay with me': ['PLAINTEXT', 'Please stay with me', 1, 1, 0],
    'dash-ing': ['PLAINTEXT', 'dash-ing', 1, 1, 0],
    '{braced}': ['PLAINTEXT', '{braced}', 1, 1, 0],
    'wakka jawaka': ['PLAINTEXT', 'wakka jawaka', 1, 1, 0],
    'wakka\njawaka': ['PLAINTEXT', 'wakka\njawaka', 1, 1, 0],
    '`x = 10`': ['INLINECODE', 'x = 10', 1, 1, 0],
    '```\nx=10\n```': ['CODEBLOCK', ('', 'x=10\n'), 1, 1, 0],
    '```python\nx=10\n```': ['CODEBLOCK', ('python', 'x=10\n'), 1, 1, 0],
    '# Just a comment ': ['COMMENT', 'Just a comment', 1, 1, 0],
    '###\nI have\na really long comment###': [
        'MULTILINECOMMENT', '\nI have\na really long comment', 1, 1, 0],
    '$e^{i\pi} = -1$': ['INLINEMATH', 'e^{i\pi} = -1', 1, 1, 0],
    '$$$\ne^{i\pi} = -1\n$$$': ['MULTILINEMATH', '\ne^{i\pi} = -1\n', 1, 1, 0],
    '$$$inline math $=$ inside$$$': ['MULTILINEMATH', 'inline math $=$ inside', 1, 1, 0],
}

@pytest.mark.parametrize('inp, exp', sorted(TOKEN_CASES.items()))
def test_token(inp, exp):
    assert check_token(inp, exp)


TOKENS_CASES = {
    # code: [token type, str, line, col, lexpos]
    'with::\n  x = 10\n  y = 42': [
        ['WITH', '', 1, 1, 0],
        ['INDENT', '  ', 2, 1, 6],
        ['PLAINTEXT', 'x = 10\n  y = 42', 2, 3, 9],
        ['DEDENT', '  ', 3, 1, 24],
        ],
    '**__Bold And\nUnderline!__**': [
        ['DOUBLESTAR', '**', 1, 1, 0],
        ['DOUBLEUNDER', '__', 1, 3, 2],
        ['PLAINTEXT', 'Bold And\nUnderline!', 1, 5, 4],
        ['DOUBLEUNDER', '__', 2, 11, 23],
        ['DOUBLESTAR', '**', 2, 13, 25],
        ],
    'text and \n```rst\ncode block\n```\nand more text': [
        ['PLAINTEXT', 'text and \n', 1, 1, 0],
        ['CODEBLOCK', ('rst', 'code block\n'), 2, 1, 10],
        ['PLAINTEXT', 'and more text', 5, 1, 32],
        ],
    'text $math$ text': [
        ['PLAINTEXT', 'text ', 1, 1, 0],
        ['INLINEMATH', 'math', 1, 6, 5],
        ['PLAINTEXT', ' text', 1, 12, 11],
        ],
    '\n* item 1\n- item 2': [
        ['PLAINTEXT', '\n', 1, 1, 0],
        ['LISTBULLET', '*', 2, 1, 1],
        ['PLAINTEXT', 'item 1\n', 2, 3, 3],
        ['LISTBULLET', '-', 3, 1, 10],
        ['PLAINTEXT', 'item 2', 3, 3, 12],
        ],
    'hello\n  1. yup\n  2. nope\n  3. maybe': [
        ['PLAINTEXT', 'hello', 1, 1, 0],
        ['INDENT', '  ', 2, 1, 5],
        ['LISTBULLET', 1, 2, 3, 8],
        ['PLAINTEXT', 'yup\n  ', 2, 6, 11],
        ['LISTBULLET', 2, 3, 3, 17],
        ['PLAINTEXT', 'nope\n  ', 3, 6, 20],
        ['LISTBULLET', 3, 4, 3, 27],
        ['PLAINTEXT', 'maybe', 4, 6, 30],
        ['DEDENT', '  ', 4, 1, 35],
        ],
    # test nested list
    '* - hello\n  - world': [
        ['LISTBULLET', '*', 1, 1, 0],
        ['INDENT', '  ', 1, 3, 2],
        ['LISTBULLET', '-', 1, 3, 2],
        ['PLAINTEXT', 'hello\n  ', 1, 5, 4],
        ['LISTBULLET', '-', 2, 3, 12],
        ['PLAINTEXT', 'world', 2, 5, 14],
        ['DEDENT', '  ', 2, 1, 19],
        ],
}

@pytest.mark.parametrize('inp, exp', sorted(TOKENS_CASES.items()))
def test_tokens(inp, exp):
    assert check_tokens(inp, exp)


