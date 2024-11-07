""" Test processing of notebook divs.

* Notebook start and end note should suitably create Interact and Download
  buttons or the LaTeX URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
* For notebooks with data files, the Download link should be to a zip archive.
"""

import noteout.add_notebook_links as anbL

from noteout.nutils import fmt2fmt, FilterError, filter_doc

from .tutils import filter_doc_nometa, fmt2md
from .test_mark_notebooks import OUT_RMD as MARKED_RMD

import pytest

LATEX_RMD = """\
Some text.

::: {#nte-a_notebook .callout-note .nb-start name="a_notebook" title="This is a notebook"}
## Notebook: This is a notebook

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

::: {.callout-note .nb-end}
## End of notebook: This is a notebook

The notebook `a_notebook` starts at @nte-a_notebook.
:::"""

HTML_RMD = """\
Some text.

::: {#nte-a_notebook .callout-note .nb-start name="a_notebook" title="This is a notebook"}
## Notebook: This is a notebook

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

::: {.callout-note .nb-end}
## End of notebook: This is a notebook

The notebook `a_notebook` starts at @nte-a_notebook.
:::"""


def test_examples():
    in_doc = fmt2fmt(MARKED_RMD, out_fmt='panflute')
    # We need to add the relevant metadata
    with pytest.raises(FilterError):
        filter_doc(in_doc, anbL)
    # Some but not all
    in_doc.metadata = {'noteout': {
        'book-url-root': 'https://resampling-stats.github.io/latest-r',
        'interact-url': "/interact/lab/index.html?path=",
        'nb-dir': "notebooks"}}
    with pytest.raises(FilterError, match='noteout.nb-format must be defined'):
        filter_doc(in_doc, anbL)
    # All, so now we check for the output notebook.
    in_doc.metadata['noteout']['nb-format'] = 'Rmd'
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
