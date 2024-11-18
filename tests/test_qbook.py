""" Test rendering of a project
"""

from os import listdir, unlink
from pathlib import Path
import re
from subprocess import run
from shutil import copytree, rmtree
from glob import glob
from copy import deepcopy
from collections.abc import Mapping
from hashlib import sha1
import json

import yaml
import jupytext

import panflute as pf

from noteout.process_notebooks import NBProcessor

QBOOK_PATH = Path(__file__).parent.parent.joinpath('quarto-example')
NB_ONLY_STR = 'This appears only in the notebook'
NB_DIR = '.'


def get_yml_config(lang='Python'):
    with open(QBOOK_PATH / '_quarto.yml', 'rt') as fobj:
        config = yaml.load(fobj, Loader=yaml.SafeLoader)
    is_r = lang == 'R'
    config['noteout'].update({
        'filter-divspans': ['python'] if is_r else ['r'],
        'nb-format': 'Rmd' if is_r else 'ipynb'})
    return config


def copy_book_source(out_path):
    copytree(QBOOK_PATH, out_path)
    built_path = out_path / '_book'
    if built_path.exists():
        rmtree(built_path)
    for fn in glob(str(out_path / 'meta*.json')):
        unlink(fn)


def make_book(out_path, yml_config, args=(),
              formats=('html', 'pdf')
             ):
    copy_book_source(out_path)
    with open(out_path / '_quarto.yml', 'wt') as fobj:
        yaml.dump(yml_config, fobj)
    extra = list(args) + ['--to=' + f for f in formats]
    run(['quarto', 'render', '.'] + list(extra), cwd=out_path)


def merge_dict(d1, d2):
    out = deepcopy(d1)
    for k, v2 in d2.items():
        if k not in d1:
            out[k] = v2
            continue
        v1 = d1[k]
        if isinstance(v2, Mapping) and isinstance(v1, Mapping):
            out[k] = merge_dict(v1, v2)
        else:
            out[k] = v2
    return out


def make_book_lang(out_path, lang, extra_config=None,
                   render_args=(), formats=('html',)):
    out_yml = get_yml_config(lang)
    if extra_config:
        out_yml = merge_dict(out_yml, extra_config)
    make_book(out_path, out_yml, args=render_args, formats=formats)
    return dict(out_path=out_path,
                config_yml=out_yml,
                nb_ext='Rmd' if lang == 'R' else 'ipynb')


def read_notebook(nb_fname):
    # Check notebook contents
    nb = jupytext.read(nb_fname)
    # Make panflute parsed version of each cell.
    parsed_cells = [{'cell_type': c['cell_type']} for c in nb.cells]
    for i, cell in enumerate(nb.cells):
        if cell['cell_type'] != 'markdown':
            continue
        pfp = pf.convert_text(cell['source'],
                              input_format='markdown',
                              output_format='panflute')
        parsed_cells[i].update(dict(
            pfp=pfp,
            lines=[pf.stringify(v).strip() for v in pfp],
            types=[type(v) for v in pfp]))
    return nb, parsed_cells


def dicthash(d, **kwargs):
    d = deepcopy(d)
    d.update(kwargs)
    return sha1(json.dumps(d).encode('latin1')).hexdigest()


def make_new_book(tmp_path, lang, extra_config=None, formats=('html',)):
    out_name = lang
    if extra_config:
        out_name += '_' + dicthash(extra_config)
    book_path = tmp_path / out_name
    assert not Path(book_path).exists()
    params = make_book_lang(book_path, lang,
                            extra_config=extra_config,
                            formats=formats)
    if 'html' in formats:  # Only HTML copies notebook.
        nb, nb_parsed = read_notebook(book_path / '_book' / NB_DIR /
                                      f'my_notebook.{params["nb_ext"]}')
    else:
        nb = nb_parsed = {}
    params.update(dict(book_path=book_path, nb=nb, nb_parsed=nb_parsed))
    return params


def test_qbook_render(tmp_path):
    # Test qbook build.
    # Output from write_meta filter.
    metas = set([f'meta_{i:03d}.json' for i in range(4)])
    docs = set([f'doc_{i:03d}.json' for i in range(4)])
    for lang in ('Python', 'R'):
        extra_config = {'noteout': {'pre-filter': ['comment']}}
        if lang == 'Python':
            extra_config['interact-url'] = (
                'https://mybinder.org/v2/gh/resampling-stats/'
                'resampling-with/gh-pages?filepath=python-book/')
        params = make_new_book(tmp_path,
                               lang,
                               extra_config)
        tmp_qbook = params['book_path']
        # Check meta files from write_meta
        source_listing = listdir(tmp_qbook)
        assert metas <= set(source_listing)
        # Check doc files from write_doc
        assert docs <= set(source_listing)
        # Check book generation.
        book_dir = tmp_qbook / '_book'
        gen_nb_fname = f"my_notebook.{params['nb_ext']}"
        out_fnames = listdir(book_dir)
        assert set(['index.html',
                    gen_nb_fname,
                    'intro.html']) <= set(out_fnames)
        # We aren't building the other notebook type.
        other_ext = 'ipynb' if lang == 'R' else 'Rmd'
        assert f"my_notebook.{other_ext}" not in out_fnames
        with open(book_dir / 'intro.html', 'rt') as fobj:
            intro_contents = fobj.read()
        assert NB_ONLY_STR not in intro_contents
        # Check notebook contents
        nb, parsed = params['nb'], params['nb_parsed']
        # There will be 7 cells if output left in notebook.
        assert len(nb.cells) == 5
        # Check contents of first cell.
        p1 = parsed[1]
        assert p1['lines'] == [
            'Find this notebook on the web at '
            '<a href="#nte-my_notebook" '
            'class="quarto-xref">Note\xa0nte-my_notebook</a>.',
            'Here is a paragraph.',
            NB_ONLY_STR,
            'A heading']  # Includes check that header number stripped.
        # Check nb-only div stripped.
        assert p1['types'] == [pf.Para, pf.Para, pf.Para, pf.Header]
        # Check cell output blocks stripped from text.
        for cell_info in parsed:
            if cell_info['cell_type'] != 'markdown':
                continue
            assert not any(isinstance(e, pf.RawBlock) for e in cell_info)
        # Check contents of last cell.
        pm1 = parsed[-1]
        assert (pm1['lines'] ==
                [f'{lang} thing',
                 f'{lang} text in notebook.',
                 'Last text in notebook.'])
        # Test (lack of) container filter here
        assert pm1['types'] == [pf.Para,
                                pf.Div,  # Python-only section.
                                pf.Para]
        # There's a Python / R span here, without suitable stripping.
        assert [type(v) for v in pm1['pfp'][0].content] == [pf.Span]


