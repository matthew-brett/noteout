#!/usr/bin/env python3
""" Panflute filter to detect, process and write notebooks.

See ``mark_notebooks.py`` for the overall structure of processing.

This is the second of the two processing steps for notebooks.

In this step, we parse the start and end markers to find the notebooks, then
write out the notebook files after suitable processing.

The suitable processing is:

* Fix up callout blocks
* Flatten any divspans that need flattening (see `strip_cells`)
* Drop comment marks before and after notebooks.
* Output to Github Flavored Markdown.
* If there are data files read in the notebook, also:
    * Copy data files to notebook output directory.
    * Make a zip file for notebook with read data files.

We detect notebooks simply by starting notebooks after a start marker, and
finishing before the end marker, using a search through the top level of tree,
and any divs contained therein.
"""

from pathlib import Path
import re
import zipfile

import jupytext as jpt
import panflute as pf
from panflute import Str, Strong, Space

from noteout.nutils import (is_div_class, FilterError, name2title, fmt2fmt,
                            fill_params, find_data_files)

_REQUIRED_NOTEOUT_KEYS = ()

FENCE_START_RE = re.compile(r'^```\s*(\w+)$', re.MULTILINE)

# Stuff inside HTML (and Markdown) comment markers.
COMMENT_RE = re.compile(r'<!--.*?-->', re.MULTILINE | re.DOTALL)


def proc_nb_text(nb_text):
    """ Process notebook GFM markdown
    """
    # Strip comments
    txt = COMMENT_RE.sub('', nb_text)
    # Modify code fencing to add curlies around fence arguments.
    # This converts from GFM Markdown fence blocks to RMarkdown fence blocks.
    return FENCE_START_RE.sub(r'```{\1}', txt)


def proc_callout_header(elem):
    for node in elem.content:
        if 'callout-title-container' in node.classes:
            n0, = node.content
            contents = [Str('Note:'), Space] + list(n0.content)
            return [pf.Para(Strong(*contents))]
    return []


def filter_strip_header_nos(elem, doc):
    if not isinstance(elem, pf.Span):
        return
    if (doc._wnb_params['nb-strip-header-nos'] and
        'header-section-number' in elem.classes):
        return []


def filter_flatten_divspans(elem, doc):
    params = doc._wnb_params
    if not isinstance(elem, (pf.Div, pf.Span)):
        return
    # Replace various containers with their contents.
    if params['nb-flatten-divspans'].intersection(elem.classes):
        return list(elem.content)


def filter_callout_note_classic(elem, doc):
    if not isinstance(elem, pf.Div) or 'callout-note' not in elem.classes:
        return
    header = []
    body = []
    for node in elem.content:
        assert isinstance(node, pf.Div)
        if 'callout-header' in node.classes:
            header = proc_callout_header(node)
        if 'callout-body-container' in node.classes:
            body = list(node.content)
    return header + body + (
        [] if header is None else
        [pf.Para(Strong(Str('End'), Space, Str('of'), Space, Str('note')))]
    )


def filter_callout_note_custom(elem, doc):
    if not isinstance(elem, pf.Div):
        return
    if not elem.attributes.get('__quarto_custom_type') == 'Callout':
        return
    assert elem.attributes.get('__quarto_custom') == 'true'
    header, content = list(elem.content)
    for e in (header, content):
        assert isinstance(e, pf.Div)
        assert e.attributes.get('__quarto_custom_scaffold') == 'true'
    hdr_content = pf.stringify(header)
    hdr_txt = ': ' + hdr_content if hdr_content else ''
    return (pf.convert_text(f'**Note{hdr_txt}**') +
            list(content.content) +
            pf.convert_text(f'**End of Note{hdr_txt}**'))


def filter_cell_out(elem, doc):
    if isinstance(elem, pf.Div) and 'cell' in elem.classes:
        return [e for e in elem.content
                if 'cell-code' in getattr(e, 'classes', [])]


def strip_cells(nb_doc, params):
    nb_doc._wnb_params = params
    for f in (filter_strip_header_nos,
              filter_flatten_divspans,
              filter_callout_note_classic,
              filter_callout_note_custom,
              filter_cell_out):
        nb_doc = nb_doc.walk(f)
    return nb_doc


def find_notebooks(elem):
    state = 'before-nb'
    nbs = []
    for elem in elem.content:
        # Recursive search for notebooks in divs.
        if isinstance(elem, pf.Div):
            nbs += find_notebooks(elem)
        if state == 'before-nb':
            if is_div_class(elem, 'nb-start'):
                state = 'in-nb'
                attrs = elem.attributes
                nb = []
                continue
        elif state == 'in-nb':
            if is_div_class(elem, 'nb-end'):
                state = 'before-nb'
                d = pf.Doc(*nb)
                nbs.append([attrs, d])
                continue
            nb.append(elem)
    if state != 'before-nb':
        raise FilterError('No `nb-end` found for last notebook')
    return nbs


def write_notebook_files(nb_doc, attrs):
    if 'name' not in attrs:
        raise FilterError('Need name in notebook attributes')
    if 'title' not in attrs:
        attrs['title'] = name2title(attrs['name'])
    out_nb_dir = attrs['nb_out_path']
    out_nb_fpath = out_nb_dir / '{name}.{nb-format}'.format(**attrs)
    out_nb_dir.mkdir(parents=True, exist_ok=True)
    nb_md = ('# {title}\n\n\n'.format(**attrs) +
             fmt2fmt(nb_doc, in_fmt='panflute'))
    nb = jpt.reads(proc_nb_text(nb_md), 'Rmd')
    jpt.write(nb, out_nb_fpath, fmt=attrs['nb-format'])
    # Write associated data files.
    if not (dfs := find_data_files(nb)):
        return
    out_data_files = write_data_files(Path(), dfs, out_nb_dir)
    # Write zip file if there are data files
    write_zip([out_nb_fpath] + out_data_files, out_nb_dir), len(dfs)


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


def finalize(doc):
    params = fill_params(doc.metadata)
    build_formats = params['nb-build-formats']
    if '*' not in build_formats and params['out_format'] not in build_formats:
        return
    for attrs, nb_doc in find_notebooks(doc):
        nb_doc = strip_cells(nb_doc, params)
        write_notebook_files(nb_doc, {**attrs, **params})


def action(elem, doc):
    pass


def main(doc=None):
    return pf.run_filter(action=action,
                         prepare=None,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
