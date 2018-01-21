"""A leyline visitor for rendering lecture notes (via LaTeX)."""
from leyline.context_visitor import ContextVisitor

HEADER = r"""
\documentclass[12pt]{article}
\usepackage{color}
\usepackage{graphicx}
\usepackage{booktabs} % nice rules for tables
\usepackage{microtype} % if using PDF
\usepackage{xspace}
\usepackage{listings}
\usepackage{textcomp}
\usepackage[normalem]{ulem}
\usepackage{amssymb}
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

\newcommand{\superscript}[1]{\ensuremath{^{\textrm{#1}}}}
\newcommand{\subscript}[1]{\ensuremath{_{\textrm{#1}}}}

\begin{document}
"""

FOOTER = r"""\end{document}"""


class Notes(ContextVisitor):
    """A leyline visitor for rendering lecture notes (via LaTeX)."""

    renders = 'notes'

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
        self._enumerate_level = 0
        body = ''
        for n in node.body:
            body += self.visit(n)
        s = HEADER + self._make_title() + body + FOOTER
        return s

    def visit_with(self, node):
        super().visit_with(node)
        return ''

    def visit_plaintext(self, node):
        return node.text

    def visit_textblock(self, node):
        body = ''
        for n in node.body:
            body += self.visit(n)
        return body

    def visit_comment(self, node):
        return ''

    def visit_codeblock(self, node):
        # get the language for the code block
        lang = node.lang
        if not lang:
            lang = self.lang
        s = '\\lstset{language=' + lang + '}\n'
        s += '\\begin{lstlisting}\n'
        s += node.text
        s += '\\end{lstlisting}\n'
        return s

    def visit_inlinecode(self, node):
        lang = node.lang
        if not lang:
            lang = self.lang
        s = '\\lstset{language=' + lang + '}'
        s += '\\lstinline[columns=fixed]{' + node.text + '}'
        return s

    def visit_equation(self, node):
        s = '\\begin{equation}\n'
        s += node.text
        s += '\\end{equation}\n'
        return s

    def visit_inlinemath(self, node):
        return '$' + node.text + '$'

    def visit_bold(self, node):
        body = '\\textbf{'
        for n in node.body:
            body += self.visit(n)
        body += '}'
        return body

    def visit_italics(self, node):
        body = '\\textit{'
        for n in node.body:
            body += self.visit(n)
        body += '}'
        return body

    def visit_strikethrough(self, node):
        body = '\\sout{'
        for n in node.body:
            body += self.visit(n)
        body += '}'
        return body

    def visit_underline(self, node):
        body = '\\underline{'
        for n in node.body:
            body += self.visit(n)
        body += '}'
        return body

    def visit_renderfor(self, node):
        if self.renders not in node.targets:
            return ''
        body = ''
        for n in node.body:
            body += self.visit(n)
        return body

    def _itemize_list(self, node):
        s = '\\begin{itemize}\n'
        for item in node.items:
            s += '  \\item ' + self.visit(item) + '\n'
        s += '\\end{itemize}\n'
        return s

    def _enumerate_list(self, node):
        self._enumerate_level += 1
        s = '\\begin{enumerate}\n'
        for item in node.items:
            s += '  \\item ' + self.visit(item) + '\n'
        s += '\\end{enumerate}\n'
        self._enumerate_level -= 1
        return s

    _enum_counter = {
        1: 'enumi',
        2: 'enumii',
        3: 'enumiii',
        4: 'enumiv',
        }

    def _enumerate_custom_num_list(self, node):
        self._enumerate_level += 1
        counter = self._enum_counter.get(self._enumerate_level, 'enumi')
        s = '\\begin{enumerate}\n'
        for num, item in zip(node.bullets, node.items):
            s += '  \\setcounter{' + counter + '}{' + str(num) + '}\n'
            s += '  \\item ' + self.visit(item) + '\n'
        s += '\\end{enumerate}\n'
        self._enumerate_level -= 1
        return s

    def visit_list(self, node):
        if isinstance(node.bullets, str):
            return self._itemize_list(node)
        elif isinstance(node.bullets, int):
            return self._enumerate_list(node)
        elif isinstance(node.bullets[0], str):
            return self._itemize_list(node)
        elif isinstance(node.bullets[0], int):
            return self._enumerate_custom_num_list(node)
        else:
            msg = 'bullets not understood: ' + str(node)
            raise ValueError(msg)

    def _compute_column_widths(self, node):
        if node.widths != 'auto':
            raise ValueError('Only "auto" widths are currently supported.')
        normcols = len(node.rows[0]) - node.header_cols
        w = '|'
        if node.header_cols > 0:
            w += ('l' * node.header_cols) + '|'
        w += 'c' * (len(node.rows[0]) - node.header_cols)
        w += '|'
        return w

    def visit_table(self, node):
        widths = self._compute_column_widths(node)
        s = '\\begin{center}\n'
        s += '\\begin{tabular}[hctb]{' + widths + '}\n'
        s += '\\hline\n'
        # do header rows
        if node.header_rows > 0:
            for row in node.rows[:node.header_rows]:
                cells = []
                for cell in row:
                    c = ''.join(map(self.visit, cell)).strip()
                    cells.append('\\textbf{' + c + '}')
                s += ' & '.join(cells)
                s += r' \\' + '\n'
            s += '\\hline\n'
        # do data rows
        for row in node.rows[node.header_rows:]:
            cells = []
            for i, cell in enumerate(row):
                c = ''.join(map(self.visit, cell)).strip()
                if i < node.header_cols:
                    cells.append('\\textbf{' + c + '}')
                else:
                    cells.append(c)
            s += ' & '.join(cells)
            s += r' \\' + '\n'
        s += '\\hline\n'
        s += '\\end{tabular}\n'
        s += '\\end{center}\n'
        return s
