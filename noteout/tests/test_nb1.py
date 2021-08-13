""" Tests on notebook 1 text.
"""

from pathlib import Path
from copy import deepcopy

import panflute as pf

import noteout.filter_divspans as nfds
import noteout.write_notebooks as nwnbs

from .tutils import (read_md, assert_json_equal, filter_doc)

DATA_DIR = Path(__file__).parent


def test_nb1_strip():
    pth = DATA_DIR.joinpath('nb1.Rmd')
    doc = read_md(pth)
    # No filtering section - contents unchanged.
    filtered_not = filter_doc(doc, nfds)
    assert_json_equal(doc, filtered_not)
    # Filter out R sections
    doc_dont_r = deepcopy(doc)
    doc_dont_r.metadata['noteout'] = {"filter_divspans": ['r']}
    filtered_r = filter_doc(doc_dont_r, nfds)
    doc_no_r = read_md(DATA_DIR.joinpath('nb1_no_r.Rmd'))
    assert_json_equal(filtered_r, doc_no_r)
    # Filter Python instead.
    doc_dont_py = deepcopy(doc)
    doc_dont_py.metadata['noteout'] = {"filter_divspans": ['python']}
    filtered_py = filter_doc(doc_dont_py, nfds)
    doc_no_py = read_md(DATA_DIR.joinpath('nb1_no_py.Rmd'))
    assert_json_equal(doc_no_py, filtered_py)


def test_nb1_notebook(tmp_path):
    pth = DATA_DIR.joinpath('nb1.Rmd')
    doc = read_md(pth)
    # Simulate _variables.yml file read
    for lang, nb_format in (('python', 'ipynb'),
                            ('r', 'Rmd')):
        doc.metadata['noteout'] = {'nb-format': nb_format}
        doc.metadata['project'] = {'output-dir': str(tmp_path)}
        if nb_format == 'ipynb':
            doc.metadata['noteout']['binder-url'] = (
                'https://mybinder.org/v2/gh/resampling-stats/'
                'resampling-with/gh-pages?filepath=python-book/')
        nb_filtered = filter_doc(doc, nwnbs)
        actual = pf.convert_text(nb_filtered,
                                 input_format='panflute',
                                 output_format='markdown')
        expected = read_md(
            DATA_DIR.joinpath(f'nb1_{lang}_nbs.Rmd'),
            output_format='markdown')
        assert actual == expected
        nb1 = tmp_path / f'first_notebook.{nb_format}'
        assert nb1.exists()
        nb2 = tmp_path / f'second_notebook.{nb_format}'
        assert nb2.exists()
