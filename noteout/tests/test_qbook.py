""" Test rendering of a project
"""

from os import listdir
from pathlib import Path
from subprocess import run
from shutil import copytree

QBOOK_PATH = Path(__file__).parent.joinpath('qbook')


def test_qbook_render(tmp_path):
    # Test qbook build.
    # Output from write_meta filter.
    metas = set([f'meta_{i:03d}.json' for i in range(4)])
    for lang, exp_ext in (('Python', 'ipynb'),
                          ('R', 'Rmd')):
        tmp_qbook = tmp_path / f'{lang}_qbook'
        copytree(QBOOK_PATH, tmp_qbook)
        with open(tmp_qbook / '_variables.yml', 'wt') as fobj:
            fobj.write(f'edition: {lang.lower()}\n'
                       f'lang: {lang}')
        run(['quarto', 'render', '.'], cwd=tmp_qbook)
        # Check meta files from write_meta
        source_listing = listdir(tmp_qbook)
        assert metas <= set(source_listing)
        # Check book generation.
        generated = listdir(tmp_qbook / '_book')
        assert set(['index.html',
                    'my_notebook.' + exp_ext,
                    'intro.html']) <= set(generated)
