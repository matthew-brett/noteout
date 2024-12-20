""" Test processing of notebook divs.

* Remove / flatten notebook divs.
* Drop notes before and after flatted div.
* The notes should suitably create Interact and Download buttons or the LaTeX
  URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
* For notebooks with data files, the Download link should be to a zip archive.
* Drop nb-start and nb-end markers around the notebook, to allow
  `export_notebooks` to find and extract the notebooks.
* As well as the top-note, there should be a nb-only div with a link back to
  the web version of the notebook.  This could be a link to the note label for
  HTML output, but maybe we can omit this for the LaTeX case (because we won't
  generally be generating the notebooks from the LaTeX build).
"""

from copy import deepcopy

from noteout import mark_notebooks as mnb
from noteout.nutils import filter_doc, FilterError

from .tutils import check_contains, filter_doc_nometa, fmt2md, q2md, q2doc

import pytest

SIMPLE_NB = """\
Here, again, is a paragraph.

```{r}
a <- 10
```

More text."""

INP_RMD = """\
Some text.

::: {{.notebook name="a_notebook" title="This is a notebook"}}

{nb_text}

:::"""

OUT_RMD = """\
Some text.

::: {{#nte-a_notebook .callout-note}}
## Notebook: This is a notebook

{link_text}
:::

::: {{.nb-start name="a_notebook" title="This is a notebook"}}

:::

::: nb-only
Find this notebook on the web at @nte-a_notebook.
:::

{nb_text}

::: {{.nb-end}}

:::

::: {{.callout-note}}
## End of notebook: This is a notebook

`a_notebook` starts at @nte-a_notebook.
:::"""

DEF_LINK_TEXT = """\
* [Download notebook](https://resampling-stats.github.io/latest-r/notebooks/a_notebook.Rmd)
* [Interact](https://resampling-stats.github.io/latest-r/interact/lab/index.html?path=a_notebook.Rmd)"""

LATEX_RMD = OUT_RMD.format(link_text=DEF_LINK_TEXT, nb_text=SIMPLE_NB)

HTML_RMD = OUT_RMD.format(link_text="""\
<div class="nb-links">
<a class="notebook-link" href="notebooks/a_notebook.Rmd">Download notebook</a>
<a class="interact-button" href="/interact/lab/index.html?path=a_notebook.Rmd">Interact</a>
</div>""",
                          nb_text=SIMPLE_NB)

DATA_NB = '''\
```{r}
df <- read.csv("data/df.csv")
```'''

DATAS_NB = '''
```{r}
df <- read.csv("data/df.csv")
df2 <- read.csv("data/df2.csv")
```'''


def test_examples():
    def_rmd = INP_RMD.format(nb_text=SIMPLE_NB)
    in_doc = q2doc(def_rmd)
    is_nb_div = lambda e, d: mnb.is_nb_div(e)
    assert check_contains(in_doc, is_nb_div)
    # We need to add the relevant metadata.
    with pytest.raises(FilterError):
        filter_doc(in_doc, mnb)
    # Some but not all metadata.
    in_doc.metadata = {'noteout': {
        'nb-format': 'Rmd',
        'book-url-root': 'https://resampling-stats.github.io/latest-r'
    }}
    with pytest.raises(FilterError, match='noteout.interact-url must be defined'):
        filter_doc(in_doc, mnb)
    # All, so now we check for the output notebook.
    in_doc.metadata['noteout']['interact-url'] = "/interact/lab/index.html?path="
    out_doc = filter_doc_nometa(in_doc, mnb)
    assert not check_contains(out_doc, is_nb_div)
    assert fmt2md(out_doc) == fmt2md(LATEX_RMD, in_fmt='quarto-like')
    # HTML version.
    html_in_doc = deepcopy(in_doc)
    html_in_doc.metadata['quarto-doc-params'] = {'out_format': 'html'}
    out_doc = filter_doc_nometa(html_in_doc, mnb)
    assert fmt2md(out_doc) == fmt2md(HTML_RMD, in_fmt='quarto-like')
    # Remove specific title, get default.
    no_title_rmd = def_rmd.replace(' title="This is a notebook"', '')
    out_no_title_rmd = LATEX_RMD.replace('This is a notebook', 'A notebook')
    nt_in_doc = q2doc(no_title_rmd)
    nt_in_doc.metadata = in_doc.metadata
    nt_out_doc = filter_doc_nometa(nt_in_doc, mnb)
    assert fmt2md(nt_out_doc) == q2md(out_no_title_rmd)
    # Add data files.
    data_in_rmd = INP_RMD.format(nb_text=DATA_NB)
    data_out_rmd = OUT_RMD.format(link_text=DEF_LINK_TEXT, nb_text=DATA_NB)
    data_out_rmd = (
        data_out_rmd.replace(
            'Download notebook',
            'Download zip with notebook + data file')
        .replace(
            'notebooks/a_notebook.Rmd',
            'notebooks/a_notebook.zip'))
    data_in_doc = q2doc(data_in_rmd)
    data_in_doc.metadata = in_doc.metadata
    data_out_doc = filter_doc_nometa(data_in_doc, mnb)
    assert fmt2md(data_out_doc) == q2md(data_out_rmd)
    # More than one data file.
    data_in_rmd = INP_RMD.format(nb_text=DATAS_NB)
    data_out_rmd = OUT_RMD.format(link_text=DEF_LINK_TEXT, nb_text=DATAS_NB)
    data_out_rmd = (
        data_out_rmd.replace(
            'Download notebook',
            'Download zip with notebook + data files')
        .replace(
            'notebooks/a_notebook.Rmd',
            'notebooks/a_notebook.zip'))
    data_in_doc = q2doc(data_in_rmd)
    data_in_doc.metadata = in_doc.metadata
    data_out_doc = filter_doc_nometa(data_in_doc, mnb)
    assert fmt2md(data_out_doc) == q2md(data_out_rmd)
