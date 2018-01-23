"""Events testing"""
import pytest

from leyline import parse, EVENTS_CTX, EventsVisitor
from leyline.ast import PlainText
from leyline.events import Event, Slide, Sleep


EVENTS_CASES = {
"Antici...{{sleep(42.0)}}...pation": [
    Event(body=[PlainText(lineno=1, column=1, text='Antici...')]),
    Sleep(duration=42.0, body=[PlainText(lineno=1, column=25, text='...pation')]),
    ],
"Hello World{{event(start=42.0)}}Next Slide": [
    Event(body=[PlainText(lineno=1, column=1, text='Hello World')]),
    Event(start=42.0, body=[PlainText(lineno=1, column=33, text='Next Slide')]),
    ],
"Hello World{{slide('A Title')}}Next Slide": [
    Event(body=[PlainText(lineno=1, column=1, text='Hello World')]),
    Slide(title='A Title', body=[PlainText(lineno=1, column=32, text='Next Slide')]),
    ],
"""{{slide()}}Hello World{{slide()}}Next Slide
""": [Event(),
      Slide(body=[PlainText(lineno=1, column=12, text='Hello World')]),
      Slide(body=[PlainText(lineno=1, column=34, text='Next Slide\n')]),
      ],
"""Hello World{{slide()}}Next Slide
""": [Event(body=[PlainText(lineno=1, column=1, text='Hello World')]),
      Slide(body=[PlainText(lineno=1, column=23, text='Next Slide\n')]),
      ],
}

@pytest.mark.parametrize('doc, exp', sorted(EVENTS_CASES.items()))
def test_events(doc, exp):
    tree = parse(doc)
    contexts = {'ctx': EVENTS_CTX}
    visitor = EventsVisitor(contexts=contexts)
    visitor.visit(tree)
    assert exp == visitor.events
