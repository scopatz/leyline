"""Leyline AST nodes and tools."""
import pprint
import textwrap


class Node:

    attrs = ()
    lineno = 0
    column = 0

    def __init__(self, *, lineno=0, column=0, **kwargs):
        self.lineno = lineno
        self.column = column
        for attr, default in self.attrs:
            value = kwargs.get(attr, NotImplemented)
            if value is NotImplemented:
                value = default() if callable(default) else default
            setattr(self, attr, value)


class Document(Node):
    """Top-level document that contains a list of children"""

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
             ('args', list),
             ('body', list))


class IncorporealMacro(Node):
    """A macro without a body, which is eval'd in the current context."""

    attrs = (('text', ''),)


class Strikethrough(Node):
    """Renders text with strikethrough formatting."""

    attrs = (('body', list),)


class Bold(Node):
    """Renders text with bold formatting."""

    attrs = (('body', list),)


class Italics(Node):
    """Renders text with italic formatting."""

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


class Table(Node):
    """Represents a table to render"""

    attrs = (('header_rows', 1),
             ('header_cols', 0),
             ('widths', 'auto'),
             ('rows', list))


#
# Tools for trees of nodes.
#


def _lowername(cls):
    return cls.__name__.lower()


class Visitor(object):
    """Super-class for all classes that should walk over a tree of nodes.
    This implements the visit() method.
    """

    def __init__(self, tree=None):
        self.tree = tree

    def visit(self, node=None):
        """Walks over a node.  If no node is provided, the tree is used."""
        if node is None:
            node = self.tree
        if node is None:
            raise RuntimeError('no node or tree given!')
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
        if node.lineno:
            t.append('lineno={0}'.format(node.lineno))
        if node.column:
            t.append('column={0}'.format(node.column))
        s += textwrap.indent(',\n'.join(t), self.indent)
        self.level -= 1
        s += '\n)'
        return s
