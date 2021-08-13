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


def name2title(name):
    return name.replace('_', ' ').capitalize()


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
    with open(out_fname, 'wt') as fobj:
        fobj.write(text2nb_text(nb_md, out_fmt))
    # Return path relative to out_froot
    return (out_fname if out_root is None else
            op.relpath(out_fname, out_root))


def prepare(doc):
    doc.nb_format = doc.get_metadata('noteout.nb-format', 'Rmd')


def action(elem, doc):
    if not isinstance(elem, pf.Div):
        return
    if not 'notebook' in elem.classes:
        return
    name = elem.attributes.get('name')
    if name is None:
        raise RuntimeError('Need name attribute for notebook')
    nb_path = write_notebook(name, elem, doc)
    header = pf.convert_text(f'Start of `{name}` notebook',
                             input_format='markdown',
                             output_format='panflute')
    interact_links = ''
    binder_url = doc.get_metadata('noteout.binder-url')
    if binder_url:
        interact_links = (
            '<a class="interact-button" '
            f'href="{binder_url}{nb_path}">Interact</a>\n')
    header.append(pf.RawBlock(
        f"""\
<div class="nb-links">
<a class="notebook-link" href={nb_path}>Download notebook</a>
{interact_links}</div>
"""))
    footer = pf.convert_text(f'End of `{name}` notebook',
                             input_format='markdown',
                             output_format='panflute')
    elem.content = header + list(elem.content) + footer
    return elem


def finalize(doc):
    del doc.nb_format


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
