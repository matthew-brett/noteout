""" Test write notebooks

The first pass (pre-pass) does these steps:

* Remove / flatten notebook divs.
* Drop notes before and after flatted div.
* The notes should suitably create Interact and Download buttons or the LaTeX
  URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
* As well as the top-note, there should be a nb-only div with a link back to
  the web version of the notebook.  This could be a link to the note label for
  HTML output, but maybe we can omit this for the LaTeX case (because we won't
  generally be generating the notebooks from the LaTeX build).
"""

import panflute as pf

from noteout import filter_pre, filter_divspans, write_notebooks as wn

from .tutils import (fmt2fmt, doc2json, read_md, assert_json_equal, filter_doc,
                     check_contains)

import pytest


@pytest.fixture
def filtered_nb1(nb1_doc):
    metadata = {'noteout': {
        'pre-filter': ['todo', 'comment'],
        'filter-divspans': ['python']}}
    nb1_doc.metadata = metadata
    de_pre = filter_doc(nb1_doc, filter_pre.PreFilter)
    de_pre.metadata = metadata
    return filter_doc(de_pre, filter_divspans.MetaFilter)


def test_first_pass(filtered_nb1):
    # Unfiltered does have notebook divs.
    is_nb_div = lambda e, d: wn.is_nb_div(e)
    assert check_contains(filtered_nb1, is_nb_div)
    out_doc = filter_doc(filtered_nb1, wn)
    # assert not check_contains(out_doc, is_nb_div)
    filtered_json = doc2json(filtered_nb1)
    md = fmt2fmt(filtered_json, 'json', 'markdown')
    # Check the basic conversion.
    assert md.startswith('# A heading\n')
    assert md.strip().endswith('\nEnd of page.')
