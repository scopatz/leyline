"""Parser for leyline"""
import os

import ply.yacc

from leyline.lexer import Lexer
from leyline.ast import Document, Text, TextBlock, Comment, CodeBlock


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
        # some prelim setup
        self.lexer = lexer = Lexer()
        self.tokens = lexer.tokens
        self._lines = None
        self.leyline_doc = None

        tok_rules = ['text']
        for rule in tok_rules:
            self._tok_rule(rule)

        # create yacc parser
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

    def _yacc_lookahead_token(self):
        """Gets the next-to-last and last token seen by the lexer."""
        return self.lexer.beforelast, self.lexer.last

    def _tok_rule(self, rulename):
        """For a rule name, creates a rule that returns the corresponding token.
        '_tok' is appended to the rule name.
        """

        def tokfunc(self, p):
            s, t = self._yacc_lookahead_token()
            uprule = rulename.upper()
            if s is not None and s.type == uprule:
                p[0] = s
            elif t is not None and t.type == uprule:
                p[0] = t
            else:
                raise TypeError('token for {0!r} not found.'.format(rulename))

        tokfunc.__doc__ = '{0}_tok : {1}'.format(rulename, rulename.upper())
        tokfunc.__name__ = 'p_' + rulename + '_tok'
        setattr(self.__class__, tokfunc.__name__, tokfunc)


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

    def p_start_symbols_blocks(self, p):
        """start_symbols : blocks"""
        p[0] = Document(body=p[1], lineno=1, column=1)

    def p_empty(self, p):
        """empty : """
        p[0] = None

    #
    # Define blocks and block lists
    #

    def p_block(self, p):
        """block : textblock"""
        p[0] = p[1]

    def p_blocks_single(self, p):
        """blocks : block"""
        p[0] = [p[1]]

    def p_blocks_append(self, p):
        """blocks : blocks block"""
        p1 = p[1]
        p1.append(p[2])
        p[0] = p1

    #
    # Define text blocks
    #

    def p_textblock_entry(self, p):
        """textblock_entry : text_tok"""
        t = p[1]
        p[0] = Text(text=t.value, lineno=t.lineno, column=t.column)

    def p_textblock_single(self, p):
        """textblock : textblock_entry"""
        p1 = p[1]
        p[0] = TextBlock(body=[p1], lineno=p1.lineno, column=p1.column)

    def p_textblock_append(self, p):
        """textblock : textblock textblock_entry"""
        p1 = p[1]
        p1.body.append(p[2])
        p[0] = p1
