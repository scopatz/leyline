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
        self.current_event.append(node)

    def _bodied_visit(self, node):
        """Visits each subnode in the body of the given node."""
        for n in node.body:
            self.visit(n)

    visit_document = _bodied_visit
    visit_textblock = _bodied_visit
    visit_corporealmacro = _bodied_visit


class Event:
    """A generic event base class that contains ASTs to render for
    a given duration begining at a start time.
    """

    type = 'event'
    attrs = ()

    def __init__(self, *, body=None, start=None, duration=None, **kwargs):
        self.body = [] if body is None else body
        self.start = start
        self.duration = duration

    def render_latex(self, visitor):
        return '\\phantom{}'

    def render_notes(self, visitor):
        return '\\phantom{}'

    def render(self, target, visitor):
        if not hasattr(visitor, 'events'):
            return ''
        visitor.current_event = self
        return ''

    def append(self, node):
        self.body.append(node)

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
    """A transition event representing moving to a new slide.
    Each slide consists of a number of sub-slides.
    """

    type = 'slide'
    attrs = ('title',)

    def __init__(self, title='', body=None, start=None, duration=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.body = [[]] if body is None else body
        self.start = [None] if start is None else start
        self.duration = [None] if duration is None else duration
        self.idx = 0  # which subslide index new nodes should be applied to

    def append(self, node):
        while len(self.body) < self.idx + 1:
            self.body.append([])
            self.start.append(None)
            self.duration.append(None)
        self.body[self.idx].append(node)

    def render_slides(self, visitor):
        title = self.title or ''
        return '\\end{frame}\n\\begin{frame}\n\\frametitle{' + title + '}\n'


class Subslide(Event):
    """Event that modifies the subslide index on the current slide."""

    type = 'subslide'
    attrs = ('idx',)

    def __init__(self, idx=None, **kwargs):
        self.idx = idx
        self.body = self.start = self.duration = None

    def render(self, target, visitor):
        # this event should not add itself to the visitor
        if not hasattr(visitor, 'events'):
            return ''
        for event in reversed(visitor.events):
            if isinstance(event, Slide):
                break
        else:
            raise ValueError('subslide before slide')
        idx = event.idx + 1 if self.idx is None else self.idx
        event.idx = idx
        return ''

    def append(self, node):
        pass


class Sleep(Event):
    """An event representing pausing for the provided number of seconds."""

    type = 'sleep'

    def __init__(self, duration=0.0, **kwargs):
        super().__init__(duration=duration, **kwargs)


EVENTS_CTX = {_.type: _ for _ in globals().values() if isinstance(_, type) and issubclass(_, Event)}
