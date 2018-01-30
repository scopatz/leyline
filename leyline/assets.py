"""A cache for indexing static data on the filesystem."""
import os
import json
import hashlib
from collections.abc import MutableMapping, Sequence


class AssetsCache(MutableMapping):
    """A cache for indexing static data on the filesystem."""

    def __init__(self, cachefile, srcfile, *args, **kwargs):
        """Requires a cache filename and a srcfile that all assests come from.
        All other args and kwargs are treated as arguments to dict().
        """
        self._dump_mutations = False
        self.cachefile = cachefile
        self._srcfile = self.srchash = None
        # the cache maps md5 sums of keys to a 2-list of ['filename', {'srcfile': 'srchash'}]
        self.cache = {}
        # maps the sources to the current MD5 hash
        self.sources = {}
        # cache keys, not stored
        self._hashes = {}
        self.load()
        self.srcfile = srcfile
        self.update(*args, **kwargs)
        self._dump_mutations = True
        self.dump()

    def load(self):
        """Loads the file into the cache."""
        if not os.path.isfile(self.cachefile):
            return
        with open(self.cachefile, 'r') as f:
            data = json.load(f)
        self.cache.update(data.get('cache', ()))
        self.sources.update(data.get('sources', ()))

    def dump(self):
        """Writes the cache to the filesystem"""
        data = {'cache': self.cache, 'sources': self.sources}
        with open(self.cachefile, 'w') as f:
            json.dump(data, f, indent=' ', sort_keys=True)

    @property
    def srcfile(self):
        """The path to the current source file"""
        return self._srcfile

    @srcfile.setter
    def srcfile(self, value):
        self._srcfile = value
        with open(value, 'rb') as f:
            b = f.read()
        m = hashlib.md5(b)
        h = self.srchash = m.hexdigest()
        self.sources[value] = h
        if self._dump_mutations:
            self.dump()

    def hash(self, key):
        """Returns the hash of a particular key. Only strings, bytes,
        and tuples of str or bytes are allowed.
        """
        h = self._hashes.get(key, None)
        if h is not None:
            return h
        m = hashlib.md5()
        if isinstance(key, str):
            m.update(key.encode())
        elif isinstance(key, bytes):
            m.update(key)
        elif isinstance(key, Sequence):
            for k in key:
                if isinstance(k, str):
                    m.update(k.encode())
                elif isinstance(k, str):
                    m.update(k)
                else:
                    msg = 'Assets {0!r} in {1!r} is not a str or bytes'
                    raise TypeError(msg.format(k, key))
        else:
            msg = 'Assets key {0!r} is not a str or bytes'
            raise TypeError(msg.format(key))
        h = self._hashes[key] = m.hexdigest()
        return h

    def gc(self):
        """Remove elements from the cache that are gone from the file system"""
        # find the bad entries
        bad = set()
        for key, (filename, sources) in self.cache.items():
            if not os.path.isfile(filename):
                bad.add(key)
                continue
            # remove sources whose hashes no longer match
            bad_srcs = {s for s, h in sources.items() if h != self.sources.get(s, '')}
            for s in bad_srcs:
                del sources[s]
            # if there are no sources for this file anymore, remove the entry.
            if not sources:
                bad.add(key)
        # remove bad entries
        for b in bad:
            filename, sources = self.cache.pop(b, ['', {}])
            if os.path.isfile(filename):
                os.remove(filename)
        if self._dump_mutations:
            self.dump()

    #
    # mutable mapping interface
    #

    def __len__(self):
        return len(self.cache)

    def __iter__(self):
        yield from self.cache

    def __contains__(self, key):
        m = self.hash(key)
        return m in self.cache

    def __getitem__(self, key):
        m = self.hash(key)
        return self.cache[m][0]

    def __setitem__(self, key, value):
        m = self.hash(key)
        curr = self.cache[m] = self.cache.get(m, ['', {}])
        curr[0] = value
        curr[1][self.srcfile] = self.srchash
        if self._dump_mutations:
            self.dump()

    def __delitem__(self, key):
        m = self.hash(key)
        del self.cache[m]
        if self._dump_mutations:
            self.dump()

    def update(self, *args, **kwargs):
        """Update that only dumps back to the file at the end"""
        orig = self._dump_mutations
        if orig:
            self._dump_mutations = False
        d = dict(*args, **kwargs)
        for k, v in d.items():
            self[k] = v
        self._dump_mutations = orig
        if orig and d:
            self.dump()

    def clear(self):
        """Removes all elements from the cache"""
        self.cache.clear()
        if self._dump_mutations:
            self.dump()


class GC:
    """Fake AST visitor that doesn't actually walk nodes, but does
    clean up garbage when rendered.
    """

    def __init__(self, **kwargs):
        pass

    def render(self, assets=None, **kwargs):
        assets.gc()
        return True
