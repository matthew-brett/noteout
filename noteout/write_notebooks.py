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


def prepare(doc):
    pass


def action(elem, doc):
    if not isinstance(elem, pf.Div):
        return
    if not elem.identifier == 'notebook':
        return
    if not 'name' in elem.attributes:
        raise RuntimeError('Need name attribute for notebook')
    out_sdir = doc.get_metadata('nb_out_dir', default='notebooks')
    edition = doc.get_metadata('rsbook_edition', default='python')
    if not op.isdir(out_sdir):
        os.mkdir(out_sdir)
    out_fmt = FMT_RECODES[edition]
    out_fname = f"{out_sdir}{op.sep}{elem.attributes['name']}.{out_fmt}"
    nb_md = pf.convert_text(elem.content,
                            input_format='panflute',
                            output_format='gfm',
                            standalone=True)
    with open(out_fname, 'wt') as fobj:
        fobj.write(text2nb_text(nb_md, out_fmt))


def finalize(doc):
    pass


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
