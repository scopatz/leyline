#!/usr/bin/env python
try:
    from setuptools import setup
    HAVE_SETUPTOOLS = True
except ImportError:
    from distutils.core import setup
    HAVE_SETUPTOOLS = False


VERSION = '0.0.0'

setup_kwargs = {
    "version": VERSION,
    "description": 'Lecture Creation',
    "license": 'BSD 3-clause',
    "author": 'Anthony Scopatz',
    "author_email": 'scopatz@gmail.com',
    "url": 'https://github.com/scopatz/leyline',
    "download_url": "https://github.com/scopatz/leyline/zipball/" + VERSION,
    "classifiers": [
        "License :: OSI Approved",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Utilities",
        ],
    "zip_safe": False,
    "data_files": [("", ['LICENSE', 'README.rst']),],
    "scripts": ["scripts/leyline"],
    }

if HAVE_SETUPTOOLS:
    setup_kwargs['install_requires'] = ['ply']


if __name__ == '__main__':
    setup(
        name='leyline',
        packages=['leyline'],
        long_description=open('README.rst').read(),
        **setup_kwargs
        )
