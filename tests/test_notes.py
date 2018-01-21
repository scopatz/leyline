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
# text and table
"""hello world

table::
  header_cols = 1

  * - a
    - b
    - c
  * - l
    - m
    - n
  * - x
    - y
    - z
""": r"""hello world

\begin{center}
\begin{tabular}[hctb]{|l|cc|}
\hline
\textbf{a} & \textbf{b} & \textbf{c} \\
\hline
\textbf{l} & m & n \\
\textbf{x} & y & z \\
\hline
\end{tabular}
\end{center}
"""
}


@pytest.mark.parametrize('doc, exp', NOTES_CASES.items())
def test_parse(doc, exp):
    tree = parse(doc)
    visitor = Notes(tree=tree)
    obs = visitor.visit()
    exp = HEADER + exp + FOOTER
    assert exp == obs#, difftex(exp, obs)
