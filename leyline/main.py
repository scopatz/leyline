"""Command line interface for leyline"""
import os
import getpass
import importlib
from argparse import ArgumentParser

from leyline.parser import parse
from leyline.assets import AssetsCache
from leyline.events import EVENTS_CTX


TARGETS = {
    'gc': ('leyline.assets', 'GC'),
    'ast': ('leyline.ast', 'PrettyFormatter'),
    'ansi': ('leyline.ansi', 'AnsiFormatter'),
    'notes': ('leyline.notes', 'Notes'),
    'polly': ('leyline.audio', 'SSML'),
    'dictate': ('leyline.audio', 'Dictation'),
    'slides': ('leyline.video', 'Slides'),
    'video': ('leyline.video', 'Video'),
    }
TARGET_VISITORS = {}


def make_assets_cache(ns):
    """Adds an assets cache to the current namespace."""
    os.makedirs(ns.assets_dir, exist_ok=True)
    cachefile = os.path.join(ns.assets_dir, ns.assets_file)
    print("Loading assets cache " + cachefile)
    ns.assets = AssetsCache(cachefile, ns.filename)


def render_target(tree, target, ns):
    modname, clsname = TARGETS[target]
    mod = importlib.import_module(modname)
    cls = getattr(mod, clsname)
    visitor = cls(contexts=ns.contexts)
    return visitor.render(tree=tree, **ns.__dict__)


def make_argparser():
    """makes an argparser instance for leyline"""
    p = ArgumentParser('leyline', description='Leyline Rendering Tool')
    p.add_argument('--pdb', '--debug', default=False, action='store_true',
                   dest='debug', help='Enter into pdb on error.')
    p.add_argument('--polly-user', default=getpass.getuser(),
                   help='username for AWS Polly')
    p.add_argument('--assets-dir', '--static-dir', default='_static',
                   help='Path to assets or static directory, where large '
                        'unique files will be stored', dest='assets_dir')
    p.add_argument('--assets-cache', default='assets.json', dest='assets_file',
                   help='Filename (relative to assets dir) that the assets '
                        'cache will use to store data.')
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
    tree = parse(s, filename=ns.filename)
    make_assets_cache(ns)
    ns.contexts = {'ctx': EVENTS_CTX}
    for target in ns.targets:
        try:
            rtn = render_target(tree, target, ns)
        except Exception:
            if not ns.debug:
                raise
            import sys
            import pdb
            import traceback
            type, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)
        # check break condition
        if rtn is None:
            return

if __name__ == '__main__':
    main()
