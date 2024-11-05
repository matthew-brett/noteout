""" Test write notebooks
"""

import panflute as pf

from noteout import filter_pre, filter_divspans

from .tutils import fmt2fmt, doc2json, read_md, assert_json_equal, filter_doc

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
    md = fmt2fmt(doc2json(filtered_nb1), 'json', 'gfm')
    assert md.startswith('# A heading\n')
    assert md.strip().endswith('\nEnd of page.')
