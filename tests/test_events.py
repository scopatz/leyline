"""Events testing"""
import pytest

from leyline import parse, EVENTS_CTX, EventsVisitor
from leyline.ast import PlainText
from leyline.events import Event, Slide


EVENTS_CASES = {
"""{{slide()}}Hello World{{slide()}}Next Slide
""": [Event(),
      Slide(body=[PlainText(lineno=1, column=12, text='Hello World')]),
      Slide(body=[PlainText(lineno=1, column=34, text='Next Slide\n')]),
      ],
}

@pytest.mark.parametrize('doc, exp', sorted(EVENTS_CASES.items()))
def test_events(doc, exp):
    tree = parse(doc)
    contexts = {'ctx': EVENTS_CTX}
    visitor = EventsVisitor(contexts=contexts)
    visitor.visit(tree)
    assert visitor.events == exp
