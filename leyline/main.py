"""Command line interface for leyline"""
import importlib
from argparse import ArgumentParser

from leyline.parser import parse


TARGETS = {
    'notes': ('leyline.notes', 'Notes'),
    }
TARGET_VISITORS = {}


def render_target(tree, target, ns):
    modname, clsname
    mod = importlib.import_module(modname)
    cls = getattr(mod, clsname)
    visitor = cls()
    visitor.render(tree=tree, **ns.__dict__)


def make_argparser():
    """makes an argparser instance for leyline"""
    p = ArgumentParser('leyline', description='Leyline Rendering Tool')
    p.add_argument('targets', nargs='+', help='targets to render the file into: '
                   + ', '.join(sorted(TARGETS.keys())),
                   choices=TARGETS)
    p.add_argument('filename', help='file to render')
    return p


def main(args=None):
    """Main entry point for leyline"""
    p = make_argparser()
    ns = p.parse_args(args=args)
    with open(ns.filename, 'r') as f:
        s = f.read()
    tree = parse(s)
    for target in ns.targets:
        render_target(tree, target, ns)


if __name__ == '__main__':
    main()