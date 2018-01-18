"""The leyline language lexer."""
import re
from textwrap import dedent
from collections import deque

import ply.lex


class Lexer(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.build(**kwargs)

    # lexing happens in order of precedence in the file.

    def t_MULTILINECOMMENT(self, t):
        r"[#][#][#][^#\\]*(?:(?:\\.|[#](?![#][#][#]))[^[#]\\]*)*[#][#][#]"
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value[3:-3]
        return t

    def t_CODEBLOCK(self, t):
        r"```[^`\\]*(?:(?:\\.|`(?!``))[^`\\]*)*```"
        t.lexer.lineno += t.value.count('\n')
        lang, _, block = t.value[3:-3].partition('\n')
        t.value = (lang.strip(), dedent(block))
        return t

    def t_MULTILINEMATH(self, t):
        r"\$\$\$[^\$\\]*(?:(?:\\.|\$(?!\$\$))[^\$\\]*)*\$\$\$"
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value[3:-3]
        return t

    def t_COMMENT(self, t):
        r'[#][^\r\n]*'
        t.value = t.value[1:].strip()
        return t

    def t_INLINECODE(self, t):
        r"`([^\n`\\]*(?:\\.[^\n`\\]*)*)`"
        t.value = t.value[1:-1]
        return t

    def t_INLINEMATH(self, t):
        r"\$([^\n\$\\]*(?:\\.[^\n\$\\]*)*)\$"
        t.value = t.value[1:-1]
        return t

    def t_LBRACEPERCENTRBRACE(self, t):
        r'{%}'
        return t

    def t_LBRACEPERCENT(self, t):
        r'{%'
        return t

    def t_PERCENTRBRACE(self, t):
        r'%}'
        return t

    def t_DOUBLELBRACE(self, t):
        r'{{'
        return t

    def t_DOUBLERBRACE(self, t):
        r'}}'
        return t

    def t_DOUBLEDASH(self, t):
        r'--'
        return t

    def t_DOUBLESTAR(self, t):
        r'\*\*'
        return t

    def t_DOUBLETILDE(self, t):
        r'~~'
        return t

    def t_DOUBLEUNDER(self, t):
        r'__'
        return t

    def t_COLON(self, t):
        r':'
        return t

    reserved = {
        'rend': 'REND',
        'with': 'WITH',
        'table': 'TABLE',
        }

    @ply.lex.TOKEN(r'(' + '|'.join(sorted(reserved.keys())) + ')')
    def t_RESERVED(self, t):
        t.type = self.reserved.get(t.value, 'RESERVED')
        return t

    def t_INDENT(self, t):
        r'\n+[ \t]*'
        # track line numbers
        t.lexer.lineno += t.value.count('\n')
        i = t.value.lstrip('\n')
        last = self.indents[-1]
        if i == last:
            # return if this basically text
            t.type = 'TEXT'
            return t
        # now we know we have an indent or a dedent
        t.lineno = t.lexer.lineno
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
        t.type = 'TEXT'
        return t

    @ply.lex.TOKEN('[^' + text_breaks + ']+')
    def t_TEXT(self, t):
        t.lexer.lineno += t.value.count('\n')
        return t

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)
        #t.type = 'TEXT'
        #return t

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
            self.queue.append(dedent)
            del self.indents[-1]
            last = self.indents[-1]
        return self.token()

    def input(self, s):
        return self.lexer.input(s)

    def reset(self):
        self.queue = deque()
        self.indents = ['']

    def build(self, **kwargs):
        """Build the lexer"""
        self.reset()
        self.lexer = ply.lex.lex(module=self, reflags=re.DOTALL, **kwargs)

    def token(self):
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
            toks.extend(self.reserved.values())
            toks.append('DEDENT')
            self._tokens = tuple(toks)
        return self._tokens
