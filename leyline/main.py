"""Command line interface for leyline"""
import getpass
import importlib
from argparse import ArgumentParser

from leyline.parser import parse


TARGETS = {
    'notes': ('leyline.notes', 'Notes'),
    'polly': ('leyline.audio', 'SSML'),
    'dictate': ('leyline.audio', 'Dictation'),
    }
TARGET_VISITORS = {}


def render_target(tree, target, ns):
    modname, clsname = TARGETS[target]
    mod = importlib.import_module(modname)
    cls = getattr(mod, clsname)
    visitor = cls()
    visitor.render(tree=tree, **ns.__dict__)


def make_argparser():
    """makes an argparser instance for leyline"""
    p = ArgumentParser('leyline', description='Leyline Rendering Tool')
    p.add_argument('--pdb', '--debug', default=False, action='store_true',
                   dest='debug', help='Enter into pdb on error.')
    p.add_argument('--polly-user', default=getpass.getuser(),
                   help='username for AWS Polly')
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
        try:
            render_target(tree, target, ns)
        except Exception:
            if not ns.debug:
                raise
            import sys
            import pdb
            import traceback
            type, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)


if __name__ == '__main__':
    main()