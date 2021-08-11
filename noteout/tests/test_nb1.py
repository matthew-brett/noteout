""" Tests on notebook 1 text.
"""

from pathlib import Path
from copy import deepcopy
from io import StringIO

import panflute as pf

import noteout.filter_divspans as nfds
import noteout.write_notebooks as nwnbs

DATA_DIR = Path(__file__).parent


def _dump_json(d, fname):
    """ Function for interactive debugging
    """
    import json
    with open(fname, 'wt') as fobj:
        json.dump(d, fobj, indent=2)


def get_contents(file_like):
    if hasattr(file_like, 'open'):
        with file_like.open(encoding='utf-8') as fobj:
            return fobj.read()
    return file_like.read()


def read_md(pth, output_format='panflute'):
    markdown_text = get_contents(pth)
    return pf.convert_text(markdown_text,
                           input_format='markdown',
                           output_format=output_format,
                           standalone=True)


def assert_doc_equal(doc1, doc2):
    assert doc1.to_json() == doc2.to_json()


def filter_me(doc, filt_mod):
    copied = deepcopy(doc)
    pf.run_filter(filt_mod.action,
                  prepare=filt_mod.prepare,
                  finalize=filt_mod.finalize,
                  doc=copied)
    return copied


def test_nb1_strip():
    pth = DATA_DIR.joinpath('nb1.Rmd')
    contents = get_contents(pth)
    doc = read_md(StringIO(contents))

    filtered_r = filter_me(doc, nfds)
    doc_no_r = read_md(DATA_DIR.joinpath('nb1_no_r.Rmd'))
    assert_doc_equal(filtered_r, doc_no_r)
    drop_spec = "filter_divspans: ['R']"
    # Filter Python instead.
    contents_no_py = contents.replace(
        drop_spec,
        "filter_divspans: ['Python']")
    doc_no_py = read_md(StringIO(contents_no_py))
    filtered_py = filter_me(doc_no_py, nfds)
    doc_no_py = read_md(DATA_DIR.joinpath('nb1_no_py.Rmd'))
    assert_doc_equal(doc_no_py, filtered_py)
    # No filtering section - contents unchanged.
    contents_no_drop = contents.replace(drop_spec, '')
    doc_no_drop = read_md(StringIO(contents_no_drop))
    filtered_not = filter_me(doc_no_drop, nfds)
    assert_doc_equal(doc_no_drop, filtered_not)


def test_nb1_notebook(tmp_path):
    pth = DATA_DIR.joinpath('nb1.Rmd')
    contents = get_contents(pth)
    doc = read_md(StringIO(contents))
    # Simulate _variables.yml file read
    doc.metadata['_quarto-vars'] = {'edition': 'python'}
    doc.metadata['output-dir'] = str(tmp_path)
    nb_filtered = filter_me(doc, nwnbs)
    actual = pf.convert_text(nb_filtered,
                             input_format='panflute',
                             output_format='markdown')
    expected = read_md(DATA_DIR.joinpath('nb1_nb_links.Rmd'),
                       output_format='markdown')
    assert actual == expected
