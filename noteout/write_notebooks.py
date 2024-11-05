#!/usr/bin/env python3
""" Panflute filter to drop divs and spans

Rethinking the strategy.

Do a first pass before Quarto filters (note_notebooks) that takes each notebook
div and:

* Drops a note marking the start of the notebook.
* Takes the contents of the div and moves it down a level.
* Drops a note marking the end of the notebook.

Then, in another pass, (write_notebooks) after the Quarto filters:

* walk the tree.
* when encountering a start notebook note, start recording elements.
* when we hit a stop notebook note, stop recording elements.
* Write out the corresonding notebook.

This could be done by:

* Writing a null filter that merely collects the notebooks.
* A finalize method that writes the notebooks.
"""

import os
from pathlib import Path
import os.path as op
import re
from copy import deepcopy
from shutil import copyfile
import zipfile

import panflute as pf
from panflute import Str, Strong, Space
import jupytext as jpt


FENCE_START_RE = re.compile(r'^```\s*(\w+)$', re.MULTILINE)

# Stuff inside HTML (and Markdown) comment markers.
COMMENT_RE = re.compile(r'<!--.*?-->', re.MULTILINE | re.DOTALL)

# Default flatten divspans
DEFAULT_FLATTEN_DS = {'header-section-number', 'nb-only'}

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


def proc_text(nb_text):
    """ Process notebook GFM markdown
    """
    # Strip comments
    txt = COMMENT_RE.sub('', nb_text)
    # Modify code fencing to add curlies around fence arguments.
    # This converts from GFM Markdown fence blocks to RMarkdown fence blocks.
    return FENCE_START_RE.sub(r'```{\1}', txt)


def name2title(name):
    return name.replace('_', ' ').capitalize()


def prepare(doc):
    doc.nb_format = doc.get_metadata('noteout.nb-format', 'Rmd')
    doc.strip_header_nos = doc.get_metadata('noteout.strip-header-nos', True)
    flat_ds = set(doc.get_metadata('noteout.nb-flatten-divspans',
                                   DEFAULT_FLATTEN_DS))
    if '+' in flat_ds:
        flat_ds.remove('+')
        flat_ds = flat_ds | DEFAULT_FLATTEN_DS
    doc.nb_flatten_divspans = flat_ds
    doc.notebooks = []
    doc.parse_state = 'before-notebook'


def finalize(doc):
    for nb in doc.notebooks:
        write_notebook(nb)
    del doc.nb_format, doc.strip_header_nos, doc.nb_flatten_divspans


def filter_callout_header(elem):
    for node in elem.content:
        if 'callout-title-container' in node.classes:
            n0, = node.content
            contents = [Str('Note:'), Space] + list(n0.content)
            return [pf.Para(Strong(*contents))]
    return []


def filter_callout_note(elem):
    header = []
    body = []
    for node in elem.content:
        assert isinstance(node, pf.Div)
        if 'callout-header' in node.classes:
            header = filter_callout_header(node)
        if 'callout-body-container' in node.classes:
            body = list(node.content)
    return header + body + (
        [] if header is None else
        [pf.Para(Strong(Str('End'), Space, Str('of'), Space, Str('note')))]
    )


def filter_out(elem):
    return [e for e in elem.content
            if 'cell-code' in getattr(e, 'classes', [])]


def strip_cells(elem, doc):
    if not isinstance(elem, (pf.Div, pf.Span)):
        return
    if (doc.strip_header_nos and
        isinstance(elem, pf.Span) and
        'header-section-number' in elem.classes):
        return []
    # Replace various containers with their contents.
    if doc.nb_flatten_divspans.intersection(elem.classes):
        return list(elem.content)
    if 'callout-note' in elem.classes:
        return filter_callout_note(elem)
    # Drop cell div and all contents except code.
    if 'cell' not in elem.classes:
        return
    return filter_out(elem)


def find_data_files(nb):
    out_fnames = []
    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue
        match = READ_RE.search(cell['source'])
        if match:
            out_fnames.append(match.groups()[-1])
    return out_fnames


def write_data_files(data_files, out_dir):
    # Write any data files.
    out_files = []
    for data_fname in data_files:
        data_out_fname = op.join(out_dir, data_fname)
        data_out_dir = op.dirname(data_out_fname)
        if not op.isdir(data_out_dir):
            os.makedirs(data_out_dir)
        copyfile(data_fname, data_out_fname)
        out_files.append(data_out_fname)
    return out_files


def _reroot(fname, out_root):
    return fname if out_root is None else op.relpath(fname, out_root)


