""" Tests for nb2
"""

import jupytext

import noteout.write_notebooks as nwnbs

from .tutils import md2fmt, filter_doc


def test_nb2_nb(in_tmp_path, nb2_text):
    doc = md2fmt(nb2_text, 'panflute')
    doc.metadata['noteout'] = {'nb-format': 'ipynb'}
    filter_doc(doc, nwnbs)
    nb = jupytext.read('nb_primero.ipynb')
    nb_md = jupytext.writes(nb, fmt='Rmd')
    assert nb_md == """\
# The first notebook


Some notebook text.
"""
