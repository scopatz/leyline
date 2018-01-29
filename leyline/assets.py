"""A cache for indexing static data on the filesystem."""
import os
import json
import hashlib
from collections.abc import MuatableMapping, Sequence


class AssetsCache(MutableMapping):
    """A cache for indexing static data on the filesystem."""

    def __init__(self, filename, *args, **kwargs):
        """Requires a filename, all other args and kwargs are
        treated as arguments to dict().
        """
        self._dump_mutations = True
        self.filename = filename
        self.cache = {}
        self.load()
        self.update(*args, **kwargs)

    def load(self):
        """Loads the file into the cache."""
        with open(self.filename, 'r') as f:
            self.cache.update(json.load(f))

    def dump(self):
        """Writes the cache to the filesystem"""
        with open(self.filename, 'w') as f:
            json.dump(self.cache, f)

    def hash(self, key):
        """Returns the hash of a particular key. Only strings, bytes,
        and tuples of str or bytes are allowed.
        """
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
        return m.hexdigest()

    def gc(self):
        """Remove elements from the cache that are gone from the file system"""
        bad = {k for k, v in self.cache.items() if not os.path.isfile(v)}
        for b in bad:
            del self.cache[b]
        if self._dump_mutations:
            self.dump()

    #
    # mutable mapping interface
    #

    def __len__(self):
        return len(self.cache)

    def __iter__(self):
        yield from self.cache

    def __getitem__(self, key):
        m = self.hash(key)
        return self.cache[m]

    def __setitem__(self, key, value):
        m = self.hash(key)
        self.key[m] = value
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
