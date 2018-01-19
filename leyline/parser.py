"""Parser for leyline"""
import os
from textwrap import dedent

import ply.yacc

from leyline.lexer import Lexer
from leyline.ast import (Document, Text, TextBlock, Comment, CodeBlock, Bold,
    Italics, Underline, Strikethrough, With, RenderFor)


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

        self._attach_nodedent_base_rules()

        tok_rules = ['text', 'doubledash', 'doublestar', 'doubletilde',
                     'doubleunder', 'rend', 'with', 'indent', 'dedent']
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
        self.filename = None

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
        self.filename = filename
        tree = self.parser.parse(input=s, lexer=self.lexer, debug=debug_level)
        return tree

    @property
    def lines(self):
        if self._lines is None and self.leyline_doc is not None:
            self._lines = self.leyline_doc.splitlines(keepends=True)
        return self._lines

    def _parse_error(self, msg, lineno=None, column=None):
        if lineno is None or column is None:
            before, last = self._yacc_lookahead_token()
            tok = before if before is not None else last
            if tok is not None:
                lineno = tok.lineno
                column = tok.column
        if self.leyline_doc is None or lineno is None or column is None:
            err_line_pointer = ''
        else:
            col = column - 1
            lines = self.lines
            if lineno == 0:
                lineno = len(lines)
            i = lineno - 1
            if 0 <= i < len(lines):
                err_line = lines[i].rstrip()
                err_line_pointer = '\n{}\n{: >{}}'.format(err_line, '^', col)
            else:
                err_line_pointer = ''
        loc = self.filename
        if lineno is not None:
            loc += ':' + str(lineno)
        if column is not None:
            loc += ':' + str(column)
        err = SyntaxError('{0}: {1}{2}'.format(loc, msg, err_line_pointer))
        err.lineno = loc
        raise err

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
        """block : textblock
                 | withblock
                 | rendblock
        """
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
    # rend blocks
    #

    def p_rend(self, p):
        """rendblock : rend_tok text_tok COLON INDENT blocks DEDENT"""
        p1 = p[1]
        p2 = p[2]
        targs = p2.value
        if not targs.startswith(' '):
            self._parse_error('Invalid render targets {0!r}'.format(targs),
                              lineno=p2.lineno, column=p2.column)
        targs = set(targs.split())
        p[0] = RenderFor(targets=targs, body=p[5], lineno=p1.lineno, column=p1.column)

    #
    # with blocks
    #

    def p_with_null(self, p):
        """withblock : with_tok COLON indent_tok nodedent dedent_tok"""
        p1 = p[1]
        text = self.leyline_doc[p[3].lexpos:p[5].lexpos]
        text = dedent(text.strip('\n'))
        p[0] = With(lineno=p1.lineno, column=p1.column, text=text)

    def p_with_name(self, p):
        """withblock : with_tok TEXT COLON indent_tok nodedent dedent_tok"""
        p1 = p[1]
        ctx = p[2].strip() # maybe have a stronger enforcement here
        text = self.leyline_doc[p[4].lexpos:p[6].lexpos]
        text = dedent(text.strip('\n'))
        p[0] = With(lineno=p1.lineno, column=p1.column, text=text, ctx=ctx)

    def p_with_reserved(self, p):
        """withblock : with_tok TEXT REND COLON indent_tok nodedent dedent_tok
                     | with_tok TEXT WITH COLON indent_tok nodedent dedent_tok
                     | with_tok TEXT TABLE COLON indent_tok nodedent dedent_tok
                     | with_tok TEXT RESERVED COLON indent_tok nodedent dedent_tok
        """
        p1 = p[1]
        if p[2] != ' ':
            assert False
        ctx = p[3]
        text = self.leyline_doc[p[5].lexpos:p[7].lexpos]
        text = dedent(text.strip('\n'))
        p[0] = With(lineno=p1.lineno, column=p1.column, text=text, ctx=ctx)

    #
    # Define text blocks
    #

    def p_textblock_entry_text(self, p):
        """textblock_entry          : text_tok
           not_bold_entry           : text_tok
           not_italics_entry        : text_tok
           not_underline_entry      : text_tok
           not_strikethrough_entry  : text_tok
        """
        t = p[1]
        p[0] = Text(text=t.value, lineno=t.lineno, column=t.column)

    def p_textblock_entry_formatted_text(self, p):
        """textblock_entry          : bold
                                    | italics
                                    | underline
                                    | strikethrough
           not_bold_entry           : italics
                                    | underline
                                    | strikethrough
           not_italics_entry        : bold
                                    | underline
                                    | strikethrough
           not_underline_entry      : bold
                                    | italics
                                    | strikethrough
           not_strikethrough_entry  : bold
                                    | italics
                                    | underline
        """
        p[0] = p[1]

    def p_textblock_single(self, p):
        """textblock              : textblock_entry
           not_boldblock          : not_bold_entry
           not_italicsblock       : not_italics_entry
           not_underlineblock     : not_underline_entry
           not_strikethroughblock : not_strikethrough_entry
        """
        p1 = p[1]
        p[0] = TextBlock(body=[p1], lineno=p1.lineno, column=p1.column)

    def p_textblock_append(self, p):
        """textblock              : textblock textblock_entry
           not_boldblock          : not_boldblock not_bold_entry
           not_italicsblock       : not_italicsblock not_italics_entry
           not_underlineblock     : not_underlineblock not_underline_entry
           not_strikethroughblock : not_strikethroughblock not_strikethrough_entry
        """
        p1 = p[1]
        p1.body.append(p[2])
        p[0] = p1


    #
    # Define some inline formatting
    #

    def p_bold(self, p):
        """bold : doublestar_tok not_boldblock DOUBLESTAR"""
        p1 = p[1]
        p[0] = Bold(lineno=p1.lineno, column=p1.column, body=p[2].body)

    def p_italics(self, p):
        """italics : doubletilde_tok not_italicsblock DOUBLETILDE"""
        p1 = p[1]
        p[0] = Italics(lineno=p1.lineno, column=p1.column, body=p[2].body)

    def p_underline(self, p):
        """underline : doubleunder_tok not_underlineblock DOUBLEUNDER"""
        p1 = p[1]
        p[0] = Underline(lineno=p1.lineno, column=p1.column, body=p[2].body)

    def p_strikethrough(self, p):
        """strikethrough : doubledash_tok not_strikethroughblock DOUBLEDASH"""
        p1 = p[1]
        p[0] = Strikethrough(lineno=p1.lineno, column=p1.column, body=p[2].body)

    #
    # represent a block that doesn't dedent past the current
    # indentation level
    #

    def _attach_nodedent_base_rules(self):
        toks = set(self.tokens)
        toks.remove('DEDENT')
        ts = '\n       | '.join(sorted(toks))
        doc = 'nodedent : ' + ts + '\n'
        self.p_nodedent_base.__func__.__doc__ = doc

    def p_nodedent_base(self, p):
        # see above attachment function
        pass

    def p_nodedent_any(self, p):
        """nodedent : INDENT any_dedent_toks DEDENT"""
        pass

    def p_nodedent_many(self, p):
        """nodedent : nodedent nodedent"""
        pass

    def p_any_dedent_tok(self, p):
        """any_dedent_tok : nodedent
                          | DEDENT
        """
        pass

    def p_any_dedent_toks(self, p):
        """any_dedent_toks : any_dedent_tok
                           | any_dedent_toks any_dedent_tok
        """
        pass

    #
    # special psuedo-rules
    #

    def p_error(self, p):
        if p is None:
            self._parse_error('no further code')
        else:
            msg = 'code: {0}'.format(p.value),
            self._parse_error(msg, lineno=p.lineno, column=p.column)
