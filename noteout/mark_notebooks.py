#!/usr/bin/env python3
""" Panflute filter to drop notes at start and end of notebooks.

Do a first pass before Quarto filters (note_notebooks) that takes each notebook
div and:

* Drops a note marking the start of the notebook.
* Takes the contents of the div and moves it down a level.
* Drops a note marking the end of the notebook.
"""

from pathlib import Path
import os.path as op
from copy import deepcopy

import panflute as pf
from panflute import Str, Strong, Space


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
    header, footer = get_header_footer(name, doc, nb_path, out_path, df_paths)
    elem.content = header + list(elem.content) + footer
    return elem


def main(doc=None):
    return pf.run_filter(action)


if __name__ == "__main__":
    main()
