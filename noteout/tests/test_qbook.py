""" Test rendering of a project
"""

from os import listdir
from pathlib import Path
from subprocess import run
from shutil import copytree
from copy import deepcopy
from collections.abc import Mapping

import yaml
import jupytext

import panflute as pf


QBOOK_PATH = Path(__file__).parent.joinpath('qbook')
NB_ONLY_STR = 'This appears only in the notebook'


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


def merge_dict(d1, d2):
    out = deepcopy(d1)
    for k, v2 in d2.items():
        if k not in d1:
            out[k] = v2
            continue
        v1 = d1[k]
        if isinstance(v2, Mapping):
            if isinstance(v1, Mapping):
                out[k] = merge_dict(v1, v2)
            else:
                out[k] = v2
            continue
    return out


def make_book_lang(out_path, lang, extra_config=None, render_args=()):
    out_yml = get_yml_config(lang)
    if extra_config:
        out_yml = merge_dict(out_yml, extra_config)
    make_book(out_path, out_yml, args=render_args)
    return dict(out_path=out_path,
                config_yml=out_yml,
                nb_ext='Rmd' if lang == 'R' else 'ipynb')


def read_notebook(nb_fname):
    # Check notebook contents
    nb = jupytext.read(nb_fname)
    parsed_cells = []
    for cell in nb.cells:
        if cell['cell_type'] != 'markdown':
            parsed_cells.append(None)
            continue
        pfp = pf.convert_text(cell['source'],
                              input_format='markdown',
                              output_format='panflute')
        lines = [pf.stringify(v).strip() for v in pfp]
        parsed_cells.append(dict(pfp=pfp, lines=lines))
    return nb, parsed_cells


def test_qbook_render(tmp_path):
    # Test qbook build.
    # Output from write_meta filter.
    metas = set([f'meta_{i:03d}.json' for i in range(4)])
    for lang in ('Python', 'R'):
        tmp_qbook = tmp_path / f'{lang}_qbook'
        extra_config = {'noteout': {'pre-filter': ['comment']}}
        if lang == 'Python':
            extra_config['binder-url'] = (
                'https://mybinder.org/v2/gh/resampling-stats/'
                'resampling-with/gh-pages?filepath=python-book/')
        params = make_book_lang(tmp_qbook,
                                lang,
                                extra_config)
        # Check meta files from write_meta
        source_listing = listdir(tmp_qbook)
        assert metas <= set(source_listing)
        # Check book generation.
        book_dir = tmp_qbook / '_book'
        gen_nb_fname = f"my_notebook.{params['nb_ext']}"
        out_fnames = listdir(book_dir)
        assert set(['index.html',
                    gen_nb_fname,
                    'intro.html']) <= set(out_fnames)
        with open(book_dir / 'intro.html', 'rt') as fobj:
            intro_contents = fobj.read()
        assert NB_ONLY_STR not in intro_contents
        # Check notebook contents
        nb, parsed = read_notebook(book_dir / gen_nb_fname)
        # There will be 6 cells if output left in notebook.
        assert len(nb.cells) == 4
        p1 = parsed[1]
        assert p1['lines'] == [
            'Here is a paragraph.',
            NB_ONLY_STR,
            'A heading']  # Includes check that header no stripped.
        # Check nb-only div stripped.
        assert not isinstance(p1['pfp'], pf.Div)
        # Check cell outputs stripped from text.
        for cell_info in parsed:
            if cell_info is None:
                continue
            assert not any(isinstance(e, pf.RawBlock) for e in cell_info)


def test_header_strip(tmp_path):
    book_path = tmp_path / 'book'
    extra_config = {'noteout': {'strip-header-nos': False}}
    make_book_lang(book_path, 'Python', extra_config)
    nb, parsed = read_notebook(book_path / '_book' / 'my_notebook.ipynb')
    # If we turn off header stripping, we get section no.
    assert parsed[1]['lines'] == [
        'Here is a paragraph.',
        NB_ONLY_STR,
        '2.1 A heading']
