""" Tests on notebook 1 text.
"""

import os.path as op
from pathlib import Path
from copy import deepcopy

import jupytext

from noteout.filter_divspans import DivSpanFilter as nfds

from .tutils import (read_md, assert_json_equal, filter_doc_nometa,
                     filter_two_pass, fmt2md)

import pytest

DATA_DIR = Path(__file__).parent

NB_NAMES = ('first_notebook', 'second_notebook')
INB_NAMES = (nb + '.ipynb' for nb in NB_NAMES)
DEF_NOTEOUT =  {
    'nb-format': 'Rmd',
    'nb-dir': 'notebooks',
    'book-url-root': 'https://example.com',
    'interact-url': 'https://mybinder.org/v2/gh/resampling-stats/'
    'resampling-with/gh-pages?filepath=python-book/'}


def test_nb1_strip(nb1_doc):
    # No filtering section - contents unchanged.
    filtered_not = filter_doc_nometa(nb1_doc, nfds)
    assert_json_equal(nb1_doc, filtered_not)
    # Filter out R sections
    doc_dont_r = deepcopy(nb1_doc)
    doc_dont_r.metadata['noteout'] = {"filter-divspans": ['r']}
    filtered_r = filter_doc_nometa(doc_dont_r, nfds)
    doc_no_r = read_md(DATA_DIR.joinpath('nb1_no_r.Rmd'))
    assert_json_equal(filtered_r, doc_no_r)
    # Filter Python instead.
    doc_dont_py = deepcopy(nb1_doc)
    doc_dont_py.metadata['noteout'] = {"filter-divspans": ['python']}
    filtered_py = filter_doc_nometa(doc_dont_py, nfds)
    doc_no_py = read_md(DATA_DIR.joinpath('nb1_no_py.Rmd'))
    assert_json_equal(doc_no_py, filtered_py)


def test_nb1_notebook(nb1_doc, in_tmp_path):
    # Simulate _variables.yml file read
    meta = nb1_doc.metadata
    for lang, nb_format in (('python', 'ipynb'),
                            ('r', 'Rmd')):
        meta['noteout'] = DEF_NOTEOUT.copy()
        meta['noteout']['nb-format'] = nb_format
        meta['quarto-doc-params'] = {'output_directory': str(in_tmp_path)}
        if nb_format == 'ipynb':
            meta['noteout']['interact-url'] = (
                'https://mybinder.org/v2/gh/resampling-stats/'
                'resampling-with/gh-pages?filepath=python-book/')
        nb_filtered = filter_two_pass(nb1_doc)
        actual = fmt2md(nb_filtered)
        expected = read_md(DATA_DIR.joinpath(f'nb1_{lang}_nbs.Rmd'),
                           'markdown')
        assert actual == expected
        for nb_name in NB_NAMES:
            assert (in_tmp_path / 'notebooks' /
                    f'{nb_name}.{nb_format}').exists()


NB_EXPECTED = {'first_notebook': """\
# First notebook


Here is a paragraph.

And another.
""",
               'second_notebook': """\
# Second notebook


Here, again, is a paragraph.

And, again, another.
"""}


def test_notebooks(in_tmp_path, nb1_doc):
    for lang, nb_format in (('python', 'ipynb'),
                            ('r', 'Rmd')):
        nb1_doc.metadata['noteout'] = {'nb-format': nb_format}
        filter_two_pass(nb1_doc)
        for nb_name in NB_NAMES:
            nb = jupytext.read(f'{nb_name}.{nb_format}')
            assert len(nb.cells) == 2
            nb_md = jupytext.writes(nb, fmt='Rmd')
            assert nb_md == NB_EXPECTED[nb_name]


@pytest.fixture
def nb1_idoc(nb1_doc):
    nb1_doc.metadata['noteout'] = {'nb-format': 'ipynb'}
    return nb1_doc


def test_nb1_out_path(in_tmp_path, nb1_idoc):
    # No output directory, built at working directory.
    filter_two_pass(nb1_idoc)
    for nb_name in INB_NAMES:
        assert op.exists(nb_name)
        assert (in_tmp_path / nb_name).exists()


def test_nb1_proj_path(in_tmp_path, nb1_idoc):
    # Set project output path (relative), use that.
    nb1_idoc.metadata['quarto-doc-params'] = {'output_directory': 'test_book'}
    filter_two_pass(nb1_idoc)
    for nb_name in INB_NAMES:
        assert op.exists(op.join('test_book', nb_name))
        assert (in_tmp_path / 'test_book' / nb_name).exists()


def test_nb1_sdir(in_tmp_path, nb1_idoc):
    # Set notebook subdirectory, use that.
    nb1_idoc.metadata['noteout']['nb-dir'] = 'nb_directory'
    filter_two_pass(nb1_idoc)
    for nb_name in INB_NAMES:
        assert op.exists(op.join('nb_directory', nb_name))
        assert (in_tmp_path / 'nb_directory' / nb_name).exists()


def test_nb1_proj_and_sdir(in_tmp_path, nb1_idoc):
    # Set both project and subdirectory.
    nb1_idoc.metadata['quarto-doc-params'] = {'output_directory': 'test_book'}
    nb1_idoc.metadata['noteout']['nb-dir'] = 'nb_directory'
    filter_two_pass(nb1_idoc)
    for nb_name in INB_NAMES:
        assert op.exists(op.join('test_book', 'nb_directory', nb_name))
        assert (in_tmp_path / 'test_book' / 'nb_directory' / nb_name).exists()


def test_nb1_sdir_overrides(in_tmp_path, tmp_path, nb1_idoc):
    # Set both project and subdirectory.
    nb1_idoc.metadata['quarto-doc-params'] = {'output_directory': 'test_book'}
    # Subdirectory is absolute path.
    # Subdirectory overrides project directory.
    nb1_idoc.metadata['noteout']['nb-dir'] = op.abspath(tmp_path)
    filter_two_pass(nb1_idoc)
    for nb_name in INB_NAMES:
        assert not op.exists(op.join('test_book', nb_name))
        assert (tmp_path / nb_name).exists()
