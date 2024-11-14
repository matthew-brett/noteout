""" Tests for nb2
"""

from pathlib import Path

import jupytext

from .test_nb1 import NB1_META
from .tutils import q2doc, filter_two_pass


def test_nb2_nb(in_tmp_path, nb2_text):
    doc = q2doc(nb2_text)
    doc.metadata = NB1_META.copy()
    filter_two_pass(doc)
    out_path = Path('out_notes')
    nb = jupytext.read(out_path / 'nb_primero.ipynb')
    nb_md = jupytext.writes(nb, fmt='Rmd')
    assert nb_md == """\
# The first notebook


Find this notebook on the web at @nte-nb_primero.

Some notebook text.
"""
