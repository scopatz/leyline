"""The leyline language lexer."""
import re
from textwrap import dedent
from collections import deque

import ply.lex


RE_INDENT = re.compile('\n+([ \t]*)[^ \n\t]*')
RE_SPACES = re.compile('( +)')
RE_LISTBULLET = re.compile('([-*]|\d+\.) ')
RE_BULLETS = re.compile('([ \t]*)((?:[-*]|\d+\.) )+')


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
        'figure': 'FIGURE',
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

    def t_FIGURE(self, t):
        r'figure::'
        self._set_column(t)
        return t

    def _append_listbullet(self, bullet, t, nnl=0):
        if not bullet:
            return
        if bullet.endswith('.'):
            # must be a number
            bullet = int(bullet[:-1])
        li = ply.lex.LexToken()
        li.type = 'LISTBULLET'
        li.value = bullet
        li.lineno = t.lexer.lineno
        li.lexpos = t.lexpos + len(t.value) + nnl
        li.column = len(t.value.lstrip('\n')) + 1
        self.queue.append(li)

    def t_LISTBULLET(self, t):
        r'(([-*]|\d+\.) )'
        # check to see if we have a real list bullet
        self._set_column(t)
        toklen = len(t.value)
        i = self.inp.rfind('\n', 0, t.lexpos) + 1
        j = t.lexpos + toklen + 1
        pre = self.inp[i:j]
        m = RE_BULLETS.match(pre)
        if m is None:
            # we don't have a real list bullet, make text instead
            t.type = 'PLAINTEXT'
            return t
        # must have a real list bullet
        bullet = t.value.strip()
        if bullet.endswith('.'):
            # must be a number
            bullet = int(bullet[:-1])
        t.value = bullet
        # append indent after bullet
        indent = self.indents[-1] + (' ' * toklen)
        u = ply.lex.LexToken()
        u.type = 'INDENT'
        u.value = indent
        u.lexpos = t.lexpos
        u.lineno = t.lineno
        u.column = t.column
        self.queue.append(u)
        self.indents.append(indent)
        return t

    def t_INDENT(self, t):
        r'\n+[ \t]*'
        # track line numbers
        nnl = t.value.count('\n')
        t.lexer.lineno += nnl
        #n = len(RE_LISTBULLET.split(t.value)[0])
        #t.value, bullet = t.value[:n], t.value[n:].strip()
        i = RE_INDENT.match(t.value).group(1)
        last = self.indents[-1]
        if i == last:
            # return if this basically text
            self._set_column(t)
            t.type = 'PLAINTEXT'
            #self._append_listbullet(bullet, t)
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
            self._lexer_error(t, "Indentation level doesn't match")
        #self._append_listbullet(bullet, t, nnl=nnl)
        return t

    text_breaks = '-\n#`${}%*~_:' + ''.join(k[0] for k in sorted(set(reserved.keys())))

    @ply.lex.TOKEN('[' + text_breaks + ']')
    def t_UNBREAKTEXT(self, t):
        self._set_column(t)
        t.type = 'PLAINTEXT'
        post = self.inp[t.lexpos:]
        m = RE_LISTBULLET.match(post)
        if m is None:
            # normal text, continue as planned
            return t
        # check if we are part of a nested list
        _, _, pre = self.inp[:t.lexpos].rpartition('\n')
        n = RE_BULLETS.match(pre)
        if n is None:
            # still normal text, continue as planned
            return t
        # we have a nested list!
        indent = self.indents[-1] + ' ' * len(n.group(2))
        t.type = 'LISTBULLET'
        self.indents.append(indent)
        self.queue.append(t)
        t.lexer.lexpos += 1  # skip over the space that follows the bullet
        s = ply.lex.LexToken()
        s.type = 'INDENT'
        s.value = indent
        s.lineno = t.lineno
        s.lexpos = t.lexpos
        s.column = t.column
        return s

    @ply.lex.TOKEN('[^' + text_breaks + ']+')
    def t_PLAINTEXT(self, t):
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

    _skip_trailing_ws = frozenset(['COMMENT', 'MULTILINECOMMENT',
                                   'CODEBLOCK', 'MULTILINEMATH'])

    def _next_token(self):
        """Obtain the next token"""
        # get token from current queue or lexer
        if self.queue:
            t = self.queue.popleft()
        else:
            t = self.lexer.token()
        # custom handling of certain tokens
        if t is None:
            pass
        elif t.type == 'PLAINTEXT':
            # merge text tokens
            next = self.queue.popleft() if self.queue else self.lexer.token()
            while next is not None and next.type == 'PLAINTEXT':
                t.value += next.value
                next = self.queue.popleft() if self.queue else self.lexer.token()
            self.queue.appendleft(next)
        elif t.type in self._skip_trailing_ws:
            # draw down whitespace after a comments, etc
            next = self.queue.popleft() if self.queue else self.lexer.token()
            while next is not None and (next.type == 'PLAINTEXT' and
                                        not next.value.strip()):
                next = self.queue.popleft() if self.queue else self.lexer.token()
            self.queue.appendleft(next)
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
            toks.extend(['DEDENT'])
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
