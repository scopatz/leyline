"""Tools for rendering audio from a document."""
import os
import sys
import queue
import shutil

from lazyasd import lazyobject

from leyline.ast import indent, AnsiFormatter, Visitor
from leyline.context_visitor import ContextVisitor


@lazyobject
def np():
    import numpy
    return numpy


@lazyobject
def sd():
    import sounddevice
    return sounddevice


@lazyobject
def sf():
    import soundfile
    return soundfile


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


class Dictation(ContextVisitor, AnsiFormatter):
    """A context visitor that renders the document by recording audio from the
    microphone. Audio is chunked into small blocks and cached for later use.
    Users should only need to record a certain block once.
    """

    renders = 'audio'

    def render(self, *, tree=None, assets=None, assets_dir='.', **kwargs):
        """Takes a dictation of the text and returns a list of filenames that
        represent the text.
        """
        if assets is None:
            raise ValueError('assets cannot be None, must be an isnstance '
                             'of AssetsCache')
        self.blocks = ['']
        self.visit(tree)
        filenames = []
        for block in self.blocks:
            filename = self.record_block(block, assets, assets_dir)
            if filename is None:
                # recieved quit
                return
            filenames.append(filename)
        return filenames

    def record_block(self, block, assets, assets_dir):
        """Interactively records a block, returns the file name"""
        # first check if we already have a recording
        asset_key = ('dictation', block)
        if asset_key in assets:
            filename = assets[asset_key]
            print('found \x1b[1m' + filename + '\x1b[0m in cache')
            assets[assets_key] = filename  # update src hash
            return filename
        # now make sure we can record
        if not hasattr(self, 'recorder'):
            self.recorder = Recorder()
        basename = h + '.ogg'
        filename = os.path.join(assets_dir, basename)
        done = False
        while not done:
            print('Please speak the following text; '
                  'press Enter to start recording\n\n')
            print(block, '\n\n')
            input()
            self.recorder.record(filename)
            print('would you like to \x1b[1m(k)\x1b[0meep or '
                  '\x1b[1m(d)\x1b[0miscard this recording: ')
            s = None
            while not s:
                if s is not None:
                    print('selection not understood, please input k/d or y/n or q')
                s = input()[0].lower()
                if s not in 'kdynq':
                    continue
                elif s in 'ky':
                    done = True
                elif s == 'q':
                    return
                else:
                    s = ''
                    done = False
        assets[asset_key] = filename
        return filename

    def append(self, s):
        """Adds a string to the last block"""
        self.blocks[-1] += s

    def append_paragraphs(self, s):
        # split paragraphs into separate blocks
        paragraphs = s.split('\n\n')
        self.append(paragraphs.pop(0))
        self.blocks.extend(paragraphs)

    def visit_textblock(self, node):
        s = self._bodied_visit(node)
        self.append_paragraphs(s)
        return s

    def visit_document(self, node):
        self.blocks = ['']
        self._bodied_visit(node)
        for i in range(len(self.blocks) - 1, -1, -1):
            block = self.blocks[i].strip()
            if block:
                # put the stripped version back in
                self.blocks[i] = block
            else:
                # remove empty blocks
                del self.blocks[i]
        return self.blocks

    def visit_renderfor(self, node):
        if self.renders not in node.targets:
            return ''
        return self._bodied_visit(node)

    def visit_comment(self, node):
        return ''

    def visit_with(self, node):
        super().visit_with(node)
        return ''

    def visit_incorporealmacro(self, node):
        s = super().visit_incorporealmacro(node)
        return s

    def visit_list(self, node):
        for bullet, item in node:
            s = '\u001b[32;1m'
            s += bullet if isinstance(bullet, str) else str(bullet) + '.'
            s += '\u001b[0m '
            self.blocks.append(s)
            for i in item:
                self.visit(i)
            self.append('\n')
        self.blocks.append('')
        return ''

    def visit_figure(self, node):
        s = 'figure:: ' + node.path + '\n' + node.caption
        return s


