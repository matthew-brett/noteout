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
import shutil
import json

import yaml
import jupytext

import panflute as pf

from noteout.process_notebooks import NBProcessor

QBOOK_PATH = Path(__file__).parent.parent.joinpath('quarto-example')
NB_ONLY_STR = 'This appears only in the notebook'


def get_yml_config(config_path, lang):
    config = yaml.safe_load(config_path.read_text())
    is_r = lang == 'R'
    config['noteout'].update({
        'filter-divspans': ['python'] if is_r else ['r'],
        'nb-format': 'Rmd' if is_r else 'ipynb'})
    if not 'processing' in config:
        config['processing'] = {}
    config['processing']['language'] = lang.lower()
    return config


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


class BookMaker:

    source_path = QBOOK_PATH

    def __init__(self, root_path,
                 extra_config=None,
                 lang='Python',
                 name=None,
                 args=(),
                 formats=('html',)):
        self.root_path = Path(root_path)
        self.extra_config = extra_config if extra_config else {}
        self.lang = lang
        start_config = get_yml_config(self.source_path / '_quarto.yml',
                                      self.lang)
        self.yml_config = merge_dict(start_config, self.extra_config)
        self.name = name if name else dicthash(self.yml_config)
        self.args = args
        self.formats = formats
        self.book_path = self.root_path / self.name
        self._nb_ext='Rmd' if lang == 'R' else 'ipynb'
        self.nb = self.nb_parsed = {}

    def get_book_source(self):
        copytree(self.source_path, self.book_path)
        with open(self.book_path / '_quarto.yml', 'wt') as fobj:
            yaml.dump(self.yml_config, fobj)
        built_path = self.book_path / '_book'
        if built_path.exists():
            rmtree(built_path)
        for fn in glob(str(self.book_path / 'meta*.json')):
            unlink(fn)
        self.change_source()

    def change_source(self):
        pass

    def make_book(self, clobber=True):
        if self.book_path.is_dir():
            if clobber:
                shutil.rmtree(self.book_path)
            else:
                raise ValueError(f'{self.book_path} exists')
        self.get_book_source()
        extra = list(self.args) + ['--to=' + f for f in self.formats]
        run(['quarto', 'render', '.'] + list(extra), cwd=self.book_path)
        params = dict(book_path=self.book_path,
                      config_yml=self.yml_config,
                      nb_ext=self._nb_ext,
                      nb={},
                      nb_parsed={})
        if 'html' not in self.formats:  # Only HTML copies notebook.
            return params
        nb_dir = self.yml_config['noteout'].get('nb-dir', 'notebooks')
        self._nb, self._nb_parsed = read_notebook(
            self.book_path / '_book' / nb_dir /
            f'my_notebook.{self._nb_ext}')
        params['nb'] = self._nb.copy()
        params['nb_parsed'] = self._nb_parsed.copy()
        return params


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
        params = BookMaker(tmp_path, extra_config, lang).make_book()
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
    params = BookMaker(tmp_path, extra_config).make_book()
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
    params = BookMaker(tmp_path, extra_config).make_book()
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
    params = BookMaker(tmp_path, extra_config).make_book()
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
    params = BookMaker(tmp_path, extra_config).make_book()
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


def test_pdf_smoke(tmp_path):
    params = BookMaker(tmp_path, formats=('pdf',)).make_book()
    assert Path(params['book_path'] / '_book' / 'Quarto-example.pdf').is_file()


def unresolved_refs(nb_file):
    nb = jupytext.read(nb_file)
    nb_rmd = jupytext.writes(nb, 'Rmd')
    return re.findall('quarto-unresolved-ref', nb_rmd)


def test_proc_nbs(tmp_path):
    params = BookMaker(tmp_path).make_book()
    book_out = params['book_path'] / '_book'
    html_files = sorted(book_out.glob('**/*.html'))
    nb_file = book_out / 'my_notebook.ipynb'
    assert len(unresolved_refs(nb_file)) == 1
    assert len(html_files) == 4
    out_jl = tmp_path / 'jl_out'
    assert not out_jl.is_dir()
    nbp = NBProcessor(params['book_path'] / '_quarto.yml', out_jl)
    nbp.process()
    assert len(unresolved_refs(nb_file)) == 0
    assert (out_jl / 'jupyter-lite.json').is_file()
    nb_paths = sorted(out_jl.glob('**/*.ipynb'))
    assert len(nb_paths) == 1
    assert len(unresolved_refs(nb_paths[0])) == 0


class MBookMaker(BookMaker):

    def change_source(self):
        (self.book_path / 'intro.Rmd').write_text('''\
---
title: "My Document"
---

# Introduction

::: {.notebook name="my_notebook"}

Here is a paragraph.

::: {.callout-note}
## Note heading

Note text.
:::

Last text in notebook.
:::

Final text.
''')


def test_callout_note(tmp_path):
    params = MBookMaker(tmp_path).make_book()
    out = jupytext.writes(params['nb'], 'Rmd')
    assert re.match(r'''# My notebook$\s+
^Find this notebook on the web at.*?\s+
^Here is a paragraph\.$\s+
^\*\*Note: Note heading\*\*$\s+
^Note text\.$\s+
^\*\*End of Note: Note heading\*\*$\s+
^Last text in notebook\.
''', out, flags=re.MULTILINE | re.DOTALL)
