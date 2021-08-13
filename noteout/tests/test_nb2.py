""" Tests for nb2
"""

import os
import os.path as op
from pathlib import Path
from copy import deepcopy

import panflute as pf
import jupytext

import noteout.write_notebooks as nwnbs

from .tutils import (read_md, assert_json_equal, filter_doc, in_tmp_path)

import pytest

DATA_DIR = Path(__file__).parent

def test_nb2_nb(in_tmp_path):
    doc = read_md(DATA_DIR.joinpath('nb2.Rmd'))
    doc.metadata['noteout'] = {'nb-format': 'ipynb'}
    filter_doc(doc, nwnbs)
    nb = jupytext.read('nb_primero.ipynb')
    nb_md = jupytext.writes(nb, fmt='Rmd')
    assert nb_md == """\
# The first notebook


Some notebook text.
"""
