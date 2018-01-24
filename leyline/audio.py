"""Tools for rendering audio from a document."""
import os
import sys

from leyline.context_visitor import ContextVisitor


class SSML(ContextVisitor):
    """Renders an AST as Speech Synthesis Markup Language (SSML).
    Visiting this will return a list of SSML strings, broken up by
    paragraph in the document.
    """

    renders = 'audio'

    def render(self, *, tree=None, filename='', polly_user=None, **kwargs):
        """Performs the actual render, putting the notes file on disk."""
        blocks = self.visit(tree)
        basename, _ = os.path.splitext(filename)
        outfile = basename + '.mp3'
        self._render_with_polly(blocks, outfile, polly_user)

    def _render_with_polly(self, blocks, outfile, user):
        from boto3 import Session
        from botocore.exceptions import BotoCoreError, ClientError
        session = Session(profile_name=user)
        polly = session.client("polly")
        nblocks = len(blocks)
        aud = b''
        for i, ssml in enumerate(blocks):
            print('{0}/{1}\r'.format(i, nblocks), end='')
            sys.stdout.flush()
            response = polly.synthesize_speech(Text=ssml,
                                               TextType='ssml',
                                               VoiceId='Matthew',
                                               OutputFormat='mp3')
            aud += response["AudioStream"].read()
        with open(outfile, 'bw') as f:
            f.write(aud)
        print('Done... ' + outfile)

    def _bodied_visit(self, node):
        """Visits each subnode in the body of the given node."""
        s = ''.join(map(self.visit, node.body))
        return s

    visit_textblock = _bodied_visit
    visit_underline = _bodied_visit
    visit_superscript = _bodied_visit

    def visit_document(self, node):
        s = self._bodied_visit(node)
        # break up by paragraph
        blocks = s.split('\n\n')
        for i in range(len(blocks)):
            blocks[i] = '<speak>' + blocks[i] + '<break time="0.3s" /></speak>'
        return blocks

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
        s = '\n\n'
        for i, (bullet, item) in enumerate(zip(bullets, node.items), 1):
            if i == n:
                s += ' and '
            if isinstance(bullet, int):
                s += str(bullet) + ' <break strength="weak"/> '
            s += ''.join(map(self.visit, item)) + ' <break strength="strong"/> '
        s += '\n\n'
        return s

    def visit_with(self, node):
        super().visit_with(node)
        return ''
