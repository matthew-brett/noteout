#!/usr/bin/env python3
""" Panflute filter to drop divs and spans
"""

import os
import os.path as op
import re
from copy import deepcopy
from shutil import copyfile

import panflute as pf
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


def finalize(doc):
    del doc.nb_format, doc.strip_header_nos, doc.nb_flatten_divspans


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
    # Drop cell div and all contents except code.
    if 'cell' not in elem.classes:
        return
    return filter_out(elem)


def find_data_reads(nb):
    out_fnames = []
    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue
        match = READ_RE.search(cell['source'])
        if match:
            out_fnames.append(match.groups()[-1])
    return out_fnames


def write_data_files(nb, out_dir):
    # Write any data files.
    for data_fname in find_data_reads(nb):
        data_out_fname = op.join(out_dir, data_fname)
        data_out_dir = op.dirname(data_out_fname)
        if not op.isdir(data_out_dir):
            os.makedirs(data_out_dir)
        copyfile(data_fname, data_out_fname)


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
    nb_md = f'# {title}\n\n\n' + pf.convert_text(
        elem.content,
        input_format='panflute',
        output_format='gfm',
        standalone=True)
    nb = jpt.reads(proc_text(nb_md), 'Rmd')
    jpt.write(nb, out_fname, fmt=out_fmt)  # Write notebook.
    write_data_files(nb, out_dir)  # Write associated data files.
    # Return path relative to out_froot
    return (out_fname if out_root is None else
            op.relpath(out_fname, out_root))


def get_header_footer(name, doc, nb_path):
    nb_sdir = doc.get_metadata('noteout.nb-dir', None)
    link_nb_sdir = doc.get_metadata('noteout.link-nb-dir', nb_sdir)
    parts = op.split(nb_path)
    download_path = '/'.join(parts)
    if nb_sdir != link_nb_sdir and parts[0] == nb_sdir:
        parts = (parts[1:] if link_nb_sdir is None else
                 (link_nb_sdir,) + parts[1:])
    link_path = '/'.join(parts)
    header = pf.convert_text(f'Start of `{name}` notebook',
                             input_format='markdown',
                             output_format='panflute')
    interact_links = ''
    binder_url = doc.get_metadata('noteout.binder-url')
    if binder_url:
        interact_links = (
            '<a class="interact-button" '
            f'href="{binder_url}{link_path}">Interact</a>\n')
    header.append(pf.RawBlock(
        f"""\
<div class="nb-links">
<a class="notebook-link" href={download_path}>Download notebook</a>
{interact_links}</div>
"""))
    footer = pf.convert_text(f'End of `{name}` notebook',
                             input_format='markdown',
                             output_format='panflute')
    return header, footer


def action(elem, doc):
    if not isinstance(elem, pf.Div):
        return
    if not 'notebook' in elem.classes:
        return
    name = elem.attributes.get('name')
    if name is None:
        raise RuntimeError('Need name attribute for notebook')
    stripped = deepcopy(elem)
    stripped.walk(strip_cells)
    nb_path = write_notebook(name, stripped, doc)
    header, footer = get_header_footer(name, doc, nb_path)
    elem.content = header + list(elem.content) + footer
    return elem


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
