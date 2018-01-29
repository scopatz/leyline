"""Tools for rendering leyline ASTs as video"""
import tempfile
import subprocess

from leyline.latex import Latex


HEADER = r"""
\documentclass[aspectratio=169]{beamer}
\usepackage{color}
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
\DeclareMathAlphabet{\mathpzc}{OT1}{pzc}{m}{it}

\definecolor{listinggray}{gray}{0.9}
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

\usetheme{Warsaw}

\setbeamercolor{normal text}{fg=white,bg=black!90}
\setbeamercolor{structure}{fg=white}

\setbeamercolor{alerted text}{fg=red!85!black}

\setbeamercolor{item projected}{use=item,fg=black,bg=item.fg!35}

\setbeamercolor*{palette primary}{use=structure,fg=structure.fg}
\setbeamercolor*{palette secondary}{use=structure,fg=structure.fg!95!black}
\setbeamercolor*{palette tertiary}{use=structure,fg=structure.fg!90!black}
\setbeamercolor*{palette quaternary}{use=structure,fg=structure.fg!95!black,bg=black!80}

\setbeamercolor*{framesubtitle}{fg=white}

\setbeamercolor*{block title}{parent=structure,bg=black!60}
\setbeamercolor*{block body}{fg=black,bg=black!10}
\setbeamercolor*{block title alerted}{parent=alerted text,bg=black!15}
\setbeamercolor*{block title example}{parent=example text,bg=black!15}

\begin{document}
\begin{frame}
"""

FOOTER = r"""
\end{frame}
\end{document}
"""


class Frame(Latex):
    """Renders a video frame via the LaTeX Beamer package."""

    renders = 'video'

    def render(self, *, tree=None, assets=None, assets_dir='.', title=None, **kwargs):
        """Renders a single 1080p frame of video as a jpg via LaTeX. Returns the filename."""
        self.title = title
        s = self.visit(tree)
        asset_key = ('frame', s)
        if asset_key in assets:
            filename = assets[asset_key]
            print('found \x1b[1m' + filename + '\x1b[0m in cache')
            assets[assets_key] = filename  # update src hash
            return filename
        h = self.hash(asset_key)
        basename = h + '.jpg'
        filename = os.path.join(assets_dir, basename)
        with tempfile.TemporaryDirectory(prefix='frame-' + h) as d:
            texname = os.path.join(d, h + '.tex')
            with open(texname, 'w') as f:
                f.write(s)
            out = subprocess.check_call(['pdflatex', texname])
            pdfname = os.path.join(d, h + '.pdf')
            out = subprocess.check_call(['convert', '-density', '1080', '-antialias',
                                         '-quality', '100', pdfname + '[0]', filename])
        return filename


    def _make_title(self):
        title = getattr(self, title, None)
        if title is None:
            return ''
        return '\\frametitle{' + title + '}\n'

    def visit_document(self, node):
        body = super().visit_document(node)
        s = HEADER + self._make_title() + body + FOOTER
        return s