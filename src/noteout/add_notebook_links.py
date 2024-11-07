#!/usr/bin/env python3
""" Panflute filter to write notebook downloads and associated links

See ``mark_notebooks.py`` for the overall structure of processing.

This is the last of the three processing steps for notebooks.

In this step, work out which notebooks have data files associated, write out
zips for download of notebooks with data files, and drop interact and download
links into the originating document.   (We have to do this last step separately
because we don't know what the download links should link to until we know
whether the notebooks have data files, and should therefore be ``.zip``
download links instead of notebook download links).

* The notes should suitably create Interact and Download buttons or the LaTeX
  URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
"""

from pathlib import Path

import panflute as pf

from noteout.nutils import FilterError, fmt2fmt

_REQUIRED_NOTEOUT_KEYS = ('book-url-root', 'nb-dir', 'nb-format')
_REQUIRED_MARKER_KEYS = ('name', 'title')


def prepare(doc):
    params = doc.get_metadata('noteout', {})
    for key in _REQUIRED_NOTEOUT_KEYS:
        if not key in params:
            raise FilterError(f'noteout.{key} must be defined in metadata')
    if params.get('url-nb-suffix') is None:
        params['url-nb-suffix'] = '.' + params.get('nb-format', 'ipynb')
    doc._params = params


def finalize(doc):
    del doc._params


def get_process_nb(elem, doc):
    return Path('foo.ipynb')


def get_nb_links(elem, doc, dl_suffix):
    params = doc._params.copy()
    params.update(elem.attributes)
    if doc.get_metadata('quarto-doc-params.out_format') == 'html':
        txt = '''\
<div class="nb-links">
<a class="notebook-link" href="{nb-dir}/{name}.{nb-format}">Download notebook</a>
<a class="interact-button" href="{interact-url}{name}{url-nb-suffix}">Interact</a>\n')
</div>'''.format(**params)
    else:  # Generic format.
        txt = '''\
* [Download notebook]({book-url-root}/{nb-dir}/{name}.{nb-format})
* [Interact]({book-url-root}{interact-url}{name}{url-nb-suffix})
'''.format(**params)
    return fmt2fmt(txt, out_fmt='panflute').content


def action(elem, doc):
    if not isinstance(elem, pf.Div) or 'nb-start' not in elem.classes:
        return
    for key in _REQUIRED_MARKER_KEYS:
        if not key in elem.attributes:
            raise FilterError(f'{key} must be defined in nb-start element')
    nb_pth = get_process_nb(elem, doc)
    elem.content = (list(elem.content) +
                    list(get_nb_links(elem, doc, nb_pth.suffix)))
    return elem
