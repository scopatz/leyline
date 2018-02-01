"""A leyline visitor for rendering lecture notes (via LaTeX)."""
import os

from leyline.latex import Latex


HEADER = r"""\documentclass[12pt]{article}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{booktabs} % nice rules for tables
\usepackage{microtype} % if using PDF
\usepackage{xspace}
\usepackage{listings}
\usepackage{textcomp}
\usepackage[normalem]{ulem}
\usepackage[export]{adjustbox}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{hyperref}
\DeclareMathAlphabet{\mathpzc}{OT1}{pzc}{m}{it}

\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=blue,
}

\definecolor{listinggray}{gray}{0.9}
\definecolor{lbcolor}{rgb}{0.9,0.9,0.9}
\lstset{
    language={Python},
    tabsize=4,
    rulecolor=\color{black},
    upquote=true,
    aboveskip={1.5\baselineskip},
    belowskip={1.5\baselineskip},
    columns=fixed,
    extendedchars=true,
    breaklines=true,
    prebreak=\raisebox{0ex}[0ex][0ex]{\ensuremath{\hookleftarrow}},
    frame=single,
    showtabs=false,
    showspaces=false,
    showstringspaces=false,
    basicstyle=\scriptsize\ttfamily\color{green!40!black},
    keywordstyle=\color[rgb]{0,0,1.0},
    commentstyle=\color[rgb]{0.133,0.545,0.133},
    stringstyle=\color[rgb]{0.627,0.126,0.941},
    numberstyle=\color[rgb]{0,1,0},
    identifierstyle=\color{black},
    captionpos=t,
}

\begin{document}
"""

FOOTER = r"""\end{document}"""


class Notes(Latex):
    """A leyline visitor for rendering lecture notes (via LaTeX)."""

    renders = 'notes'

    def render(self, *, tree=None, filename='', **kwargs):
        """Performs the actual render, putting the notes file on disk."""
        s = self.visit(tree)
        basename, _ = os.path.splitext(filename)
        outfile = basename + '.tex'
        with open(outfile, 'w') as f:
            f.write(s)
        return True

    def _make_title(self):
        if 'meta' not in self.contexts:
            return ''
        meta = self.contexts['meta']
        s = ''
        title = meta.get('title', None)
        if title is not None:
            s += '\\title{' + title + '}\n'
        author = meta.get('author', None)
        if author is not None:
            s += '\\author{' + author + '}\n'
        date = meta.get('date', None)
        if date is None and s:
            s += '\\date{\\today}\n'
        elif date is not None:
            s += '\\date{' + date + '}\n'
        if s:
            s += '\\maketitle\n'
        return s

    def visit_document(self, node):
        body = super().visit_document(node)
        s = HEADER + self._make_title() + body + FOOTER
        return s
