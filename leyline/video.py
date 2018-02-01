"""Tools for rendering leyline ASTs as video"""
import os
import re
import tempfile
import itertools
import subprocess

from lazyasd import lazyobject

from leyline.ast import Document
from leyline.latex import Latex
from leyline.audio import Dictation, append_to_track
from leyline.events import EventsVisitor, Slide


@lazyobject
def np():
    import numpy
    return numpy


@lazyobject
def sf():
    import soundfile
    return soundfile


@lazyobject
def RE_EMPTY_FRAME():
    return re.compile(r'\\begin{frame}\s*\\end{frame}', re.DOTALL)


HEADER = r"""
\documentclass[aspectratio=169]{beamer}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{booktabs} % nice rules for tables
\usepackage{microtype} % if using PDF
\usepackage{xspace}
\usepackage{listings}
\usepackage{textcomp}
\usepackage[normalem]{ulem}
\usepackage[export]{adjustbox}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{hyperref}
\DeclareMathAlphabet{\mathpzc}{OT1}{pzc}{m}{it}

\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=blue,
}

\definecolor{listinggray}{gray}{0.9}
\lstset{
    language={Python},
    tabsize=4,
    rulecolor=\color{black},
    upquote=true,
    aboveskip={1.5\baselineskip},
    belowskip={1.5\baselineskip},
    columns=fixed,
    extendedchars=true,
    breaklines=true,
    prebreak=\raisebox{0ex}[0ex][0ex]{\ensuremath{\hookleftarrow}},
    frame=single,
    showtabs=false,
    showspaces=false,
    showstringspaces=false,
    basicstyle=\scriptsize\ttfamily\color{green!40!black},
    keywordstyle=\color[rgb]{0,0,1.0},
    commentstyle=\color[rgb]{0.133,0.545,0.133},
    stringstyle=\color[rgb]{0.627,0.126,0.941},
    numberstyle=\color[rgb]{0,1,0},
    identifierstyle=\color{black},
    captionpos=t,
}

\usetheme{Warsaw}

\setbeamercolor{normal text}{fg=white,bg=black!90}
\setbeamercolor{structure}{fg=white}

\setbeamercolor{alerted text}{fg=red!85!black}

\setbeamercolor{item projected}{use=item,fg=black,bg=item.fg!35}

\setbeamercolor*{palette primary}{use=structure,fg=structure.fg}
\setbeamercolor*{palette secondary}{use=structure,fg=structure.fg!95!black}
\setbeamercolor*{palette tertiary}{use=structure,fg=structure.fg!90!black}
\setbeamercolor*{palette quaternary}{use=structure,fg=structure.fg!95!black,bg=black!80}

\setbeamercolor*{framesubtitle}{fg=white}

\setbeamercolor*{block title}{parent=structure,bg=black!60}
\setbeamercolor*{block body}{fg=black,bg=black!10}
\setbeamercolor*{block title alerted}{parent=alerted text,bg=black!15}
\setbeamercolor*{block title example}{parent=example text,bg=black!15}

\begin{document}
\begin{frame}
"""

FOOTER = r"""
\end{frame}
\end{document}
"""


def linkpath(path):
    """finds a path to link in, whether it is a file or a directory."""
    d, p = os.path.split(path)
    if not d:
        # must be a file, since no directory
        return path
    # find top-most directory
    while d:
        d, p = os.path.split(d)
    return p


class Frame(Latex):
    """Renders a video frame via the LaTeX Beamer package."""

    renders = 'video'

    def render(self, *, tree=None, assets=None, assets_dir='.', title=None,
               **kwargs):
        """Renders a single 1080p frame of video as a jpg via LaTeX.
        Returns the filename.
        """
        self.title = title
        self.linkpaths = []
        s = self.visit(tree)
        asset_key = ('frame', s)
        if asset_key in assets:
            filename = assets[asset_key]
            print('found \x1b[1m' + filename + '\x1b[0m in cache')
            assets[asset_key] = filename  # update src hash
            return filename
        h = assets.hash(asset_key)
        basename = h + '.jpg'
        filename = os.path.join(assets_dir, basename)
        with tempfile.TemporaryDirectory(prefix='frame-' + h) as d:
            # create symlinks
            for linkpath in self.linkpaths:
                os.symlink(os.path.abspath(linkpath), os.path.join(d, linkpath),
                           target_is_directory=os.path.isdir(linkpath))
            # write tex
            texname = os.path.join(d, h + '.tex')
            with open(texname, 'w') as f:
                f.write(s)
            subprocess.check_call(['pdflatex', texname], cwd=d)
            pdfname = os.path.join(d, h + '.pdf')
            subprocess.check_call([
                'gs', '-dNOPAUSE', '-sDEVICE=jpeg', '-dFirstPage=1',
                '-dLastPage=1', '-sOutputFile=' + filename,
                '-dJPEGQ=100', '-dFIXEDMEDIA', '-dPDFFitPage', '-g1920x1080',
                '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4',
                '-q', pdfname, '-c', 'quit'])
        assets[asset_key] = filename
        return filename

    def _make_title(self):
        title = getattr(self, 'title', None)
        if title is None:
            return ''
        return '\\frametitle{' + title + '}\n'

    def visit_document(self, node):
        body = super().visit_document(node)
        s = HEADER + self._make_title() + body + FOOTER
        return s

    def visit_figure(self, node):
        rtn = super().visit_figure(node)
        if os.path.isabs(node.path):
            pass
        else:
            self.linkpaths.append(linkpath(node.path))
        return rtn


