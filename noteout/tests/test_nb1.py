""" Tests on notebook 1 text.
"""

from pathlib import Path
from copy import deepcopy
from io import StringIO

import panflute as pf

import noteout.drop_div_spans as ndds

DATA_DIR = Path(__file__).parent


def get_contents(file_like):
    if hasattr(file_like, 'open'):
        with file_like.open(encoding='utf-8') as fobj:
            return fobj.read()
    return file_like.read()


def read_md(pth):
    markdown_text = get_contents(pth)
    return pf.convert_text(markdown_text,
                           input_format='markdown',
                           output_format='panflute',
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


def test_nb1():
    pth = DATA_DIR.joinpath('nb1.Rmd')
    contents = get_contents(pth)
    doc = read_md(StringIO(contents))

    filtered_r = filter_me(doc, ndds)
    doc_no_r = read_md(DATA_DIR.joinpath('nb1_no_r.Rmd'))
    assert_doc_equal(filtered_r, doc_no_r)
    drop_spec = "drop_div_spans: ['R']"
    # Filter Python instead.
    contents_no_py = contents.replace(drop_spec,
                                      "drop_div_spans: ['Python']")
    doc_no_py = read_md(StringIO(contents_no_py))
    filtered_py = filter_me(doc_no_py, ndds)
    doc_no_py = read_md(DATA_DIR.joinpath('nb1_no_py.Rmd'))
    assert_doc_equal(doc_no_py, filtered_py)
    # No filtering section - contents unchanged.
    contents_no_drop = contents.replace(drop_spec, '')
    doc_no_drop = read_md(StringIO(contents_no_drop))
    filtered_not = filter_me(doc_no_drop, ndds)
    assert_doc_equal(doc_no_drop, filtered_not)
