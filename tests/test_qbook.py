""" Test rendering of a project
"""

from fnmatch import fnmatch
from os import listdir
from pathlib import Path
import re
from subprocess import run as sp_run
from copy import deepcopy
from collections.abc import Mapping
from hashlib import sha1
import json

import yaml
import jupytext
import panflute as pf

from noteout.process_notebooks import NBProcessor

import pytest

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


class GitignoreMatcher:

    def __init__(self, gitignore_path):
        self.gitignore_path = Path(gitignore_path)
        self.root_path = self.gitignore_path.parent
        self.rel_fpats = []
        self.rel_dpats = []
        self.abs_fpats = []
        self.abs_dpats = []
        self._parse()

    def _parse(self):
        if not self.gitignore_path.is_file():
            return
        for line in self.gitignore_path.read_text().splitlines():
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            if line.endswith('/'):
                line = line.rstrip('/')
                if '/' in line:
                    line = line.lstrip('/')
                    self.abs_dpats += [line, line + '/**']
                else:
                    self.rel_dpats.append(line)
                continue
            if '/' in line:
                self.abs_fpats.append(line.strip('/'))
            else:
                self.rel_fpats.append(line)

    def _dir_matches(self, dir_path):
        for pat in self.abs_dpats:
            if fnmatch(dir_path, pat):
                return True
        for dp_part in dir_path.parts:
            for pat in self.rel_dpats:
                if fnmatch(dp_part, pat):
                    return True
        return False

    def _fn_matches(self, path):
        for pat in self.abs_fpats:
            if fnmatch(path, pat):
                return True
        name = path.name
        for pat in self.rel_fpats:
            if fnmatch(name, pat):
                return True
        return False

    def filtered(self):
        for fp in self.root_path.rglob('*'):
            rel_fp = fp.relative_to(self.root_path)
            rel_dp = rel_fp if fp.is_dir() else rel_fp.parent
            if self._dir_matches(rel_dp):
                continue
            if self._fn_matches(rel_fp):
                continue
            yield fp

    def copytree_filtered(self, out_path):
        out_path = Path(out_path)
        out_path.mkdir(parents=True, exist_ok=True)
        out = []
        for fp in self.filtered():
            out_fp = out_path / fp.relative_to(self.root_path)
            if fp.is_dir():
                out_fp.mkdir(parents=True, exist_ok=True)
            else:
                content = fp.read_bytes()
                out_fp.write_bytes(content)
            out.append(out_fp)
        return out


class BookMaker:

    model_path = QBOOK_PATH

    def __init__(self, root_path,
                 extra_config=None,
                 lang='Python',
                 name=None,
                 args=(),
                 formats=('html',)):
        self.root_path = Path(root_path).absolute()
        self.extra_config = extra_config if extra_config else {}
        self.lang = lang
        start_config = get_yml_config(self.model_path / '_quarto.yml',
                                      self.lang)
        self.yml_config = merge_dict(start_config, self.extra_config)
        self.name = name if name else dicthash(self.yml_config)
        self.args = args
        self.formats = formats
        self.book_path = self.root_path / self.name
        _render_dir = (self.yml_config.get('project', {})
                            .get('output-dir', '_book'))
        self.render_path = self.book_path / _render_dir
        nb_dir = self.yml_config['noteout'].get('nb-dir', 'notebooks')
        self.nb_path = self.render_path / nb_dir
        self._nb_ext = self.yml_config['noteout']['nb-format']
        self.nbs = {}
        self._manifest = []
        self.prepare_book()

    def prepare_book(self):
        self.manifest = (GitignoreMatcher(self.model_path / '.gitignore')
                         .copytree_filtered(self.book_path))

    def render(self):
        self.nbs = {}
        with open(self.book_path / '_quarto.yml', 'wt') as fobj:
            yaml.dump(self.yml_config, fobj)
        if self.book_path.is_dir():
            sp_run(['quarto', 'render', '--clean'], cwd=self.book_path)
        extra = list(self.args) + ['--to=' + f for f in self.formats]
        sp_run(['quarto', 'render', '.'] + list(extra), cwd=self.book_path)
        for nb_path in (self.nb_path).glob(f'**/*.{self._nb_ext}'):
            if nb_path in self.manifest:
                continue
            nb = jupytext.read(nb_path)
            self.nbs[str(nb_path.relative_to(self.book_path))] = nb


def nb2panflute(nb):
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
    return parsed_cells


def dicthash(d, **kwargs):
    d = deepcopy(d)
    d.update(kwargs)
    return sha1(json.dumps(d).encode('latin1')).hexdigest()


