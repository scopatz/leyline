"""Parser for leyline"""
import os

import ply.yacc

from leyline.lexer import Lexer
from leyline.ast import Document, Text, Comment, CodeBlock

class Parser(object):
    """A base class that parses the xonsh language."""

    def __init__(self,
                 lexer_optimize=True,
                 lexer_table='leyline.lexer_table',
                 yacc_optimize=True,
                 yacc_table='leyline.parser_table',
                 yacc_debug=False,
                 outputdir=None):
        """
        Parameters
        ----------
        lexer_optimize : bool, optional
            Set to false when unstable and true when lexer is stable.
        lexer_table : str, optional
            Lexer module used when optimized.
        yacc_optimize : bool, optional
            Set to false when unstable and true when parser is stable.
        yacc_table : str, optional
            Parser module used when optimized.
        yacc_debug : debug, optional
            Dumps extra debug info.
        outputdir : str or None, optional
            The directory to place generated tables within. Defaults to the root
            xonsh dir.
        """
        self.lexer = lexer = Lexer()
        self.tokens = lexer.tokens
        self._lines = None
        self.leyline_doc = None

        yacc_kwargs = dict(module=self,
                           debug=yacc_debug,
                           start='start_symbols',
                           optimize=yacc_optimize,
                           tabmodule=yacc_table)
        if not yacc_debug:
            yacc_kwargs['errorlog'] = yacc.NullLogger()
        if outputdir is None:
            outputdir = os.path.dirname(os.path.dirname(__file__))
        yacc_kwargs['outputdir'] = outputdir
        self.parser = ply.yacc.yacc(**yacc_kwargs)

    def reset(self):
        """Resets for clean parsing."""
        self.lexer.reset()
        self._lines = None
        self.leyline_doc = None

    def parse(self, s, filename='<document>', debug_level=0):
        """Returns an abstract syntax tree of the leyline document.

        Parameters
        ----------
        s : str
            The leyline document.
        filename : str, optional
            Name of the file.
        debug_level : str, optional
            Debugging level passed down to yacc.

        Returns
        -------
        tree : leyline.ast.Node
        """
        self.reset()
        self.leyline_doc = s
        self.lexer.fname = filename
        tree = self.parser.parse(input=s, lexer=self.lexer, debug=debug_level)
        return tree

    @property
    def lines(self):
        if self._lines is None and self.leyline_doc is not None:
            self._lines = self.leyline_doc.splitlines(keepends=True)
        return self._lines

    #
    # Parsing rules
    #

    def p_start_symbols_empty(self, p):
        """start_symbols : empty"""
        p[0] = Document(lineno=1, column=1)

    def p_empty(self, p):
        'empty : '
        p[0] = None


