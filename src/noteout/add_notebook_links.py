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
import re
import zipfile

import jupytext as jpt
import panflute as pf

from noteout.nutils import FilterError, fmt2fmt

_REQUIRED_NOTEOUT_KEYS = ('book-url-root', 'nb-dir', 'nb-format')
_REQUIRED_MARKER_KEYS = ('name', 'title')

# Find data read
READ_RE = re.compile(
    r'''^\s*
    \w+\s*(=|<-)\s*
    (pd\.)*read[._]\w+\(
    ['"]
    (?P<fname>.*?)
    ['"]
    \)
    ''',
    flags=re.MULTILINE | re.VERBOSE)



def prepare(doc):
    params = doc.get_metadata('noteout', {})
    for key in _REQUIRED_NOTEOUT_KEYS:
        if not key in params:
            raise FilterError(f'noteout.{key} must be defined in metadata')
    if params.get('url-nb-suffix') is None:
        params['url-nb-suffix'] = '.' + params.get('nb-format', 'ipynb')
    params['interact-url'] = '/' + params['interact-url'].strip('/')
    qdp = doc.get_metadata('quarto-doc-params', {})
    params['out_format'] = qdp.get('out_format')
    params['out_path'] = Path(qdp.get('output_directory', '.'))
    params['nb_out_path'] = params['out_path'] / params['nb-dir']
    doc._params = params


def finalize(doc):
    del doc._params


def find_data_files(nb):
    """ Detect data files read within notebook

    Parameters
    ----------
    nb : dict
        Notebook.

    Returns
    -------
    out_files : list
        List of detected filenames.  These will be relative to the path assumed
        by the `nb`.
    """
    out_fnames = []
    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue
        for m in READ_RE.finditer(cell['source']):
            out_fnames.append(m.groups()[-1])
    return sorted(set(out_fnames))


def write_data_files(in_path, data_files, out_path):
    """ Write data files `data_files` to path `out_path`

    Parameters
    ----------
    in_path : :class:`Path`
        Directory containing input `data_files`.
    data_files : sequence of str
        Filenames giving paths to data files.
    out_path : :class:`Path`
        Output path.

    Returns
    -------
    out_paths : list
        List of Paths of written files.
    """
    out_paths = []
    for data_fname in data_files:
        data_out_path = out_path / data_fname
        data_out_path.parent.mkdir(parents=True, exist_ok=True)
        data_out_path.write_text((in_path / data_fname).read_text())
        out_paths.append(data_out_path)
    return out_paths


def write_zip(paths, out_path):
    out_zip_path = paths[0].with_suffix('.zip')
    with zipfile.ZipFile(out_zip_path, "w") as zf:
        for path in paths:
            zf.write(path, str(path.relative_to(out_path)))
    return out_zip_path


def get_make_dl(name, doc):
    p = doc._params
    out_path = p['nb_out_path']
    nb_path =  out_path / f'{name}.{p["nb-format"]}'
    if not nb_path.is_file():
        raise FilterError(f'"{nb_path}" does not exist')
    nb = jpt.reads(nb_path.read_text(), 'Rmd')
    if (dfs := find_data_files(nb)):
        out_data_files = write_data_files(Path(), dfs, out_path)
        return write_zip([nb_path] + out_data_files, out_path), len(dfs)
    return nb_path, 0


def get_nb_links(elem, doc, dl_path, n_dfs):
    params = doc._params.copy()
    params.update(elem.attributes)
    out_dir = params['out_path']
    params['dl_fname'] = str(dl_path.relative_to(out_dir))
    params['dl_txt'] = ('notebook' if n_dfs == 0 else
                        ('zip with notebook + data file' +
                         ('s' if n_dfs > 1 else '')))
    params['inter_url'] = ('{interact-url}{name}{url-nb-suffix}'
                           .format(**params))
    if doc.get_metadata('quarto-doc-params.out_format') == 'html':
        txt = '''\
<div class="nb-links">
<a class="notebook-link" href="{dl_fname}">Download {dl_txt}</a>
<a class="interact-button" href="{inter_url}">Interact</a>\n')
</div>'''.format(**params)
    else:  # Generic format.
        txt = '''\
* [Download notebook]({book-url-root}/{dl_fname})
* [Interact]({book-url-root}{inter_url})
'''.format(**params)
    return fmt2fmt(txt, out_fmt='panflute').content


def action(elem, doc):
    if not isinstance(elem, pf.Div) or 'nb-start' not in elem.classes:
        return
    for key in _REQUIRED_MARKER_KEYS:
        if not key in elem.attributes:
            raise FilterError(f'{key} must be defined in nb-start element')
    dl_path, n_dfs = get_make_dl(elem.attributes['name'], doc)
    elem.content = (list(elem.content) +
                    list(get_nb_links(elem, doc, dl_path, n_dfs)))
    return elem
