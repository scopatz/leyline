"""The leyline language lexer."""
import re
from textwrap import dedent
from collections import deque

import ply.lex


RE_SPACES = re.compile('( +)')


class Lexer(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.build(**kwargs)

    # lexing happens in order of precedence in the file.

    def t_MULTILINECOMMENT(self, t):
        r"[#][#][#][^#\\]*(?:(?:\\.|[#](?![#][#][#]))[^[#]\\]*)*[#][#][#]"
        self._set_column(t)
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value[3:-3]
        return t

    def t_CODEBLOCK(self, t):
        r"```[^`\\]*(?:(?:\\.|`(?!``))[^`\\]*)*```"
        self._set_column(t)
        t.lexer.lineno += t.value.count('\n')
        lang, _, block = t.value[3:-3].partition('\n')
        t.value = (lang.strip(), dedent(block))
        return t

    def t_MULTILINEMATH(self, t):
        r"\$\$\$[^\$\\]*(?:(?:\\.|\$(?!\$\$))[^\$\\]*)*\$\$\$"
        self._set_column(t)
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value[3:-3]
        return t

    def t_COMMENT(self, t):
        r'[#][^\r\n]*'
        self._set_column(t)
        t.value = t.value[1:].strip()
        return t

    def t_INLINECODE(self, t):
        r"`([^\n`\\]*(?:\\.[^\n`\\]*)*)`"
        self._set_column(t)
        t.value = t.value[1:-1]
        return t

    def t_INLINEMATH(self, t):
        r"\$([^\n\$\\]*(?:\\.[^\n\$\\]*)*)\$"
        self._set_column(t)
        t.value = t.value[1:-1]
        return t

    def t_LBRACEPERCENTRBRACE(self, t):
        r'{%}'
        self._set_column(t)
        return t

    def t_LBRACEPERCENT(self, t):
        r'{%'
        self._set_column(t)
        return t

    def t_PERCENTRBRACE(self, t):
        r'%}'
        self._set_column(t)
        return t

    def t_DOUBLELBRACE(self, t):
        r'{{'
        self._set_column(t)
        return t

    def t_DOUBLERBRACE(self, t):
        r'}}'
        self._set_column(t)
        return t

    def t_DOUBLEDASH(self, t):
        r'--'
        self._set_column(t)
        return t

    def t_DOUBLESTAR(self, t):
        r'\*\*'
        self._set_column(t)
        return t

    def t_DOUBLETILDE(self, t):
        r'~~'
        self._set_column(t)
        return t

    def t_DOUBLEUNDER(self, t):
        r'__'
        self._set_column(t)
        return t

    reserved = {
        'rend': 'REND',
        'with': 'WITH',
        'table': 'TABLE',
        }

    def t_REND(self, t):
        r'rend(?: +[A-Za-z_][A-Za-z0-9_]*)+::'
        self._set_column(t)
        subtoks = RE_SPACES.split(t.value[4:-2])[1:]
        for space in subtoks[::2]:
            if space != ' ':
                self._lexer_error(t, 'render targets must be separated by '
                                     'a single space " ".')
        t.value = set(subtoks[1::2])
        return t

    def t_WITH(self, t):
        r'with(| +[A-Za-z_][A-Za-z0-9_]*)::'
        self._set_column(t)
        ctx = t.value[4:-2]
        if not ctx:
            t.value = ctx
            return t
        subtoks = RE_SPACES.split(ctx)[1:]
        if subtoks[0] != ' ':
            self._lexer_error(t, 'with context must be separated by '
                                 'a single space "with ctx::".')
        t.value = subtoks[1]
        return t

    def t_TABLE(self, t):
        r'table::'
        self._set_column(t)
        return t

    def t_INDENT(self, t):
        r'\n+[ \t]*'
        # track line numbers
        t.lexer.lineno += t.value.count('\n')
        i = t.value.lstrip('\n')
        last = self.indents[-1]
        if i == last:
            # return if this basically text
            self._set_column(t)
            t.type = 'TEXT'
            return t
        # now we know we have an indent or a dedent
        t.lineno = t.lexer.lineno
        t.column = 1
        t.value = i
        if len(i) > len(last) and i.startswith(last):
            self.indents.append(i)
        elif len(i) < len(last) and last.startswith(i):
            del self.indents[-1]
            last = self.indents[-1]
            t.type = 'DEDENT'
            while len(i) < len(last) and last.startswith(i):
                dedent = ply.lex.LexToken()
                dedent.type = 'DEDENT'
                dedent.value = last
                dedent.lineno = t.lineno
                dedent.lexpos = t.lexpos
                self.queue.append(dedent)
                del self.indents[-1]
                last = self.indents[-1]
        else:
            raise SyntaxError("Indentation level doesn't match " + str(t))
        return t

    text_breaks = '\n#`${}%-*~_:' + ''.join(k[0] for k in sorted(set(reserved.keys())))

    @ply.lex.TOKEN('[' + text_breaks + ']')
    def t_UNBREAKTEXT(self, t):
        self._set_column(t)
        t.type = 'TEXT'
        return t

    @ply.lex.TOKEN('[^' + text_breaks + ']+')
    def t_TEXT(self, t):
        self._set_column(t)
        t.lexer.lineno += t.value.count('\n')
        return t

    def t_error(self, t):
        msg = "Illegal token {0!r}".format(t.value[0])
        self._lexer_error(t, msg)

    def t_eof(self, t):
        """Handle end of file conditions"""
        # dedent the world at the end of the file.
        if len(self.indents) == 1:
            return
        last = self.indents[-1]
        while len(self.indents) > 1:
            dedent = ply.lex.LexToken()
            dedent.type = 'DEDENT'
            dedent.value = last
            dedent.lineno = t.lineno
            dedent.lexpos = t.lexpos
            dedent.column = 1
            self.queue.append(dedent)
            del self.indents[-1]
            last = self.indents[-1]
        return self.token()

    def input(self, s):
        self.inp = s
        return self.lexer.input(s)

    def reset(self):
        self.lexer.lineno = 1
        self.inp = self.last = self.beforelast = self.filename = None
        self.queue = deque()
        self.indents = ['']

    def build(self, **kwargs):
        """Build the lexer"""
        self.lexer = ply.lex.lex(module=self, reflags=re.DOTALL, **kwargs)
        self.reset()

    def _next_token(self):
        """Obtain the next token"""
        # consume current queu
        if self.queue:
            return self.queue.popleft()
        # merge text tokens
        t = self.lexer.token()
        if t is not None and t.type == 'TEXT':
            next = self.lexer.token()
            while next is not None and next.type == 'TEXT':
                t.value += next.value
                next = self.lexer.token()
            self.queue.append(next)
        return t

    def token(self):
        """Retrieves the next token."""
        self.beforelast = self.last
        t = self.last = self._next_token()
        return t

    def __iter__(self):
        t = self.token()
        while t is not None:
            yield t
            t = self.token()

    _tokens = None

    @property
    def tokens(self):
        if self._tokens is None:
            toks = [t[2:] for t in dir(self) if t.startswith('t_') and t[2:].upper() == t[2:]]
            toks.append('DEDENT')
            self._tokens = tuple(toks)
        return self._tokens

    def _set_column(self, t):
        """Sets the column number of the token."""
        p = t.lexpos
        q = self.inp.rfind('\n', 0, p)
        if q < 0:
            col = p + 1
        else:
            col = p - q
        t.column = col

    def _lexer_error(self, t, msg):
        """Raises a syntax error coming from the lexer"""
        err_line = self.inp[:t.lexpos].rpartition('\n')[-1].partition('\n')[0].rstrip()
        err_line_pointer = '\n{}\n{: >{}}'.format(err_line, '^', t.column - 1)
        loc = '<document>' if self.filename is None else self.filename
        loc += ':' + str(t.lineno) + ':' + str(t.column)
        err = SyntaxError('{0}: {1}{2}'.format(loc, msg, err_line_pointer))
        err.lineno = loc
        raise err
