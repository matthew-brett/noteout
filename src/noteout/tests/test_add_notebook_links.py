""" Test processing of notebook divs.

* Notebook start and end note should suitably create Interact and Download
  buttons or the LaTeX URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
* For notebooks with data files, the Download link should be to a zip archive.
"""

from pathlib import Path

import noteout.add_notebook_links as anbL

from noteout.nutils import fmt2fmt, FilterError, filter_doc

from .tutils import filter_doc_nometa, fmt2md
from .test_mark_notebooks import OUT_RMD as MARKED_RMD

import pytest

LATEX_RMD = """\
Some text.

::: {#nte-a_notebook .callout-note}
## Notebook: This is a notebook

* [Download notebook](https://resampling-stats.github.io/latest-r/notebooks/a_notebook.Rmd)
* [Interact](https://resampling-stats.github.io/latest-r/interact/lab/index.html?path=a_notebook.Rmd)
:::

::: {.nb-start name="a_notebook" title="This is a notebook"}

:::

::: nb-only
Find this notebook on the web at @nte-a_notebook.
:::

Here, again, is a paragraph.

```{r}
a <- 10
```

More text.

::: {.nb-end}

:::

::: {.callout-note}
## End of notebook: This is a notebook

`a_notebook` starts at @nte-a_notebook.
:::"""

HTML_RMD = """\
Some text.

::: {#nte-a_notebook .callout-note}
## Notebook: This is a notebook

<div class="nb-links">
<a class="notebook-link" href="notebooks/a_notebook.Rmd">Download notebook</a>
<a class="interact-button" href="/interact/lab/index.html?path=a_notebook.Rmd">Interact</a>
</div>
:::

::: {.nb-start name="a_notebook" title="This is a notebook"}

:::

::: nb-only
Find this notebook on the web at @nte-a_notebook.
:::

Here, again, is a paragraph.

```{r}
a <- 10
```

More text.

::: {.nb-end}

:::

::: {.callout-note}
## End of notebook: This is a notebook

`a_notebook` starts at @nte-a_notebook.
:::"""


def test_examples(in_tmp_path):
    in_doc = fmt2fmt(MARKED_RMD, out_fmt='panflute')
    # We need to add the relevant metadata
    with pytest.raises(FilterError):
        filter_doc(in_doc, anbL)
    # Some but not all
    in_doc.metadata = {'noteout': {
        'book-url-root': 'https://resampling-stats.github.io/latest-r',
        'interact-url': "/interact/lab/index.html?path=",
        'language': 'r',
        'nb-dir': "notebooks"}}
    with pytest.raises(FilterError, match='noteout.nb-format must be defined'):
        filter_doc(in_doc, anbL)
    # All, so now we check for the output notebook.
    in_doc.metadata['noteout']['nb-format'] = 'Rmd'
    with pytest.raises(FilterError, match='" does not exist'):
        filter_doc(in_doc, anbL)
    # Write a fake notebook.
    out_nb_path = Path('notebooks')
    out_nb_path.mkdir()
    (out_nb_path / 'a_notebook.Rmd').write_text('Some text')
    # The filter now works.
    out_doc = filter_doc_nometa(in_doc, anbL)
    # When we don't know the output format (from the metadata), we get the
    # LaTeX version.
    assert fmt2md(out_doc) == fmt2md(LATEX_RMD)
    # Unless HTML specified.
    in_doc.metadata['quarto-doc-params'] = {'out_format': 'html'}
    out_doc_html = filter_doc_nometa(in_doc, anbL)
    assert fmt2md(out_doc_html) == fmt2md(HTML_RMD)
    # Remove title to generate error.
    no_title_rmd = MARKED_RMD.replace(' title="This is a notebook"', '')
    in_doc_nt = fmt2fmt(no_title_rmd, out_fmt='panflute')
    in_doc_nt.metadata = in_doc.metadata
    with pytest.raises(FilterError, match='title must be defined'):
        filter_doc(in_doc_nt, anbL)
    # Try adding a data file to notebook.
    data_path = Path('data')
    data_path.mkdir()
    in_data = data_path / 'df.csv'
    in_data.write_text('a,b\n1,2\n3,4')
    (out_nb_path / 'a_notebook.Rmd').write_text(
        '''\
```{r}
df <- read.csv("data/df.csv")
```''')
    out_with_data = filter_doc_nometa(in_doc, anbL)
    assert (out_nb_path / 'data').is_dir()
    assert (out_nb_path / 'data' / 'df.csv').is_file()
    assert (out_nb_path / 'a_notebook.zip').is_file()
    data_rmd = (
        HTML_RMD.replace(
            'Download notebook',
            'Download zip with notebook + data file')
        .replace(
            'notebooks/a_notebook.Rmd',
            'notebooks/a_notebook.zip'))
    assert fmt2md(out_with_data) == fmt2md(data_rmd)
    # Two data files.
    in_data = data_path / 'df2.csv'
    in_data.write_text('a,b\n1,2\n3,4')
    (out_nb_path / 'a_notebook.Rmd').write_text(
        '''\
```{r}
df <- read.csv("data/df.csv")
df2 <- read.csv("data/df2.csv")
```''')
    out_with_data2 = filter_doc_nometa(in_doc, anbL)
    assert (out_nb_path / 'data' / 'df2.csv').is_file()
    data_rmd = data_rmd.replace('+ data file', '+ data files')
    assert fmt2md(out_with_data2) == fmt2md(data_rmd)
