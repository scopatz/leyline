"""AST visitor tools for evelauating contexts as the tree is trasversed."""
from collections import defaultdict

from leyline.ast import Visitor


class ContextVisitor(Visitor):
    """An AST Visitor that executes with-blocks as Python
    code as a named context. Incorporeal macros are then
    evaluated in the default context.

    If the object evaluated by incorporeal macro has a ``render_<target>()``
    method, this visitor will return the result of calling that method.  For
    example::

        class Upper:

            def render_notes(self, visitor=None):
                return str(self).upper()

    If instead, the object has a general purpose ``render()`` method,
    which accepts as its first argument the current render target,
    this method will be called. For example::

        class Lower:

            def render(self, target=None, vistor=None):
                return str(self).upper()

    If no render method is found on the object, the object itself is
    returned.
    """

    def __init__(self, *, default='ctx', contexts=(), **kwargs):
        """
        Parameters
        ----------
        default : str, optional
            Name of the default context ("ctx").
        contexts : dict of strs to dicts, optional
            All additional kwargs are treated as the initial
            contexts to start the visitor with.
        kwargs : optional
            All additional kwargs are passed to superclass.
        """
        super().__init__(**kwargs)
        self.default = default
        self.contexts = defaultdict(dict, contexts)

    def visit_with(self, node):
        name = node.ctx if node.ctx else self.default
        ctx = self.contexts[name]
        exec(node.text, ctx)

    def visit_incorporealmacro(self, node):
        obj = eval(node.text, self.contexts[self.default])
        # see if there is a method specifically for this renderer
        if self.renders is not None:
            meth = getattr(obj, 'render_' + self.renders, None)
            if meth is not None:
                return meth(self)
        # see if there is a general purpose renderer
        meth = getattr(obj, 'render', None)
        if meth is not None:
            return meth(target=self.renders, visitor=self)
        # finally just return the object
        return obj