class Recorder:
    """Manages the recording of audio."""

    def __init__(self, device=None, channels=1, columns=None, fft_low=100.0,
                 fft_high=2000.0, gain=10.0, block_duration=0.05):
        """
        Parameters
        ----------
        device : int, optional
            The audio input device to use. If None, the user will be prompted
            for a selection.
        channels : int, optional
            Number of channels to record, default 1.
        columns : int, optional
            Numbetr of columns to display the FFT with. Defaults to current
            terminal column width.
        fft_low : float, optional
            Lower bound frequency [Hz] for FFT.
        fft_high : float, optional
            Upper bound frequency [Hz] for FFT.
        gain : int, optional
            FFT gain factor to apply.
        block_duration : float, optional
            The length of time [sec] that each recorded block should be.
        """
        self._gradient = self._samplerate = self.fft_size = None
        if columns is None:
            columns = shutil.get_terminal_size().columns
        self.columns = columns
        self.fft_low = fft_low
        self.fft_high = fft_high
        self.gain = gain
        self.block_duration = block_duration
        self.blocks = None
        self.channels = channels

        self.delta_f = (fft_high - fft_low) / (columns - 1)
        self.low_bin = int(np.floor(fft_low / self.delta_f))

        self._device = device
        self.device = device

    @property
    def gradient(self):
        if self._gradient is not None:
            return self._gradient
        #from https://gist.github.com/maurisvh/df919538bcef391bc89f
        template = '\x1b[{};{}m{}'
        colors = 30, 34, 35, 91, 93, 97
        chars = ':%#'
        self._gradient = gradient = []
        for bg, fg in zip(colors, colors[1:]):
            # add a blank space to start
            gradient.append('\x1b[{};{}m{}'.format(fg, bg + 10, ' '))
            # add forward colors
            for char in chars:
                gradient.append('\x1b[{};{}m{}'.format(fg, bg + 10, char))
            # reverse colors and switch fg, bg
            for char in reversed(chars):
                gradient.append('\x1b[{};{}m{}'.format(bg, fg + 10, char))
        return gradient

    @property
    def device(self):
        """The input """
        if self._device is None:
            d = self.device
        return self._device

    @device.setter
    def device(self, val):
        if val is None:
            info = str(sd.query_devices())
            if 'linux' in sys.platform:
                info = '\n'.join(line for line in info.splitlines() if '(0 in' not in line)
            if not info.strip():
                print('\x1b[1mNo available input devices!\x1b[0m')
                #self._device = self._samplerate = self.fft_size = None
                return
            print('Please select a mircophone.\n\x1b[1mAvailable Input Devices:\x1b[0m')
            print(info)
        while val is None:
            print('device number: ', end='', flush=True)
            s = input()
            try:
                val = int(s)
            except ValueError:
                print('please use an integer to select the input device.')
        self._samplerate = self.fft_size = None
        self._device = val

    @property
    def samplerate(self):
        """The sample rate for the selected input device"""
        if self._samplerate is None:
            sr = sd.query_devices(self.device, 'input')['default_samplerate']
            self._samplerate = sr
            self.fft_size = int(np.ceil(sr / self.delta_f))
        return self._samplerate

    def callback(self, indata, frames, time, status):
        """Callback for recording via sounddevice and displaying the spectrum as the
        recording streams.
        """
        if status:
            text = ' ' + str(status) + ' '
            print('\x1b[34;40m', text.center(self.columns, '#'),
                  '\x1b[0m', sep='', end='\r', flush=True)
        if any(indata):
            self.blocks.put(indata.copy())
            magnitude = np.abs(np.fft.rfft(indata[:, 0], n=self.fft_size))
            magnitude *= self.gain / self.fft_size
            line = (self.gradient[int(np.clip(x, 0, 1) * (len(self.gradient) - 1))]
                    for x in magnitude[self.low_bin:self.low_bin + self.columns])
            print(*line, sep='', end='\x1b[0m\r', flush=True)
        else:
            print('no input', end='\r', flush=True)

    def raw_record(self):
        """Actually records from the microphone. Returns a queue of numpy arrays."""
        self.blocks = queue.Queue()
        print('Press Enter to stop recording.')
        with sd.InputStream(device=self.device, channels=1, callback=self.callback,
                            blocksize=int(self.samplerate * self.block_duration),
                            samplerate=self.samplerate):
            response = True
            while response:
                response = input()
        return self.blocks

    def record(self, filename):
        """Records sounds and writes it to the filesystem."""
        blocks = self.raw_record()
        print('Writing file \x1b[1m' + filename + '\x1b[0m')
        with sf.SoundFile(filename, mode='w', samplerate=int(self.samplerate),
                          channels=self.channels, subtype='VORBIS') as f:
            while not blocks.empty():
                block = blocks.get()
                f.write(block)