@pytest.mark.parametrize("lang", ['R', 'Python'])
def test_qbook_render(tmp_path, lang):
    # Test qbook build.
    # Output from write_meta filter.
    metas = set([f'meta_{i:03d}.json' for i in range(4)])
    docs = set([f'doc_{i:03d}.json' for i in range(4)])
    extra_config = {'noteout': {'pre-filter': ['comment']}}
    if lang == 'Python':
        extra_config['interact-url'] = (
            'https://mybinder.org/v2/gh/resampling-stats/'
            'resampling-with/gh-pages?filepath=python-book/')
    bm = BookMaker(tmp_path, extra_config, lang)
    bm.render()
    tmp_qbook = bm.book_path
    # Check meta files from write_meta
    source_listing = listdir(tmp_qbook)
    assert metas <= set(source_listing)
    # Check doc files from write_doc
    assert docs <= set(source_listing)
    # Check book generation.
    book_dir = tmp_qbook / '_book'
    for fn in ('index.html', 'intro.html'):
        assert (bm.render_path / fn).is_file()
    # Check notebook generation.
    nb_ext = 'Rmd' if lang == 'R' else 'ipynb'
    assert (bm.nb_path / f"my_notebook.{nb_ext}").is_file()
    # We aren't building the other notebook type.
    other_ext = 'ipynb' if lang == 'R' else 'Rmd'
    assert not (bm.nb_path / f"my_notebook.{other_ext}").is_file()
    with open(book_dir / 'intro.html', 'rt') as fobj:
        intro_contents = fobj.read()
    assert NB_ONLY_STR not in intro_contents
    # Check notebook contents
    assert len(bm.nbs) == 1
    nb = next(iter(bm.nbs.values()))
    # There will be 7 cells if output left in notebook.
    assert len(nb.cells) == 5
    # Check contents of first cell.
    parsed = nb2panflute(nb)
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
    bm = BookMaker(tmp_path, extra_config)
    bm.render()
    parsed = nb2panflute(next(iter(bm.nbs.values())))
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
    bm = BookMaker(tmp_path, extra_config)
    bm.render()
    parsed = nb2panflute(next(iter(bm.nbs.values())))
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
    bm = BookMaker(tmp_path, extra_config)
    bm.render()
    parsed = nb2panflute(next(iter(bm.nbs.values())))
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
    bm = BookMaker(tmp_path, extra_config)
    bm.render()
    parsed = nb2panflute( next(iter(bm.nbs.values())))
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
    bm = BookMaker(tmp_path, formats=('pdf',))
    bm.render()
    assert Path(bm.book_path / '_book' / 'Quarto-example.pdf').is_file()


def unresolved_refs(nb_file):
    nb = jupytext.read(nb_file)
    nb_rmd = jupytext.writes(nb, 'Rmd')
    return re.findall('quarto-unresolved-ref', nb_rmd)


def test_proc_nbs(tmp_path):
    bm = BookMaker(tmp_path)
    bm.render()
    html_files = sorted(bm.render_path.glob('**/*.html'))
    assert len(html_files) == 4
    nb_file = bm.nb_path / 'my_notebook.ipynb'
    assert len(unresolved_refs(nb_file)) == 1
    out_jl = tmp_path / 'jl_out'
    assert not out_jl.is_dir()
    nbp = NBProcessor(bm.book_path / '_quarto.yml', out_jl)
    nbp.process()
    assert len(unresolved_refs(nb_file)) == 0
    assert (out_jl / 'jupyter-lite.json').is_file()
    nb_paths = sorted(out_jl.glob('**/*.ipynb'))
    assert len(nb_paths) == 1
    assert len(unresolved_refs(nb_paths[0])) == 0


CALLOUT_NB_RMD = '''\
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
'''


def test_callout_note(tmp_path):
    bm = BookMaker(tmp_path)
    (bm.book_path / 'intro.Rmd').write_text(CALLOUT_NB_RMD)
    bm.render()
    assert len(bm.nbs) == 1
    nb = next(iter(bm.nbs.values()))
    out = jupytext.writes(nb, 'Rmd')
    assert re.match(r'''# My notebook$\s+
^Find this notebook on the web at.*?\s+
^Here is a paragraph\.$\s+
^\*\*Note: Note heading\*\*$\s+
^Note text\.$\s+
^\*\*End of Note: Note heading\*\*$\s+
^Last text in notebook\.
''', out, flags=re.MULTILINE | re.DOTALL)
