""" Test processing of notebook divs.

* Notebook start and end note should suitably create Interact and Download
  buttons or the LaTeX URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
* For notebooks with data files, the Download link should be to a zip archive.
"""

from noteout import filter_pre, filter_divspans, add_notebooks_links as anbL

from noteout.nutils import fmt2fmt, FilterError, filter_doc

from .tutils import check_contains, filter_doc_nometa, assert_md_rt_equal
from .test_mark_notebooks import OUT_RMD as MARKED_RMD

import pytest

HTML_RMD = """\
Some text.

::: {#nte-a_notebook .callout-note name="a_notebook" title="This is a notebook"}
## Notebook: A notebook

<div class="nb-links">
<a class="notebook-link" href="notebooks/a_notebook.Rmd">Download notebook</a>
<a class="interact-button" href="/interact/lab/index.html?path=a_notebook.Rmd">Interact</a>\n')
</div>
:::

::: nb-only
Find this notebook on the web at @nte-a_notebook.
:::

Here, again, is a paragraph.

```{r}
a <- 10
```

More text.

::: {.callout-note}
## End of notebook: This is a notebook

The notebook `a_notebook` starts at @nte-a_notebook.
:::"""

LATEX_RMD = """\
Some text.

::: {#nte-a_notebook .callout-note name="a_notebook" title="This is a notebook"}
## Notebook: A notebook

* [Download notebook](https://resampling-stats.github.io/latest-r/notebooks/a_notebook.Rmd)
* [Interact](https://resampling-stats.github.io/latest-r/interact/lab/index.html?path=a_notebook.Rmd)
:::

::: nb-only
Find this notebook on the web at @nte-a_notebook.
:::

Here, again, is a paragraph.

```{r}
a <- 10
```

More text.

::: {.callout-note}
## End of notebook: A notebook

The notebook `a_notebook` starts at @nte-a_notebook.
:::"""


def test_examples():
    in_doc = fmt2fmt(MARKED_RMD, out_fmt='panflute')
    is_nb_div = lambda e, d: anbL.is_nb_div(e)
    assert check_contains(in_doc, is_nb_div)
    # We need to add the relevant metadata
    with pytest.raises(FilterError):
        filter_doc(in_doc, pnd)
    # Some but not all
    in_doc.metadata = {'noteout': {
        'book-url-root': 'https://resampling-stats.github.io/latest-r',
        'interact-url': "/interact/lab/index.html?path=",
        'nb-dir': "notebooks"}}
    with pytest.raises(FilterError):
        filter_doc(in_doc, pnd)
    # All
    in_doc.metadata['noteout']['nb-format'] = 'Rmd'
    out_doc = filter_doc_nometa(in_doc, pnd)
    assert not check_contains(out_doc, is_nb_div)
    # When we don't know the output format (from the metadata), we get the
    # LaTeX version.
    assert_md_rt_equal(out_doc, LATEX_RMD)
    # Unless HTML specified.
    in_doc.metadata['quarto-doc-params'] = {'out_format': 'html'}
    out_doc_html = filter_doc_nometa(in_doc, pnd)
    assert_md_rt_equal(out_doc_html, HTML_RMD)