def test_nb_output(tmp_path):
    extra_config = {'noteout': {'nb-strip-header-nos': False}}
    params = make_new_book(tmp_path, 'Python', extra_config)
    parsed = params['nb_parsed']
    # If we turn off header stripping, we get section no.
    assert parsed[1]['lines'] == [
        'Find this notebook on the web at '
        '<a href="#nte-my_notebook" '
        'class="quarto-xref">Note\xa0nte-my_notebook</a>.',
        'Here is a paragraph.',
        NB_ONLY_STR,
        '2.1 A heading']
    # Turn off all container filtering.
    extra_config = {'noteout': {'nb-flatten-divspans': [],
                                'nb-strip-header-nos': False}}
    params = make_new_book(tmp_path, 'Python', extra_config)
    parsed = params['nb_parsed']
    # Check nothing is filtered, at a first pass, by checking
    # parts of the parsed first and last cells.
    assert parsed[1]['types'] == [pf.Div, pf.Para, pf.Div, pf.Header]
    assert parsed[-1]['types'] == [pf.Para, pf.Div, pf.Para]
    # Python / R span to start last cell.
    assert [type(v) for v in parsed[-1]['pfp'][0].content] == [pf.Span]
    # Header has span around number.
    assert ([type(v) for v in parsed[1]['pfp'][-1].content] ==
            [pf.Span, pf.Space, pf.Str, pf.Space, pf.Str])
    # Turn on maximal container filtering, retain header numbers.
    extra_config = {'noteout': {'nb-flatten-divspans': ['+', 'python'],
                                'nb-strip-header-nos': False}}
    params = make_new_book(tmp_path, 'Python', extra_config)
    parsed = params['nb_parsed']
    # Check everything is filtered.
    assert parsed[1]['types'] == [pf.Para, pf.Para, pf.Para, pf.Header]
    assert parsed[-1]['types'] == [pf.Para, pf.Para, pf.Para]
    # Now we have the contents of the Python span, not the span.
    assert ([type(v) for v in parsed[-1]['pfp'][0].content] ==
            [pf.Str, pf.Space, pf.Str])
    # We have the header number, but not the header number span.
    assert ([type(v) for v in parsed[1]['pfp'][-1].content] ==
            [pf.Str, pf.Space, pf.Str, pf.Space, pf.Str])
    # If we don't add the '+', we don't get header or nb-only flattening.
    extra_config = {'noteout': {'nb-flatten-divspans': ['python'],
                                'nb-strip-header-nos': False}}
    params = make_new_book(tmp_path, 'Python', extra_config)
    parsed = params['nb_parsed']
    # The nb only is not flattened
    assert parsed[1]['types'] == [pf.Div, pf.Para, pf.Div, pf.Header]
    # But the Python block is.
    assert parsed[-1]['types'] == [pf.Para, pf.Para, pf.Para]
    # We have the contents of the span, from span flattening.
    assert ([type(v) for v in parsed[-1]['pfp'][0].content] ==
            [pf.Str, pf.Space, pf.Str])
    # We still have the header span tho'
    assert ([type(v) for v in parsed[1]['pfp'][-1].content] ==
            [pf.Span, pf.Space, pf.Str, pf.Space, pf.Str])


def test_pdf_smoke(tmpdir):
    params = make_new_book(tmpdir, 'Python', {}, formats=('pdf',))
    assert Path(params['book_path'] / '_book' / 'Quarto-example.pdf').is_file()


def unresolved_refs(nb_file):
    nb = jupytext.read(nb_file)
    nb_rmd = jupytext.writes(nb, 'Rmd')
    return re.findall('quarto-unresolved-ref', nb_rmd)


def test_proc_nbs(tmp_path):
    params = make_new_book(tmp_path, 'Python', {}, formats=('html',))
    book_out = params['out_path'] / '_book'
    html_files = sorted(book_out.glob('**/*.html'))
    nb_file = book_out / 'my_notebook.ipynb'
    assert len(unresolved_refs(nb_file)) == 1
    assert len(html_files) == 4
    out_jl = tmp_path / 'jl_out'
    assert not out_jl.is_dir()
    nbp = NBProcessor(params['out_path'] / '_quarto.yml', out_jl)
    nbp.process()
    assert out_jl.is_dir()
    assert len(unresolved_refs(nb_file)) == 0
