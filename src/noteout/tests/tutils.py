""" Test utilities
"""

import os
import json
from copy import deepcopy

import panflute as pf
import pytest


def dump_json(d, fname):
    """ Function for interactive debugging
    """
    if hasattr(d, 'to_json'):
        d = d.to_json()
    with open(fname, 'wt') as fobj:
        json.dump(d, fobj, indent=2)


def get_contents(file_like):
    if hasattr(file_like, 'open'):
        with file_like.open(encoding='utf-8') as fobj:
            return fobj.read()
    return file_like.read()


def read_md(file_like, output_format='panflute'):
    return pf.convert_text(get_contents(file_like),
                           input_format='markdown',
                           output_format=output_format,
                           standalone=True)


def assert_json_equal(doc1, doc2):
    assert doc1.to_json() == doc2.to_json()


def filter_doc(doc, filt_mod):
    copied = deepcopy(doc)
    pf.run_filter(filt_mod.action,
                  prepare=getattr(filt_mod, 'prepare', None),
                  finalize=getattr(filt_mod, 'finalize', None),
                  doc=copied)
    copied.metadata = {}
    return copied


@pytest.fixture
def in_tmp_path(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)
