""" Test processing of notebook divs.

* Remove / flatten notebook divs.
* Drop notes before and after flatted div.
* The notes should suitably create Interact and Download buttons or the LaTeX
  URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
* As well as the top-note, there should be a nb-only div with a link back to
  the web version of the notebook.  This could be a link to the note label for
  HTML output, but maybe we can omit this for the LaTeX case (because we won't
  generally be generating the notebooks from the LaTeX build).
"""

from noteout import filter_pre, filter_divspans, mark_notebooks as mnb

from noteout.nutils import fmt2fmt, filter_doc

from .tutils import check_contains, filter_doc_nometa, fmt2md

import pytest


@pytest.fixture
def filtered_nb1(nb1_doc):
    metadata = {'noteout': {
        'pre-filter': ['todo', 'comment'],
        'filter-divspans': ['python']}}
    nb1_doc.metadata = metadata
    de_pre = filter_doc_nometa(nb1_doc, filter_pre.PreFilter)
    de_pre.metadata = metadata
    return filter_doc(de_pre, filter_divspans.DivSpanFilter)


INP_RMD = """\
Some text.

::: {.notebook name="a_notebook" title="This is a notebook"}
Here, again, is a paragraph.

```{r}
a <- 10
```

More text.
:::"""

OUT_RMD = """\
Some text.

::: {#nte-a_notebook .callout-note .nb-start name="a_notebook" title="This is a notebook"}
## Notebook: This is a notebook
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

`a_notebook` starts at @nte-a_notebook.
:::"""


def test_examples():
    in_doc = fmt2fmt(INP_RMD, out_fmt='panflute')
    is_nb_div = lambda e, d: mnb.is_nb_div(e)
    assert check_contains(in_doc, is_nb_div)
    out_doc = filter_doc_nometa(in_doc, mnb)
    assert not check_contains(out_doc, is_nb_div)
    assert fmt2md(out_doc) == fmt2md(OUT_RMD)
    # Remove specific title.
    no_title_rmd = INP_RMD.replace(' title="This is a notebook"', '')
    out_no_title_rmd = OUT_RMD.replace('This is a notebook', 'A notebook')
    in_doc = fmt2fmt(no_title_rmd, out_fmt='panflute')
    out_doc = filter_doc_nometa(in_doc, mnb)
    assert fmt2md(out_doc) == fmt2md(out_no_title_rmd)
