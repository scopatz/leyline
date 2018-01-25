"""Leyline AST nodes and tools."""
import re
import pprint
import textwrap

RE_NEWLINE_INDENT = re.compile('\n+[ \t]*')


def indent(s, ind):
    return s.replace('\n', '\n' + ind)


class Node:

    attrs = ()
    lineno = 0
    column = 0
    extra = None

    def __init__(self, *, lineno=0, column=0, **kwargs):
        self.lineno = lineno
        self.column = column
        for attr, default in self.attrs:
            value = kwargs.pop(attr, NotImplemented)
            if value is NotImplemented:
                value = default() if callable(default) else default
            setattr(self, attr, value)
        if kwargs:
            self.extra = kwargs

    def __str__(self):
        return PrettyFormatter(self).visit()

    def __repr__(self):
        return RE_NEWLINE_INDENT.sub('', str(self))

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.lineno != other.lineno:
            return False
        if self.column != other.column:
            return False
        for attr, _ in self.attrs:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True


class Document(Node):
    """Top-level document that contains a list of children"""

    attrs = (('body', list),)


class PlainText(Node):
    """Represents unformatted text."""

    attrs = (('text', ''),)


class TextBlock(Node):
    """Represents formatted text."""

    attrs = (('body', list),)


class Comment(Node):
    """Represents a comment in the text"""

    attrs = (('text', ''),)


class CodeBlock(Node):
    """Represents a large code that should be displayed
    as a separate listing.
    """

    attrs = (('lang', ''),
             ('text', ''))


class InlineCode(Node):
    """Represents a code snippet that should be rendered within the text."""

    attrs = (('lang', ''),
             ('text', ''))


class Equation(Node):
    """Represents mathematics that should be diplayed in its own block."""

    attrs = (('text', ''),)


class InlineMath(Node):
    """Represents mathematics that should be rendered within the text."""

    attrs = (('text', ''),)


class CorporealMacro(Node):
    """A macro that has a body."""

    attrs = (('name', ''),
             ('args', ''),
             ('body', list))


class IncorporealMacro(Node):
    """A macro without a body, which is eval'd in the current context."""

    attrs = (('text', ''),)


class Bold(Node):
    """Renders text with bold formatting."""

    attrs = (('body', list),)


class Italics(Node):
    """Renders text with italic formatting."""

    attrs = (('body', list),)


class Strikethrough(Node):
    """Renders text with strikethrough formatting."""

    attrs = (('body', list),)


class Subscript(Node):
    """Renders text as a subscript."""

    attrs = (('body', list),)


class Superscript(Node):
    """Renders text as a superscript."""

    attrs = (('body', list),)


class Underline(Node):
    """Renders text with underline formatting."""

    attrs = (('body', list),)


class RenderFor(Node):
    """Include the body only if rendering one of the specified
    targets. Skip this body otherwise.
    """

    attrs = (('targets', set),
             ('body', list))


class With(Node):
    """Exec the block as a Python code into a context."""

    attrs = (('ctx', ''),
             ('text', ''))


class List(Node):
    """Represents a list of items."""

    attrs = (('bullets', '*'),
             ('items', list))


class Table(Node):
    """Represents a table to render"""

    attrs = (('header_rows', 1),
             ('header_cols', 0),
             ('widths', 'auto'),
             ('rows', list))


class Figure(Node):
    """Represents a figure to display."""

    attrs = (('path', ''),
             ('align', 'center'),
             ('scale', 1.0),
             ('caption', list))

#
# Tools for trees of nodes.
#


def _lowername(cls):
    return cls.__name__.lower()


class Visitor(object):
    """Super-class for all classes that should walk over a tree of nodes.
    This implements the visit() method.
    """
    # which render target this class renders. None means all targets
    renders = None

    def __init__(self, tree=None, lang='python'):
        self.tree = tree
        self.lang = lang

    def visit(self, node=None):
        """Walks over a node.  If no node is provided, the tree is used."""
        if node is None:
            node = self.tree
        if node is None:
            raise RuntimeError('no node or tree given!')
        if not isinstance(node, Node):
            raise RuntimeError('{0!r} is not a leyline node'.format(node))
        for clsname in map(_lowername, type.mro(node.__class__)):
            meth = getattr(self, 'visit_' + clsname, None)
            if callable(meth):
                rtn = meth(node)
                break
        else:
            msg = 'could not find valid visitor method for {0} on {1}'
            nodename = node.__class__.__name__
            selfname = self.__class__.__name__
            raise AttributeError(msg.format(nodename, selfname))
        return rtn


