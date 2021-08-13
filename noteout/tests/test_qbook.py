""" Test rendering of a project
"""

from os import listdir
from pathlib import Path
from subprocess import run
from shutil import copytree
from copy import deepcopy

import yaml
import jupytext

QBOOK_PATH = Path(__file__).parent.joinpath('qbook')


def test_qbook_render(tmp_path):
    # Test qbook build.
    # Output from write_meta filter.
    metas = set([f'meta_{i:03d}.json' for i in range(4)])
    with open(QBOOK_PATH / '_quarto.yml', 'rt') as fobj:
        in_yml = yaml.load(fobj, Loader=yaml.SafeLoader)
    for lang, exp_ext in (('Python', 'ipynb'),
                          ('R', 'Rmd')):
        tmp_qbook = tmp_path / f'{lang}_qbook'
        copytree(QBOOK_PATH, tmp_qbook)
        out_yml = deepcopy(in_yml)
        out_yml['noteout'] = {
            'filter-divspans': ['python'] if lang == 'r' else ['r'],
            'nb-format': exp_ext}
        if lang == 'python':
            out_yml['binder-url'] = (
                'https://mybinder.org/v2/gh/resampling-stats/'
                'resampling-with/gh-pages?filepath=python-book/')
        with open(tmp_qbook / '_quarto.yml', 'wt') as fobj:
            yaml.dump(out_yml, fobj)
        run(['quarto', 'render', '.'], cwd=tmp_qbook)
        # Check meta files from write_meta
        source_listing = listdir(tmp_qbook)
        assert metas <= set(source_listing)
        # Check book generation.
        book_dir = tmp_qbook / '_book'
        gen_nb_fname = 'my_notebook.' + exp_ext
        assert set(['index.html',
                    gen_nb_fname,
                    'intro.html']) <= set(listdir(book_dir))
        with open(book_dir / 'intro.html', 'rt') as fobj:
            intro_contents = fobj.read()
        nb_only_str = 'This appears only in the notebook'
        assert nb_only_str not in intro_contents
        nb = jupytext.read(book_dir / gen_nb_fname)
        assert len(nb.cells) == 2
        assert nb_only_str in nb.cells[1]['source']
