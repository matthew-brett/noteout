""" Test rendering of a project
"""

from pathlib import Path
from subprocess import run

QBOOK_PATH = Path(__file__).parent.joinpath('qbook')


def test_qbook_render():
    run(['quarto', 'render', '.'], cwd=QBOOK_PATH)
