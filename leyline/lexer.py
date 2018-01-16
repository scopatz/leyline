"""The leyline language lexer."""
from collections import deque

import ply.lex


class Lexer(object):

    _tokens = None

    # lexing happens in order of precedence in the file.

    def t_MULTILINECOMMENT(self, t):
        r"[^#\\]*(?:(?:\\.|[#](?![#][#][#]))[^[#]\\]*)*[#][#][#]"
        t.value = t.value[3:-3]
        return t

    def t_CODEBLOCK(self, t):
        r"[^`\\]*(?:(?:\\.|`(?!``))[^`\\]*)*```"
        lang, _, block = t.value[3:-3].partition('\n')
        t.value = (lang.strip(), block.strip())
        return t

    def t_MULTILINEMATH(self, t):
        r"[^\$\\]*(?:(?:\\.|\$(?!\$\$))[^\$\\]*)*\$\$\$"
        t.value = t.value[3:-3]
        return t

    def t_COMMENT(self, t):
        r'[#][^\r\n]*'
        t.value = t[1:].strip()
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
        r'**'
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

    @ply.lex.TOKEN(r'(' + '|'.join(reserved.keys()) + ')')
    def t_RESERVED(self, t):
        r'(' + '|'.join()
        t.type = self.reserved.get(t.value, 'RESERVED')
        return t

    def t_TEXT(self, t):
        r'.*?'
        return t

    def t_INDENT(self, t):
        r'\n[ \t]*'
        # track line numbers
        t.lexer.lineno += 1
        i = t.value = t.value[1:]
        last = self.indents[-1]
        if i == last:
            t.lexer.skip(1)
            return
        elif len(i) > len(last) and i.startswith(last):
            self.indents.append(i)
            return t
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
            return t
        else:
            raise SyntaxError("Indentation level doesn't match " + str(t))

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def t_eof(self, t):
        """Handle end of file conditions"""
        if len(self.indents) > 1:
            # dedent the world at the end of the file.
            t.lexer.input('\n')
            return t.lexer.token()

    def reset(self):
        self.queue = deque()
        self.indents = ['']

    def build(self, **kwargs):
        """Build the lexer"""
        self.reset()
        self.lexer = ply.lex.lex(module=self, **kwargs)

    def token(self):
        """Obtain the next token"""
        if self.queue:
            return self.queue.popleft()
        return self.lexer.token()

    @property
    def tokens(self):
        if self._tokens is None:
            toks = [t[2:] for t in dir(self) if t.startswith('t_') and t[2:].upper() == t[2:]]
            toks.extend(self.reserved.values())
            toks.append('DEDENT')
            self._tokens = tuple(toks)
        return self._tokens
