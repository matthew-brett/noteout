""" Test rendering of a project
"""

from os import listdir
from pathlib import Path
from subprocess import run
from shutil import copytree

QBOOK_PATH = Path(__file__).parent.joinpath('qbook')


def test_qbook_render(tmp_path):
    tmp_qbook = tmp_path / 'qbook'
    copytree(QBOOK_PATH, tmp_qbook)
    run(['quarto', 'render', '.'], cwd=tmp_qbook)
    generated = listdir(tmp_qbook / '_book')
    assert set(['index.html',
                'my_notebook.ipynb',
                'intro.html']) <= set(generated)
