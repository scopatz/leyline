"""A base leyline visitor for rendering LaTeX."""
import os

from leyline.context_visitor import ContextVisitor

class Latex(ContextVisitor):
    """A base leyline visitor for rendering LaTeX."""

    renders = 'latex'

    def visit_document(self, node):
        self._enumerate_level = 0
        s = ''
        for n in node.body:
            s += self.visit(n)
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
        s += node.text.strip() + '\n'
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

    def visit_subscript(self, node):
        body = '{\\ensuremath{_{\\textrm{'
        for n in node.body:
            body += self.visit(n)
        body += '}}}'
        return body

    def visit_superscript(self, node):
        body = '{\\ensuremath{^{\\textrm{'
        for n in node.body:
            body += self.visit(n)
        body += '}}}'
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
            s += '  \\item ' + ''.join(map(self.visit, item)).strip() + '\n'
        s += '\\end{itemize}\n'
        return s

    def _enumerate_list(self, node):
        self._enumerate_level += 1
        s = '\\begin{enumerate}\n'
        for item in node.items:
            s += '  \\item ' + ''.join(map(self.visit, item)).strip() + '\n'
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
            s += '  \\item ' + ''.join(map(self.visit, item)).strip() + '\n'
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

    def visit_figure(self, node):
        s = '\\begin{figure}[htbp]\n'
        s += '\\includegraphics[scale=' + str(node.scale) + ','
        s += node.align + ']{' + node.path + '}\n'
        if node.caption:
            s += '\\caption{'
            s += ''.join(map(self.visit, node.caption)).strip()
            s += '}\n'
        s += '\\end{figure}\n'
        return s