class PrettyFormatter(Visitor):
    """Formats a tree of nodes into a pretty string"""

    def __init__(self, tree=None, indent=' '):
        super().__init__(tree=tree)
        self.level = 0
        self.indent = indent

    def visit_node(self, node):
        s = node.__class__.__name__ + '('
        if len(node.attrs) == 0:
            return s + ')'
        s += '\n'
        self.level += 1
        t = []
        for aname, _ in node.attrs:
            a = getattr(node, aname)
            t.append(self.visit(a) if isinstance(a, Node) else pprint.pformat(a))
        t = ['{0}={1}'.format(n, x) for (n, _), x in zip(node.attrs, t)]
        t.append('lineno={0}'.format(node.lineno))
        t.append('column={0}'.format(node.column))
        if node.extra:
            t.append('**' + repr(node.extra))
        s += indent(',\n'.join(t), self.indent)
        self.level -= 1
        s += '\n)'
        return s

    def visit_document(self, node):
        s = 'Document(lineno={0}, column={1}, body=[\n'.format(node.lineno, node.column)
        self.level += 1
        t = ',\n'.join(map(self.visit, node.body))
        s += self.indent + indent(t, self.indent)
        self.level -= 1
        s += '\n])'
        return s

    def visit_list(self, node):
        s = 'List(lineno={0}, column={1},\n'.format(node.lineno, node.column)
        s += self.indent + 'bullets=' + repr(node.bullets) + ',\n'
        s += self.indent + 'items=[\n'
        self.level += 1
        for item in node.items:
            self.level += 1
            s += self.indent*2 + '[\n'
            t = ',\n'.join(map(self.visit, item))
            s += self.indent*3 + indent(t, self.indent*3)
            s += '\n' + self.indent*2 + '],\n'
            self.level -= 1
        self.level -= 1
        s += self.indent + ']\n)'
        return s

    def _textual_node(self, node):
        s = node.__class__.__name__
        s += '(lineno={0}, column={1}, '.format(node.lineno, node.column)
        s += 'text=' + pprint.pformat(node.text, indent=len(self.indent)).lstrip()
        if '\n' in s:
            s += '\n'
        s += ')'
        return s

    visit_plaintext = _textual_node
    visit_comment = _textual_node
    visit_equation = _textual_node
    visit_inlinemath = _textual_node
    visit_incorporealmacro = _textual_node

    def _code_node(self, node):
        s = node.__class__.__name__
        s += '(lineno={0}, column={1}, '.format(node.lineno, node.column)
        s += 'lang=' + repr(node.lang) + ', '
        s += 'text=' + pprint.pformat(node.text, indent=len(self.indent)).lstrip()
        if '\n' in s:
            s += '\n'
        s += ')'
        return s

    visit_codeblock = _code_node
    visit_inlinecode = _code_node

    def _bodied_text(self, node):
        s = node.__class__.__name__
        s += '(lineno={0}, column={1}, body=[\n'.format(node.lineno, node.column)
        self.level += 1
        t = ',\n'.join(map(self.visit, node.body))
        s += self.indent + indent(t, self.indent)
        self.level -= 1
        s += '\n])'
        return s

    visit_textblock = _bodied_text
    visit_bold = _bodied_text
    visit_italics = _bodied_text
    visit_strikethrough = _bodied_text
    visit_subscript = _bodied_text
    visit_supercript = _bodied_text
    visit_underline = _bodied_text

    def visit_table(self, node):
        s = 'Table(lineno={0}, column={1},\n'.format(node.lineno, node.column)
        s += self.indent + 'widths=' + repr(node.widths) + ',\n'
        s += self.indent + 'header_cols=' + repr(node.header_cols) + ',\n'
        s += self.indent + 'header_rows=' + repr(node.header_rows) + ',\n'
        s += self.indent + 'rows=[\n'
        self.level += 1
        for row in node.rows:
            self.level += 1
            s += self.indent*2 + '[\n'
            for element in row:
                s += self.indent*3 + '[\n'
                t = ',\n'.join(map(self.visit, element))
                s += self.indent*4 + indent(t, self.indent*4)
                s += '\n' + self.indent*3 + '],\n'
            s += '\n' + self.indent*2 + '],\n'
            self.level -= 1
        self.level -= 1
        s += self.indent + ']\n)'
        return s

    def visit_corporealmacro(self, node):
        s = 'CorporealMacro(lineno={0}, column={1},\n'.format(node.lineno, node.column)
        s += self.indent + 'name=' + repr(node.name) + ',\n'
        s += self.indent + 'args=' + repr(node.args) + ',\n'
        s += self.indent + 'body=[\n'
        self.level += 1
        t = ',\n'.join(map(self.visit, node.body))
        s += self.indent*2 + indent(t, self.indent*2)
        self.level -= 1
        s += '\n])'
        return s

    def visit_with(self, node):
        s = 'With(lineno={0}, column={1}, '.format(node.lineno, node.column)
        s += 'ctx=' + repr(node.lang) + ', '
        s += 'text=' + pprint.pformat(node.text, indent=len(self.indent)).lstrip()
        if '\n' in s:
            s += '\n'
        s += ')'
        return s

    def visit_renderfor(self, node):
        s = 'RenderFor(lineno={0}, column={1},\n'.format(node.lineno, node.column)
        s += self.indent + 'targets=' + repr(node.targets) + ',\n'
        s += self.indent + 'body=[\n'
        self.level += 1
        t = ',\n'.join(map(self.visit, node.body))
        s += self.indent*2 + indent(t, self.indent*2)
        self.level -= 1
        s += '\n])'
        return s

    def visit_figure(self, node):
        s = 'Figure(lineno={0}, column={1},\n'.format(node.lineno, node.column)
        s += self.indent + 'path=' + repr(node.path) + ',\n'
        s += self.indent + 'align=' + repr(node.align) + ',\n'
        s += self.indent + 'scale=' + repr(node.scale) + ',\n'
        s += self.indent + 'caption=[\n'
        self.level += 1
        t = ',\n'.join(map(self.visit, node.caption))
        s += self.indent*2 + indent(t, self.indent*2)
        self.level -= 1
        s += '\n])'
        return s


def PrettyTable(Visitor):

    def visit_()