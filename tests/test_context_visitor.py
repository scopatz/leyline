"""Tests the leyline context visitor"""
from leyline import ContextVisitor, parse

def test_context_visitor():
    s = (
        'with::\n'
        '  s = 42\n\n'
        'with meta::\n'
        '  author = "gg all me"\n\n'
        '{{s}}'
        )
    tree = parse(s)
    visitor = ContextVisitor()
    assert len(tree.body) ==3
    # visit first with and check that context has "s"
    visitor.visit(tree.body[0])
    assert 's' in visitor.contexts['ctx']
    assert visitor.contexts['ctx']['s'] == 42
    # visit second with and check that context has "author"
    visitor.visit(tree.body[1])
    assert 'meta' in visitor.contexts
    assert 'author' in visitor.contexts['meta']
    assert visitor.contexts['meta']['author'] == 'gg all me'
    # visit incorporeal macro and check that it returns s
    rtn = visitor.visit(tree.body[2].body[0])
    assert rtn == 42
