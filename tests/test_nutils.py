""" Test nutils module
"""

from pathlib import Path

import jupytext as jpt
import panflute as pf

from noteout.nutils import find_data_files, quartoize, fill_params, FilterError

import pytest


def test_find_data_files(tmp_path):
    nb = jpt.reads(
        '''\
```{r}
df <- read.csv("data/df.csv")
```''', 'Rmd')
    assert find_data_files(nb) == ['data/df.csv']
    # Can find multiple file reads in one cell.
    nb = jpt.reads(
        '''\
```{r}
df <- read.csv("data/df.csv")
df2 <- read.csv("data/df2.csv")
```''', 'Rmd')
    assert find_data_files(nb) == ['data/df.csv', 'data/df2.csv']
    # Can find matches in different cells.
    nb = jpt.reads(
        '''\
```{r}
df <- read.csv("data/df.csv")
df2 <- read.csv("data/df2.csv")
```

Some text

```{r}
df2 <- read.csv("some_file.csv")
```''', 'Rmd')
    assert (find_data_files(nb) ==
            ['data/df.csv', 'data/df2.csv', 'some_file.csv'])
    # Matches are sorted and unique.
    nb = jpt.reads(
        '''\
```{r}
df2 <- read.csv("data/df2.csv")
df <- read.csv("data/df.csv")
df1 <- read.csv("data/df.csv")
```''', 'Rmd')
    assert find_data_files(nb) == ['data/df.csv', 'data/df2.csv']


def test_quartoize():
    assert quartoize('') == ''
    in_str = '''\
T1

```{r}
a <- 1
```

T2

```{python}
c = 1
c
```
T2'''
    exp_str = '''\
T1

::: cell

```{.r .cell-code}
a <- 1
```

:::

T2

::: cell

```{.python .cell-code}
c = 1
c
```

:::

T2'''
    assert quartoize(in_str) == exp_str
    assert (
        quartoize('Text\n```{r eval=True}\na <- 1\n```') ==
        'Text\n\n::: cell\n```{.r .cell-code eval=True}\na <- 1\n```'
        '\n\n:::\n')


def test_fill_params():
    meta = pf.MetaMap()
    default = {
        'nb-build-formats': ['*'],
        'nb-dir': 'notebooks',
        'nb-format': 'ipynb',
        'nb-strip-header-nos': True,
        'nb-flatten-divspans': {'header-section-number', 'nb-only'},
        'out_format': None,
        'output_directory': Path(),
        'interact-nb-suffix': '.ipynb',
        'nb_out_path': Path('.') / 'notebooks'
    }
    assert fill_params(meta) == default
    with pytest.raises(FilterError,
                       match='noteout.interact-url must be defined'):
        fill_params(meta, ('noteout.interact-url',))
    meta['noteout'] = {'interact-url': 'https://example.com'}
    exp = default.copy()
    exp['interact-url'] = 'https://example.com'
    assert fill_params(meta, ('noteout.interact-url',)) == exp
