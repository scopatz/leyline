"""Syntax highlighting hooks for pygments"""
import re

from pygments.lexers import get_lexer_by_name
from pygments.lexer import RegexLexer, bygroups, using
from pygments.lexers.agile import PythonLexer
from pygments.token import Punctuation, Keyword, Comment, Text, Operator, String
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
            (r'[#][#][#][^#\\]*(?:(?:\\.|[#](?![#][#][#]))[^[#]\\]*)*[#][#][#]',
             Comment.Multiline),
            (r"```([^`\\]*(?:(?:\\.|`(?!``))[^`\\]*)*)```", codeblock_callback),
            (r'[^\n]+', Text),
            ],
    }