class Slides(Latex):
    """Renders a slide deck via the LaTeX Beamer package. This is used for previewing
    how the video will look.
    """

    renders = 'slides'

    def render(self, *, tree=None, filename=None, **kwargs):
        """Renders the slide deck and returns the filename.
        """
        s = self.visit(tree)
        basename, _ = os.path.splitext(filename)
        texfile = basename + '-slides.tex'
        pdffile = basename + '-slides.pdf'
        with open(texfile, 'w') as f:
            f.write(s)
        subprocess.check_call(['pdflatex', texfile])
        return pdffile

    def visit_document(self, node):
        body = super().visit_document(node)
        s = HEADER + body + FOOTER
        s = RE_EMPTY_FRAME.sub('', s)
        return s


class Video(EventsVisitor):
    """Renders a movie for a tree."""

    renders = 'video'

    def render(self, *, tree=None, filename='', assets=None, assets_dir='.',
               **kwargs):
        """Renders a movie, with synced up audio!"""
        self.visit(tree)  # fill events
        slides = [event for event in self.events if isinstance(event, Slide)]
        basename, _ = os.path.splitext(filename)
        oggfile = self.render_audio(slides, basename, assets, assets_dir)
        if oggfile is None:
            return
        frames = self.render_frames(slides, assets, assets_dir)
        mp4file = self.render_video(slides, basename, oggfile, frames)
        return mp4file

    def render_audio(self, slides, basename, assets, assets_dir):
        """Renders the audio track for a slide. Returns the path
        to the audio file.
        """
        dictation = getattr(self, 'dictation', None)
        if dictation is None:
            dictation = self.dictation = Dictation(contexts=self.contexts)
        samplerate = int(dictation.recorder.samplerate)
        channels = 2
        parbreakdur = 1.3  # number of seconds to break between paragraphs
        parbreak = np.zeros((int(samplerate*parbreakdur), channels), dtype='float64')
        oggfile = basename + '.ogg'
        track = sf.SoundFile(oggfile, 'w', samplerate=samplerate,
                             channels=channels, format='OGG', subtype='VORBIS')
        clock = 0.0
        # record audio for slides by recording audio for subslides
        for slide in slides:
            for i, subslide in enumerate(slide.body):
                dur = 0.0
                if not subslide:
                    continue
                slide.start[i] = clock
                n0 = subslide[0]
                subdoc = Document(body=subslide, lineno=n0.lineno,
                                  column=n0.column)
                files = dictation.render(tree=subdoc, assets=assets,
                                         assets_dir=assets_dir)
                if files is None:
                    return
                for fname in files:
                    dur += append_to_track(track, fname)
                    track.write(parbreak)
                    dur += parbreakdur
                # the following must come at the very end of every subslide
                slide.duration[i] = dur
                clock += dur
        track.flush()
        track.close()
        return oggfile

    def render_frames(self, slides, assets, assets_dir):
        """Render each frame and return a list of list of filename
        matching the slide/subslide arrangement.
        """
        framer = getattr(self, 'framer', None)
        if framer is None:
            framer = self.framer = Frame(contexts=self.contexts)
        # render the actual frames
        slidesframes = []
        for slide in slides:
            slideframes = []
            slidesframes.append(slideframes)
            body = []
            for i, subslide in enumerate(slide.body):
                if not subslide:
                    slideframes.append(None)
                    continue
                body.extend(subslide)
                n0 = body[0]
                subdoc = Document(body=body, lineno=n0.lineno,
                                  column=n0.column)
                fname = framer.render(tree=subdoc, assets=assets,
                                      assets_dir=assets_dir, title=slide.title)
                slideframes.append(fname)
        return slidesframes

    def render_video(self, slides, basename, oggfile, frames):
        """Renders video from slide timings, an audio file, and frame files."""
        s = 'ffconcat version 1.0\n'
        t = 'file {0}\nduration {1}\n'
        for slide, framelist in zip(slides, frames):
            itr = zip(slide.body, slide.start, slide.duration, framelist)
            for subslide, start, duration, frame in itr:
                if not subslide:
                    continue
                s += t.format(frame, duration)
        s += 'file ' + frame + '\n'  # need to copy last frame to prevent cutoff
        # write the ffmpeg concat demuxer file
        ffconcat = basename + '.ffconcat'
        with open(ffconcat, 'w') as f:
            f.write(s)
        # render the video with ffmpeg
        mp4file = basename + '.mp4'
        subprocess.check_call(['ffmpeg', '-y', '-i', ffconcat, '-i', oggfile,
                               '-vf', 'fps=24', '-shortest', mp4file])
        return mp4file
