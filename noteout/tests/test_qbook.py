""" Test rendering of a project
"""

from os import listdir
from pathlib import Path
from subprocess import run
from shutil import copytree

import yaml
import jupytext


QBOOK_PATH = Path(__file__).parent.joinpath('qbook')


def get_yml_config(lang='Python'):
    with open(QBOOK_PATH / '_quarto.yml', 'rt') as fobj:
        config = yaml.load(fobj, Loader=yaml.SafeLoader)
    is_r = lang == 'R'
    config['noteout'].update({
        'filter-divspans': ['python'] if is_r else ['r'],
        'nb-format': 'Rmd' if is_r else 'ipynb'})
    return config


def make_book(out_path, yml_config, args=()):
    copytree(QBOOK_PATH, out_path)
    with open(out_path / '_quarto.yml', 'wt') as fobj:
        yaml.dump(yml_config, fobj)
    run(['quarto', 'render', '.'] + list(args), cwd=out_path)


def test_qbook_render(tmp_path):
    # Test qbook build.
    # Output from write_meta filter.
    metas = set([f'meta_{i:03d}.json' for i in range(4)])
    for lang, exp_ext in (('Python', 'ipynb'),
                          ('R', 'Rmd')):
        tmp_qbook = tmp_path / f'{lang}_qbook'
        out_yml = get_yml_config(lang)
        out_yml['noteout']['pre-filter'] = ['comment']
        if lang == 'python':
            out_yml['binder-url'] = (
                'https://mybinder.org/v2/gh/resampling-stats/'
                'resampling-with/gh-pages?filepath=python-book/')
        make_book(tmp_qbook, out_yml)
        # Check meta files from write_meta
        source_listing = listdir(tmp_qbook)
        assert metas <= set(source_listing)
        # Check book generation.
        book_dir = tmp_qbook / '_book'
        gen_nb_fname = 'my_notebook.' + exp_ext
        out_fnames = listdir(book_dir)
        assert set(['index.html',
                    gen_nb_fname,
                    'intro.html']) <= set(out_fnames)
        with open(book_dir / 'intro.html', 'rt') as fobj:
            intro_contents = fobj.read()
        nb_only_str = 'This appears only in the notebook'
        assert nb_only_str not in intro_contents
        nb = jupytext.read(book_dir / gen_nb_fname)
        assert len(nb.cells) == 2
        assert nb_only_str in nb.cells[1]['source']
