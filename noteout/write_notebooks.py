""" Panflute filter to drop divs and spans
"""

import os
import os.path as op
import re

import panflute as pf
import jupytext as jpt


FENCE_START_RE = re.compile(r'^```\s*(\w+)$', re.MULTILINE)

# Stuff inside HTML (and Markdown) comment markers.
COMMENT_RE = re.compile(r'<!--.*?-->', re.MULTILINE | re.DOTALL)

FMT_RECODES = {'r': 'Rmd',
               'R': 'Rmd',
               'python': 'ipynb',
               'Python': 'ipynb'}

DEFAULT_BINDER = ('https://mybinder.org/v2/gh/resampling-stats/'
                  'resampling-with/gh-pages?filepath=python-book/')


def proc_text(nb_text):
    """ Process notebook GFM markdown
    """
    # Strip comments
    txt = COMMENT_RE.sub('', nb_text)
    # Modify code fencing to add curlies around fence arguments.
    # This converts from GFM Markdown fence blocks to RMarkdown fence blocks.
    return FENCE_START_RE.sub(r'```{\1}', txt)


def text2nb_text(nb_text, out_fmt):
    """ Process notebook GFM Markdown, write to notebook format `out_fmt`
    """
    txt = proc_text(nb_text)
    return jpt.writes(jpt.reads(txt, 'Rmd'), out_fmt)


def write_notebook(name, content, doc):
    out_sdir = doc.get_metadata('nb_out_dir')
    out_root = doc.get_metadata('project.output-dir', '.')
    if out_sdir is not None and not op.isdir(out_sdir):
        os.makedirs(out_sdir)
    out_fmt = FMT_RECODES[doc.edition]
    out_base = f"{name}.{out_fmt}"
    if out_sdir:
        out_base = op.join(out_sdir, out_base)
    nb_md = pf.convert_text(content,
                            input_format='panflute',
                            output_format='gfm',
                            standalone=True)
    out_fname = op.join(out_root, out_base)
    with open(out_fname, 'wt') as fobj:
        fobj.write(text2nb_text(nb_md, out_fmt))
    return out_base


def prepare(doc):
    edition = doc.get_metadata('_quarto_vars.edition')
    doc.edition = edition.lower() if edition else None


def action(elem, doc):
    if not isinstance(elem, pf.Div):
        return
    if not elem.identifier == 'notebook':
        return
    name = elem.attributes.get('name')
    if name is None:
        raise RuntimeError('Need name attribute for notebook')
    nb_path = write_notebook(name, elem.content, doc)
    header = pf.convert_text(f'Start of `{name}` notebook',
                             input_format='markdown',
                             output_format='panflute')
    binder_url = doc.get_metadata('binder_url', default=DEFAULT_BINDER)
    interact_bit = ('<a class="interact-button" '
                    f'href="{binder_url}{nb_path}">Interact</a>'
                    if doc.edition == 'python' else '')
    header.append(pf.RawBlock(
        f"""\
        <div class="nb-links">
        <a class="notebook-link" href={nb_path}>Download notebook</a>
        {interact_bit}
        </p>
        </div>
        """))
    footer = pf.convert_text(f'End of `{name}` notebook',
                             input_format='markdown',
                             output_format='panflute')
    elem.content = header + list(elem.content) + footer
    return elem


def finalize(doc):
    del doc.edition


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
