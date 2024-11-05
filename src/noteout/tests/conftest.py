""" Pytest fixtures.
"""

import os
from pathlib import Path

import pytest

from .tutils import md2fmt

DATA_DIR = Path(__file__).parent


@pytest.fixture
def nb1_text():
    return (DATA_DIR / 'nb1.Rmd').read_text()


@pytest.fixture
def nb1_doc(nb1_text):
    return md2fmt(nb1_text, 'panflute')


@pytest.fixture
def nb2_text():
    return (DATA_DIR / 'nb2.Rmd').read_text()


@pytest.fixture
def in_tmp_path(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)
