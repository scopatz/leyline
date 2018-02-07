Leyline
============================
Leyline is a markup language with the aim of supporting textual, audio, and visual rendering
targets from a single document. As with most markup languages, the twin goals of expressability
and power must be balanced. Currently, leyline can render into:

* PDFs
* Audio files (ogg, etc.)
* Videos (mp4), and
* ANSI escape sequence text for printing at the terminal.

We are open to building front ends from other languages, such as markdown, LaTeX, rst,
asciidoc, jinja, and others! Those languages would then have acces to the same great
renders already in leyline.

==================
Installation
==================
You can use ``conda`` or ``pip`` to install leyline. For example,


**conda**

.. code-block:: bash

    $ conda install -c conda-forge leyline

**pip**

.. code-block:: bash

    $ pip install leyline


===========
Quick Start
===========
First, open up and write a file called,

**test.ley**

.. code-block:: leyline

    with meta::
        title = 'On the Nature of Impure Lactose Solutions'
        author = 'Dr. Milk, Ph.D.'

    {{slide('Abstract')}}
    As with our simian servants, us cats can also be ~~lactose intolerant~~.
    While society may see this a socialy stigmatizing problem, it’s actually
    completely normal.
    {{subslide}}
    This work investigates a major potential alternative to
    traditional milk sources: __**cream**__. This study concludes that all felines
    should be given a limitless supply of cream, especially durring the
    crucial 1{^st^} year of life.
    {{subslide}}
    $$$
    S_{\mathrm{cream}} \to \infty
    $$$
    {{subslide}}
    Or computationally:
    ```python
    cream = 0.0
    while True:
        cream += 1.0
    ```


=========
Contents
=========
**Guides:**

.. toctree::
    :titlesonly:
    :maxdepth: 1

    usage


**Development Spiral:**

.. toctree::
    :titlesonly:
    :maxdepth: 2

    api/index
    devguide


============
Contributing
============
We highly encourage contributions to leyline! If you would like to contribute,
it is as easy as forking the repository on GitHub, making your changes, and
issuing a pull request.
See the `Developer's Guide <devguide.html>`_ for more information about contributing.

=============
Helpful Links
=============

* `Documentation <https://scopatz.github.io/leyline-docs>`_
* `GitHub Repository <https://github.com/scopatz/leyline>`_
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. raw:: html

    <a href="https://github.com/scopatz/leyline" class='github-fork-ribbon' title='Fork me on GitHub'>Fork me on GitHub</a>

    <style>
    /*!
     * Adapted from
     * "Fork me on GitHub" CSS ribbon v0.2.0 | MIT License
     * https://github.com/simonwhitaker/github-fork-ribbon-css
     */

    .github-fork-ribbon, .github-fork-ribbon:hover, .github-fork-ribbon:hover:active {
      background:none;
      left: inherit;
      width: 12.1em;
      height: 12.1em;
      position: absolute;
      overflow: hidden;
      top: 0;
      right: 0;
      z-index: 9999;
      pointer-events: none;
      text-decoration: none;
      text-indent: -999999px;
    }

    .github-fork-ribbon:before, .github-fork-ribbon:after {
      /* The right and left classes determine the side we attach our banner to */
      position: absolute;
      display: block;
      width: 15.38em;
      height: 1.54em;
      top: 3.23em;
      right: -3.23em;
      box-sizing: content-box;
      transform: rotate(45deg);
    }

    .github-fork-ribbon:before {
      content: "";
      padding: .38em 0;
      background-image: linear-gradient(to bottom, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.1));
      box-shadow: 0 0.07em 0.4em 0 rgba(0, 0, 0, 0.3);'
      pointer-events: auto;
    }

    .github-fork-ribbon:after {
      content: attr(title);
      color: #000;
      font: 700 1em "Helvetica Neue", Helvetica, Arial, sans-serif;
      line-height: 1.54em;
      text-decoration: none;
      text-align: center;
      text-indent: 0;
      padding: .15em 0;
      margin: .15em 0;
      border-width: .08em 0;
      border-style: dotted;
      border-color: #777;
    }

    </style>
