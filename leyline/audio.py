"""Tools for rendering audio from a document."""
from leyline.context_visitor import ContextVisitor


class SSML(ContextVisitor):
    """Renders an AST as Speech Synthesis Markup Language (SSML)"""

    renders = 'audio'

    def _bodied_visit(self, node):
        """Visits each subnode in the body of the given node."""
        s = ''.join(map(self.visit, node.body))
        return s

    visit_document = _bodied_visit
    visit_textblock = _bodied_visit
    visit_underline = _bodied_visit
    visit_superscript = _bodied_visit

    def visit_bold(self, node):
        s = '<emphasis level="strong">'
        s += self._bodied_visit(node)
        s += '</emphasis>'
        return s

    def visit_italics(self, node):
        s = '<emphasis level="moderate">'
        s += self._bodied_visit(node)
        s += '</emphasis>'
        return s

    def visit_strikethrough(self, node):
        s = ' <emphasis level="strong">not</emphasis> '
        s += self._bodied_visit(node)
        return s

    def visit_subscript(self, node):
        s = ' <emphasis level="strong">sub</emphasis> '
        s += self._bodied_visit(node)
        return s

    def visit_renderfor(self, node):
        if self.renders not in node.targets:
            return ''
        return self._bodied_visit(node)

    def _speak_text(self, node):
        return node.text

    visit_plaintext = _speak_text
    visit_inlinecode = _speak_text
    visit_inlinemath = _speak_text

    def _dont_speak(self, node):
        return ''

    visit_comment = _dont_speak
    visit_codeblock = _dont_speak
    visit_equation = _dont_speak

    def visit_list(self, node):
        n = len(node.items)
        if isinstance(node.bullets, str):
            bullets = [node.bullets] * n
        elif isinstance(node.bullets, str):
            bullets = range(1, n+1)
        else:
            bullets = node.bullets
        s = ''
        for i, (bulllet, item) = enumerate(zip(bullets, node.items), 1):
            if i == n:
                s += ' and '
            if isinstance(bullet, int):
                s += str(bullet) + ' <break strength="weak"/> '
            s += self.visit(item) + ' <break strength="strong"/> '
        return s
