"""LaTeX notes tester"""
import difflib

import pytest

from leyline import parse
from leyline.notes import Notes, HEADER, FOOTER


def difftex(x, y, xname='expected', yname='observed'):
    s = x.splitlines(True)
    t = y.splitlines(True)
    d = ''.join(difflib.unified_diff(s, t, fromfile=xname, tofile=yname))
    return d

NOTES_CASES = {
# inline
"$x + 10$": "$x + 10$",
# simple formatting
"**so bold** and ~~italic~~": "\\textbf{so bold} and \\textit{italic}",
# metadata
"""with meta::
  author = 'gg all me'
  title = 'storytime'
""": r"""\title{storytime}
\author{gg all me}
\date{\today}
\maketitle
""",
}


@pytest.mark.parametrize('doc, exp', NOTES_CASES.items())
def test_parse(doc, exp):
    tree = parse(doc)
    visitor = Notes(tree=tree)
    obs = visitor.visit()
    exp = HEADER + exp + FOOTER
    assert exp == obs#, difftex(exp, obs)
