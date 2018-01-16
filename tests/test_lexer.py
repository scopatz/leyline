from pprint import pformat
from collections.abc import Sequence

import pytest
from ply.lex import LexToken

from leyline.lexer import Lexer

LEXER_ARGS = {'lextab': 'lexer_test_table', 'debug': 0}

def ensure_tuple(x):
    if isinstance(x, LexToken):
        x = (x.type, x.value, x.lineno, x.lexpos)
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
        msg = 'The tokens differ: {0!r} != {1!r}'.format(x, y)
        pytest.fail(msg)
    return True


def assert_tokens_equal(x, y):
    """Asserts that two token sequences are equal."""
    if len(x) != len(y):
        msg = 'The tokens sequences have different lengths: {0!r} != {1!r}\n'
        msg += '# x\n{2}\n\n# y\n{3}'
        pytest.fail(msg.format(len(x), len(y), pformat(x), pformat(y)))
    diffs = [(a, b) for a, b in zip(x, y) if not tokens_equal(a, b)]
    if len(diffs) > 0:
        msg = ['The token sequences differ: ']
        for a, b in diffs:
            msg += ['', '- ' + repr(a), '+ ' + repr(b)]
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
    ':': ['COLON', ':', 1, 0],
    '**': ['DOUBLESTAR', '**', 1, 0],
    '--': ['DOUBLEDASH', '--', 1, 0],
    '~~': ['DOUBLETILDE', '~~', 1, 0],
    '__': ['DOUBLEUNDER', '__', 1, 0],
    '{{': ['DOUBLELBRACE', '{{', 1, 0],
    '}}': ['DOUBLERBRACE', '}}', 1, 0],
    '{%': ['LBRACEPERCENT', '{%', 1, 0],
    '%}': ['PERCENTRBRACE', '%}', 1, 0],
    '{%}': ['LBRACEPERCENTRBRACE', '{%}', 1, 0],
    'rend': ['REND', 'rend', 1, 0],
    'with': ['WITH', 'with', 1, 0],
    'table': ['TABLE', 'table', 1, 0],
    'wakka jawaka': ['TEXT', 'wakka jawaka', 1, 0],
    'wakka\njawaka': ['TEXT', 'wakka\njawaka', 1, 0],
    '`x = 10`': ['INLINECODE', 'x = 10', 1, 0],
    '```\nx=10\n```': ['CODEBLOCK', ('', 'x=10\n'), 1, 0],
    '```python\nx=10\n```': ['CODEBLOCK', ('python', 'x=10\n'), 1, 0],
    '# Just a comment ': ['COMMENT', 'Just a comment', 1, 0],
    '###\nI have\na really long comment###': ['MULTILINECOMMENT',
                                              '\nI have\na really long comment', 1, 0],
    '$e^{i\pi} = -1$': ['INLINEMATH', 'e^{i\pi} = -1', 1, 0],
    '$$$\ne^{i\pi} = -1\n$$$': ['MULTILINEMATH', '\ne^{i\pi} = -1\n', 1, 0],
    '$$$inline math $=$ inside$$$': ['MULTILINEMATH', 'inline math $=$ inside', 1, 0],
}

@pytest.mark.parametrize('inp, exp', TOKEN_CASES.items())
def test_token(inp, exp):
    assert check_token(inp, exp)
