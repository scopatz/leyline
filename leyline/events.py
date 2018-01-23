"""Tools for handling events in the documents."""
from leyline.ast import indent
from leyline.context_visitor import ContextVisitor


class EventsVisitor(ContextVisitor):

    def __init__(self, *, initial_event=None, **kwargs):
        super().__init__(**kwargs)
        self.events = []
        if initial_event is None:
            initial_event = Event()
        self.events.append(initial_event)

    def __str__(self):
        s = 'Events:\n' + indent('\n'.join(map(str, self.events)), '  ')
        return s

    @property
    def current_event(self):
        return self.events[-1]

    @current_event.setter
    def current_event(self, val):
        self.events.append(val)

    def visit_node(self, node):
        """generic vistor just adds node to current event body."""
        self.current_event.body.append(node)

    def _bodied_visit(self, node):
        """Visits each subnode in the body of the given node."""
        for n in node.body:
            self.visit(n)

    visit_document = _bodied_visit
    visit_textblock = _bodied_visit
    visit_corporealmacro = _bodied_visit


class Event:

    type = 'event'
    attrs = ()

    def __init__(self, *, body=None, start=None, duration=None, **kwargs):
        self.body = [] if body is None else body
        self.start = start
        self.duration = duration

    def render(self, target, visitor):
        visitor.current_event = self
        return ''

    def __str__(self):
        s = self.__class__.__name__ + '(\n'
        s += ' start=' + repr(self.start) + ',\n'
        s += ' duration=' + repr(self.duration) + ',\n'
        for attr in self.attrs:
            s += ' {0}={1},\n'.format(attr, getattr(self, attr))
        s += ' body=[\n'
        s += '  ' + indent(',\n'.join(map(str, self.body)), '  ')
        s += ' ]\n)'
        return s

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if self.type != other.type:
            return False
        if self.start != other.start:
            return False
        if self.duration != other.duration:
            return False
        if self.body != other.body:
            return False
        for attr in self.attrs:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True


class Slide(Event):

    type = 'slide'
    attrs = ('title',)

    def __init__(self, *, title='', **kwargs):
        super().__init__(**kwargs)
        self.title = title


EVENTS_CTX = {_.type: _ for _ in globals().values() if isinstance(_, type) and issubclass(_, Event)}