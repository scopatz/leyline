"""The leyline language lexer."""

import ply.lex


class Lexer(object):

    tokens = (
        'CODEBLOCK',
        'COMMENT',
        'INLINECODE',
        'INLINEMATH',
        'MULTILINECOMMENT',
        'MULTILINEMATH',
    )

    def t_CODEBLOCK(self, t):
        r"[^`\\]*(?:(?:\\.|`(?!``))[^`\\]*)*```"
        lang, _, block = t.value[3:-3].partition('\n')
        t.value = (lang.strip(), block.strip())
        return t

    t_COMMENT = r'#[^\r\n]*'
    t_COLON = r':'

    def t_INLINECODE(self, t):
        r"`([^\n`\\]*(?:\\.[^\n`\\]*)*)`"
        t.value = t.value[1:-1]
        return t

    def t_INLINEMATH(self, t):
        r"\$([^\n\$\\]*(?:\\.[^\n\$\\]*)*)\$"
        t.value = t.value[1:-1]
        return t

    t_MULTILINECOMMENT = r"[^#\\]*(?:(?:\\.|#(?!###))[^#\\]*)*###"

    def t_MULTILINEMATH(self, t):
        r"[^\$\\]*(?:(?:\\.|\$(?!\$\$))[^\$\\]*)*\$\$\$"
        t.value = t.value[3:-3]
        return t

    t_WITH = r'with'

    def t_newline(self, t):
        r'\n+'
        # track line numbers
        t.lexer.lineno += len(t.value)

    # ignored characters
    t_ignore  = ' \t'

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = ply.lex.lex(module=self, **kwargs)
