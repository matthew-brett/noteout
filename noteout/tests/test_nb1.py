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
    copied.metadata = {}
    return copied


def test_nb1_strip():
    pth = DATA_DIR.joinpath('nb1.Rmd')
    contents = get_contents(pth)
    doc = read_md(StringIO(contents))
    # No filtering section - contents unchanged.
    filtered_not = filter_me(doc, nfds)
    assert_doc_equal(doc, filtered_not)
    # Filter out R sections
    doc_dont_r = deepcopy(doc)
    doc_dont_r.metadata['noteout'] = {"filter_divspans": ['r']}
    filtered_r = filter_me(doc_dont_r, nfds)
    doc_no_r = read_md(DATA_DIR.joinpath('nb1_no_r.Rmd'))
    assert_doc_equal(filtered_r, doc_no_r)
    # Filter Python instead.
    doc_dont_py = deepcopy(doc)
    doc_dont_py.metadata['noteout'] = {"filter_divspans": ['python']}
    filtered_py = filter_me(doc_dont_py, nfds)
    doc_no_py = read_md(DATA_DIR.joinpath('nb1_no_py.Rmd'))
    assert_doc_equal(doc_no_py, filtered_py)


def test_nb1_notebook(tmp_path):
    pth = DATA_DIR.joinpath('nb1.Rmd')
    contents = get_contents(pth)
    doc = read_md(StringIO(contents))
    # Simulate _variables.yml file read
    for lang, nb_format in (('python', 'ipynb'),
                            ('r', 'Rmd')):
        doc.metadata['noteout'] = {'nb-format': nb_format}
        doc.metadata['project'] = {'output-dir': str(tmp_path)}
        if nb_format == 'ipynb':
            doc.metadata['noteout']['binder-url'] = (
                'https://mybinder.org/v2/gh/resampling-stats/'
                'resampling-with/gh-pages?filepath=python-book/')
        nb_filtered = filter_me(doc, nwnbs)
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