def get_nb_intro(doc, title):
    quarto_params = doc.get_metadata('quarto-doc-params')
    default = f'# {title}\n\n\n'
    if quarto_params is None:
        return default
    if quarto_params.get('out_format') != 'html':
        return default
    output_page = Path(quarto_params.get('output_file'))
    output_dir = Path(quarto_params.get('output_directory'))
    rel_path = output_page.relative_to(output_dir)
    return f'''\
---
jupyter:
  noteout:
    html_page: {rel_path}
---

# {title}


[Notebook from {rel_path.stem}]({rel_path})\n

'''


def write_notebook(name, elem, doc):
    out_root = doc.get_metadata('project.output-dir')
    out_sdir = doc.get_metadata('noteout.nb-dir')
    out_fmt = doc.nb_format
    parts = [out_root, out_sdir,  f"{name}.{out_fmt}"]
    out_fname = op.join(*[p for p in parts if p])
    out_dir = op.dirname(out_fname)
    if out_dir and not op.isdir(out_dir):
        os.makedirs(out_dir)
    title = elem.attributes.get('title', name2title(name))
    nb_md = get_nb_intro(doc, title) + pf.convert_text(
        elem.content,
        input_format='panflute',
        output_format='gfm',
        standalone=True)
    nb = jpt.reads(proc_text(nb_md), 'Rmd')
    data_files = find_data_files(nb)
    jpt.write(nb, out_fname, fmt=out_fmt)  # Write notebook.
    # Write associated data files.
    out_data_files = write_data_files(data_files, out_dir)
    # Return notebook and data file paths relative to out_froot
    return (_reroot(out_fname, out_root),
            [_reroot(df, out_root) for df in out_data_files])


def _get_interact_links(doc, nb_path):
    interact_url = doc.get_metadata('noteout.interact-url')
    if interact_url is None:
        return ''
    nb_path = nb_path.replace(op.sep, '/')  # In URL form.
    link_nb_dir = doc.get_metadata('noteout.link-nb-dir', None)
    if link_nb_dir is None:
        link_out_path = nb_path
    else:
        name = nb_path.split('/')[-1]
        link_out_path = (name if link_nb_dir == '' else
                            f'{link_nb_dir}/{name}')
    url_nb_suffix = doc.get_metadata('noteout.url_nb_suffix', None)
    url_nb_path = (link_out_path if url_nb_suffix is None else
                    op.splitext(link_out_path)[0] + url_nb_suffix)
    return ('<a class="interact-button" '
            f'href="{interact_url}{url_nb_path}">Interact</a>\n')


def get_header_footer(name, doc, nb_path, out_path, data_files):
    header = pf.convert_text(
        f'''\
:::{{#nte-nb_{name} .callout-note}}
## {name}` notebook
''',
        input_format='markdown',
        output_format='panflute')
    interact_links = _get_interact_links(doc, nb_path)
    download_txt = (' notebook' if len(data_files) == 0 else
                    (' zip with notebook + data file' +
                     ('s' if len(data_files) > 1 else '')))
    header.append(pf.RawBlock(
        f"""\
<div class="nb-links">
<a class="notebook-link" href={out_path}>Download{download_txt}</a>
{interact_links}</div>
"""))
    header.extend(pf.convert_text('\n:::\n\n',
                                  input_format='markdown',
                                  output_format='panflute'))
    footer = pf.convert_text(f'End of `{name}` notebook',
                             input_format='markdown',
                             output_format='panflute')
    return header, footer


def _write_zip(fnames):
    out_zip_fname = Path(fnames[0]).with_suffix('.zip')
    with zipfile.ZipFile(out_zip_fname, "w") as zf:
        for fname in fnames:
            zf.write(fname)
    return out_zip_fname


def is_nb_start(elem):
    return (isinstance(elem, pf.Div) and 'notebook-start' in elem.classes)


def is_nb_end(elem):
    return (isinstance(elem, pf.Div) and 'notebook-end' in elem.classes)


def action(elem, doc):
    if doc.parse_state == 'before-notebook':
        if is_nb_start(elem):
            # Start new notebook, change state to in-notebook.
            doc.parse_state = 'in-notebook'
    elif doc.parse_state == 'in-notebook':
        if is_nb_end(elem):
            # Dump elements with metadata to doc metadata.
            doc.parse_state = 'before-notebook'
        else:
            # Append element to notebook tree.
            pass

    name = elem.attributes.get('name')
    if name is None:
        raise RuntimeError('Need name attribute for notebook')
    stripped = deepcopy(elem)
    stripped.walk(strip_cells)
    nb_path, df_paths = write_notebook(name, stripped, doc)
    out_path = _write_zip([nb_path] + df_paths) if df_paths else nb_path
    header, footer = get_header_footer(name, doc, nb_path, out_path, df_paths)
    elem.content = header + list(elem.content) + footer
    return elem


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
