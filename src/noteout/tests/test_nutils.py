""" Test nutils module
"""

import jupytext as jpt

from noteout.nutils import find_data_files


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
