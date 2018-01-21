"""Parser for leyline"""
import os
import itertools
from textwrap import dedent
from collections.abc import Sequence

import ply.yacc

from leyline.lexer import Lexer
from leyline.ast import (Node, Document, PlainText, TextBlock, Comment, CodeBlock,
    Bold, Italics, Underline, Strikethrough, With, RenderFor, List, Table,
    InlineCode, Equation, InlineMath, CorporealMacro, IncorporealMacro)


def _lowest_column(x):
    if isinstance(x, Node):
        return x.column
    elif isinstance(x, str):
        return 'cannot find column of string ' + repr(x)
    elif isinstance(x, Sequence):
        return _lowest_column(x[0])
    else:
        return 'cannot find column of type ' + repr(type(x))


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

        tok_rules = ['plaintext', 'doubledash', 'doublestar', 'doubletilde',
                     'doubleunder', 'rend', 'with', 'indent', 'dedent',
                     'listbullet', 'table', 'comment', 'multilinecomment',
                     'codeblock', 'inlinecode', 'multilinemath', 'inlinemath',
                     'doublelbrace', 'doublerbrace', 'lbracepercent',
                     'percentrbrace']
        for rule in tok_rules:
            self._tok_rule(rule)

        # create yacc parser
        yacc_kwargs = dict(module=self,
                           debug=yacc_debug,
                           start='start_symbols',
                           optimize=yacc_optimize,
                           tabmodule=yacc_table)
        if not yacc_debug:
            yacc_kwargs['errorlog'] = ply.yacc.NullLogger()
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
        self.filename = self.lexer.filename = filename
        tree = self.parser.parse(input=s, lexer=self.lexer, debug=debug_level)
        return tree

    @property
    def lines(self):
        if self._lines is None and self.leyline_doc is not None:
            self._lines = self.leyline_doc.splitlines(keepends=True)
        return self._lines

    def source_slice(self, start, stop):
        """Gets the original source code from two (line, col) tuples in
        source-space (i.e. lineno and column start at 1).
        """
        bline, bcol = start
        eline, ecol = stop
        bline -= 1
        bcol -= 1
        ecol -= 1
        lines = self.lines[bline:eline]
        if ecol == 0:
            explen = eline - bline
            if explen == len(lines) and explen > 1:
                lines[-1] = ''
        else:
            lines[-1] = lines[-1][:ecol]
        lines[0] = lines[0][bcol:]
        return ''.join(lines)

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
        """block : list
                 | table
                 | comment
                 | equation
                 | codeblock
                 | rendblock
                 | textblock
                 | withblock
                 | corporealmacro
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
    # comments blocks
    #

    def p_comment(self, p):
        """comment : comment_tok"""
        p1 = p[1]
        p[0] = Comment(lineno=p1.lineno, column=p1.column, text=p1.value)

    def p_multilinecomment(self, p):
        """comment : multilinecomment_tok"""
        p1 = p[1]
        p[0] = Comment(lineno=p1.lineno, column=p1.column, text=p1.value)

    def p_comment_append(self, p):
        """comment : comment comment_tok"""
        p1 = p[1]
        p1.text += '\n' + p[2].value
        p[0] = p1

    def p_multilinecomment_append(self, p):
        """comment : comment multilinecomment_tok"""
        p1 = p[1]
        p1.text += '\n' + p[2].value
        p[0] = p1

    #
    # code
    #

    def p_codeblock(self, p):
        """codeblock : codeblock_tok"""
        p1 = p[1]
        p[0] = CodeBlock(lineno=p1.lineno, column=p1.column,
                         lang=p1.value[0], text=p1.value[1])

    def p_inlinecode(self, p):
        """inlinecode : inlinecode_tok"""
        p1 = p[1]
        p[0] = InlineCode(lineno=p1.lineno, column=p1.column,
                          text=p1.value)

    #
    # math
    #

    def p_equation(self, p):
        """equation : multilinemath_tok"""
        p1 = p[1]
        p[0] = Equation(lineno=p1.lineno, column=p1.column,
                        text=p1.value)

    def p_inlinemath(self, p):
        """inlinemath : inlinemath_tok"""
        p1 = p[1]
        p[0] = InlineMath(lineno=p1.lineno, column=p1.column,
                          text=p1.value)

    #
    # macros
    #

    def p_incorporealmacro(self, p):
        """incorporealmacro : doublelbrace_tok blocks doublerbrace_tok"""
        p1 = p[1]
        p3 = p[3]
        text = self.source_slice((p1.lineno, p1.column + 2),
                                 (p3.lineno, p3.column)).strip()
        p[0] = IncorporealMacro(lineno=p1.lineno, column=p1.column,
                                text=text)

    def p_corporealmacro(self, p):
        """corporealmacro : lbracepercent_tok blocks percentrbrace_tok blocks LBRACEPERCENTRBRACE"""
        p1 = p[1]
        p3 = p[3]
        head = self.source_slice((p1.lineno, p1.column + 2),
                                 (p3.lineno, p3.column)).strip()
        if not head:
            self._parse_error('corporeal macro must have a name!',
                              lineno=p1.lineno, column=p1.column)
        name, _, args = head.partition(' ')
        p[0] = CorporealMacro(lineno=p1.lineno, column=p1.column,
                              name=name.strip(), args=args.strip(), body=p[4])

    #
    # rend blocks
    #

    def p_rend(self, p):
        """rendblock : rend_tok INDENT blocks DEDENT"""
        p1 = p[1]
        targs = p1.value
        p[0] = RenderFor(targets=targs, body=p[3], lineno=p1.lineno, column=p1.column)

    #
    # with blocks
    #

    def p_with(self, p):
        """withblock : with_tok indent_tok nodedent dedent_tok"""
        p1 = p[1]
        text = self.leyline_doc[p[2].lexpos:p[4].lexpos]
        text = dedent(text.strip('\n'))
        p[0] = With(lineno=p1.lineno, column=p1.column, text=text, ctx=p1.value)

    #
    # list block
    #

    def p_listitem_text(self, p):
        """listitem : listbullet_tok textblock"""
        p[0] = [p[1], p[2]]

    def p_listitem_blocks(self, p):
        """listitem : listbullet_tok INDENT blocks DEDENT"""
        p[0] = [p[1]] + p[3]

    def p_listitem_text_blocks(self, p):
        """listitem : listbullet_tok textblock INDENT blocks DEDENT"""
        p[0] = [p[1], p[2]] + p[4]

    def p_listitems_single(self, p):
        """listitems : listitem"""
        p[0] = [p[1]]

    def p_listitems_append(self, p):
        """listitems : listitems listitem"""
        p1 = p[1]
        p1.append(p[2])
        p[0] = p1

    def _bullets_and_items(self, listitems):
        firstbullet = listitems[0][0].value
        lineno = listitems[0][0].lineno
        column = listitems[0][0].column
        bullets = []
        same_bullets = True
        items = []
        for item in listitems:
            b, i = item[0], item[1:]
            if b.value != firstbullet:
                same_bullets = False
            bullets.append(b.value)
            items.append(i)
        if same_bullets:
            bullets = firstbullet
        return lineno, column, bullets, items

    def p_list(self, p):
        """list : listitems"""
        lineno, column, bullets, items = self._bullets_and_items(p[1])
        p[0] = List(lineno=lineno, column=column, bullets=bullets, items=items)

    #
    # table block
    #

    def _items_to_rows(self, items, lineno=None, column=None):
        rows = []
        for item in items:
            if len(item) != 1:
                lineno = getattr(item, 'lineno', lineno)
                column = getattr(item, 'column', column)
                self._parse_error("incorrectly formatted table row",
                                  lineno=lineno, column=column)
            row = item[0]
            if not isinstance(row, List):
                lineno = getattr(row, 'lineno', lineno)
                column = getattr(row, 'column', column)
                self._parse_error("table row must be formatted as a list",
                                  lineno=lineno, column=column)
            rows.append(row.items)
        return rows

    _table_info_parsers = None

    @property
    def table_info_parsers(self):
        if self._table_info_parsers is None:

            def widths(s):
                if s == 'auto':
                    return True, s
                w = []
                total = 0.0
                for t in s.split():
                    try:
                        n = float(t)
                    except ValueError as e:
                        return False, str(e)
                    if n < 0.0:
                        return False, "negative widths not allowed"
                    w.append(n)
                    total += n
                for i in range(len(w)):
                    w[i] /= total
                return True, w

            def asint(s):
                try:
                    n = int(s)
                except ValueError as e:
                    return False, str(e)
                return True, n

            tip = {'widths': widths, 'header_cols': asint, 'header_rows': asint}
            self._table_info_parsers = tip
        return self._table_info_parsers

    def _parse_table_info(self, t):
        lineno = t.lineno - 1
        column = t.column
        lines = t.value.splitlines()
        info = {}
        tip = self.table_info_parsers
        for line in lines:
            lineno += 1
            line = line.strip()
            if not line:
                # empty lines are OK
                continue
            name, sep, value = line.partition('=')
            if not sep:
                self._parse_error("table metadata information must "
                                  "contain an assignment equals sign '='",
                                  lineno, column)
            name = name.strip()
            if name not in tip:
                self._parse_error("table metadata name not recognized",
                                  lineno, column)
            if name in info:
                self._parse_error(name + " appears multiple times in "
                                  "table metadata", lineno, column)
            status, val = tip[name](value)
            if not status:
                self._parse_error(val, lineno, column)
            info[name] = val
        return info

    def p_table_plain(self, p):
        """table : table_tok INDENT listitems DEDENT"""
        p1 = p[1]
        lineno, column, _, items = self._bullets_and_items(p[3])
        rows = self._items_to_rows(items, lineno, column)
        p[0] = Table(lineno=p1.lineno, column=p1.column, rows=rows)

    def p_table_info(self, p):
        """table : table_tok INDENT plaintext_tok listitems DEDENT"""
        p1 = p[1]
        info = self._parse_table_info(p[3])
        lineno, column, _, items = self._bullets_and_items(p[4])
        rows = self._items_to_rows(items, lineno, column)
        p[0] = Table(lineno=p1.lineno, column=p1.column, rows=rows,
                     **info)

    #
    # Define text blocks
    #

    def p_textblock_entry_plain(self, p):
        """textblock_entry          : plaintext_tok
           not_bold_entry           : plaintext_tok
           not_italics_entry        : plaintext_tok
           not_underline_entry      : plaintext_tok
           not_strikethrough_entry  : plaintext_tok
        """
        t = p[1]
        p[0] = PlainText(text=t.value, lineno=t.lineno, column=t.column)

    def p_special_entry(self, p):
        """special_entry : inlinecode
                         | inlinemath
                         | incorporealmacro
        """
        p[0] = p[1]

    def p_textblock_entry_special(self, p):
        """textblock_entry          : special_entry
           not_bold_entry           : special_entry
           not_italics_entry        : special_entry
           not_underline_entry      : special_entry
           not_strikethrough_entry  : special_entry
        """
        p[0] = p[1]

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


_PARSER = None


def parse(s, *, filename='<document>', debug_level=0, **kwargs):
    """Parses a leyline document and returns an AST.
    filename and  debug_level are the same as in the parse() method.
    Additional kwargs are passed to the parser constructor.
    """
    global _PARSER
    if _PARSER is None:
        _PARSER = Parser(**kwargs)
    return _PARSER.parse(s, filename=filename, debug_level=debug_level)
