"""Pretty printer for ANSI."""
from collections.abc import Sequence

from leyline.ast import Node, indent
from leyline.context_visitor import ContextVisitor


class AnsiFormatter(ContextVisitor):
    """Creates a pretty version of tree, including ANSI escape sequnces"""

    def render(self, *, tree=None, **kwargs):
        s = self.visit(tree)
        print(s)
        return True

    def _bodied_visit(self, node):
        """Visits each subnode in the body of the given node."""
        s = ''.join(map(self.visit, node.body))
        return s

    visit_document = _bodied_visit
    visit_textblock = _bodied_visit
    visit_renderfor = _bodied_visit
    visit_corporealmacro = _bodied_visit

    def visit_with(self, node):
        super().visit_with(node)
        return ''

    def visit_bold(self, node):
        s = '\u001b[1m'
        s += self._bodied_visit(node)
        s += '\u001b[0m'
        return s

    def visit_italics(self, node):
        s = '\u001b[32;1m*\u001b[0m'
        s += self._bodied_visit(node)
        s += '\u001b[32;1m*\u001b[0m'
        return s

    def visit_strikethrough(self, node):
        s = '\u001b[32;1m*\u001b[0m'
        s += self._bodied_visit(node).replace(' ', '\u001b[32;1m*\u001b[0m')
        s += '\u001b[32;1m*\u001b[0m'
        return s

    def visit_subscript(self, node):
        s = '\u001b[32;1m{_\u001b[0m'
        s += self._bodied_visit(node)
        s += '\u001b[32;1m_}\u001b[0m'
        return s

    def visit_superscript(self, node):
        s = '\u001b[32;1m{^\u001b[0m'
        s += self._bodied_visit(node)
        s += '\u001b[32;1m^}\u001b[0m'
        return s

    def visit_underline(self, node):
        s = '\u001b[4m'
        s += self._bodied_visit(node)
        s += '\u001b[0m'
        return s

    def visit_inlinecode(self, node):
        s = '\u001b[7m' + node.text + '\u001b[0m'
        return s

    def visit_inlinemath(self, node):
        s = '\u001b[40;1m\u001b[37;1m' + node.text + '\u001b[0m'
        return s

    def visit_plaintext(self, node):
        return node.text

    def visit_url(self, node):
        return node.text

    def visit_comment(self, node):
        s = '"\u001b[8m'
        s += self._bodied_visit(node)
        s += '\u001b[0m'
        return s

    def visit_codeblock(self, node):
        s = '\n\u001b[7m'
        s += self._bodied_visit(node)
        s += '\u001b[0m\n'
        s = indent(s, '  ')
        return s

    def visit_equation(self, node):
        s = '\n\u001b[40;1m\u001b[37;1m'
        s += node.text
        s += '\u001b[0m\n'
        s = indent(s, '  ')
        return s

    def visit_list(self, node):
        s = ''
        for bullet, item in node:
            s += '\u001b[32;1m'
            s += bullet if isinstance(bullet, str) else str(bullet) + '.'
            s += '\u001b[0m '
            s += ''.join(map(self.visit, item)) + '\n'
        return s

    def visit_table(self, node):
        import prettytable
        ncols = len(node.rows[0])
        headers = [[]] * ncols
        for hrow in node.rows[:node.header_rows]:
            for header, hcol in zip(headers, hrow):
                header.extend(hcol)
        headers = [''.join(h) for h in
                   [map(self.visit, header) for header in headers]]
        if len(set(headers)) < ncols:
            headers = None
        pt = prettytable.PrettyTable(headers)
        for row in node.rows[node.header_rows:]:
            r = [''.join(c) for c in [map(self.visit, col) for col in row]]
            for i in range(node.header_cols):
                r[i] = '\u001b[1m' + r[i] + '\u001b[0m'
            pt.add_row(r)
        s = pt.get_string()
        return s

    def visit_figure(self, node):
        s = 'figure:: \u001b[1m' + node.path + '\u001b[0m\n  '
        s += indent(''.join(map(self.visit, node.caption)), '  ')
        return s

    def visit_incorporealmacro(self, node):
        # this should actually evaluate the node...
        n = super().visit_incorporealmacro(node)
        if isinstance(n, str):
            return n
        elif isinstance(n, Node):
            return self.visit(n)
        elif isinstance(n, Sequence):
            return ''.join(map(self.visit, n))
        return ''
