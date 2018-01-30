"""Syntax highlighting hooks for pygments"""
import re

from pygments.lexers import get_lexer_by_name
from pygments.lexer import RegexLexer, bygroups, using, this
from pygments.lexers.agile import PythonLexer
from pygments.lexers.markup import TexLexer
from pygments.token import (Punctuation, Keyword, Comment, Text, Operator,
    String, Escape, Generic, Literal, Name)
from pygments.util import ClassNotFound


class LeylineLexer(RegexLexer):
    """Pygments lexer leyline."""

    name = 'Leyline'
    aliases = ['leyline', 'ley']
    filenames = ['*.ley', '*.leyline']

    flags = re.DOTALL

    def codeblock_callback(lexer, match):
        """lexes based on code block"""
        g1 = match.group(1)
        givenlang, nl, code = g1.partition('\n')
        lang = givenlang if givenlang else 'python'
        start = match.start()
        yield start, String, '```'
        if givenlang:
            yield start + 3, Keyword.Namespace, givenlang
        # try to get a lexer for the language given
        try:
            sublexer = get_lexer_by_name(lang)
        except ClassNotFound:
            sublexer = None
        # lex as text is lexer not found, otherwise lex the lang
        offset = start + 3 + len(givenlang)
        yield offset, Text, '\n'
        offset += 1
        if sublexer is None:
            yield offset, Text, code
        else:
            for tokentype, value in sublexer.get_tokens(code):
                yield offset, tokentype, value
                offset += len(value)
        yield start + 3 + len(g1), String, '```'


    tokens = {
        'root': [
            # multiline comments
            (r'[#][#][#][^#\\]*(?:(?:\\.|[#](?![#][#][#]))[^[#]\\]*)*[#][#][#]',
             Comment.Multiline),
            # code blocks
            (r"```([^`\\]*(?:(?:\\.|`(?!``))[^`\\]*)*)```", codeblock_callback),
            # mutliline math
            (r"(\$\$\$)([^\$\\]*(?:(?:\\.|\$(?!\$\$))[^\$\\]*)*)(\$\$\$)",
             bygroups(String, using(TexLexer), String)),
            # singleline comment
            (r'[#][^\r\n]*', Comment),
            # inline code
            (r"(`)([^\n`\\]*(?:\\.[^\n`\\]*)*)(`)",
             bygroups(String, using(PythonLexer), String)),
            # inline math
            (r"(\$)([^\n\$\\]*(?:\\.[^\n\$\\]*)*)(\$)",
             bygroups(String, using(TexLexer), String)),
            # escape chars
            (r'{%}|{%|%}', String.Escape),
            # incorporeal macros
            (r'([{][{])(.*?)([}][}])',
             bygroups(String.Escape, using(PythonLexer), String.Escape)),
            # strikethrough
            (r'--.*?--', Generic.Deleted),
            # bold
            (r'\*\*.*?\*\*', Operator.Word),
            # italics
            (r'~~.*?~~', Name.Function),
            # underscore
            (r'__.*?__', Name.Class),
            # subscript
            (r'({_)(.*?)(_})', bygroups(Name.Class, Text, Name.Class)),
            # superscript
            (r'({\^)(.*?)(\^})', bygroups(Name.Class, Text, Name.Class)),
            # rend
            (r'(rend)((?: +[A-Za-z_][A-Za-z0-9_]*)+)(::)',
             bygroups(Keyword.Reserved, Name.Namespace, Operator)),
            # with
            ('(with)(| +[A-Za-z_][A-Za-z0-9_]*)(::)',
             bygroups(Keyword.Reserved, Name.Namespace, Operator), 'withblock'),
            # table
            (r'(table)(::)', bygroups(Keyword.Reserved, Operator), 'tableblock'),
            # figure
            (r'(figure)(::)', bygroups(Keyword.Reserved, Operator)),
            # list bullets
            (r'([ \t]*)((?:[-*]|\d+\.) )+', String.Escape),
            # plain text
            (r'[^\n#`${}%*^]+', Text),
            ],
        # go into python mode for with block
        'withblock': [
            (r'[^\n]+', using(PythonLexer)),
            (r'\n[ \t]+', Text),
            (r'\n[^ \t]', using(this), '#pop')
            ],
        # go into python mode for first part of table block
        'tableblock': [
            (r'[^\n]+', using(PythonLexer)),
            (r'\n[ \t]+[^*-]', using(PythonLexer)),
            (r'\n[ \t]+[*-] ', using(this), '#pop')
            ],
        }
