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

import panflute as pf

from noteout import filter_pre, filter_divspans, proc_nb_divs as pnd

from noteout.nutils import filter_doc, fmt2fmt

from .tutils import read_md, assert_json_equal, check_contains

import pytest


@pytest.fixture
def filtered_nb1(nb1_doc):
    metadata = {'noteout': {
        'pre-filter': ['todo', 'comment'],
        'filter-divspans': ['python']}}
    nb1_doc.metadata = metadata
    de_pre = filter_doc(nb1_doc, filter_pre.PreFilter)
    de_pre.metadata = metadata
    return filter_doc(de_pre, filter_divspans.DivSpanFilter)


def test_first_pass(filtered_nb1):
    # Unfiltered does have notebook divs.
    is_nb_div = lambda e, d: pnd.is_nb_div(e)
    assert check_contains(filtered_nb1, is_nb_div)
    # Filtered does not (it has been flattened).
    out_doc = filter_doc(filtered_nb1, pnd)
    assert not check_contains(out_doc, is_nb_div)



INP_RMD = """\
Some text.

::: {.notebook name="a_notebook" title='A notebook'}
Here, again, is a paragraph.

```{r}
a <- 10
```

More text.
:::"""

# Note compression of code blocks.  This is an artefact of the pure Pandoc
# processing, and does not occur with the Quarto processing pipeline.
HTML_RMD = """\
Some text.

:::{#nte-a_notebook .callout-note}
## Notebook: A notebook

<div class="nb-links">
<a class="notebook-link" href=notebooks/a_notebook.Rmd>Download notebook</a>
<a class="interact-button" href="/interact/lab/index.html?path=a_notebook.Rmd">Interact</a>\n')
</div>
:::

[]{.nb-start}

::: nb-only
Find this notebook on the web at @nte-a_notebook.
:::

Here, again, is a paragraph.

`{r} a <- 10`

More text.

[]{.nb-end}

:::{.callout-note}
## End of notebook: A notebook

The notebook (`a_notebook`) starts at @nte-a_notebook.
:::"""

LATEX_RMD = """\
Some text.

:::{#nte-a_notebook .callout-note}
## Notebook: A notebook

* [Download notebook](https://resampling-stats.github.io/latest-r/notebooks/a_notebook.Rmd)
* [Interact](https://resampling-stats.github.io/latest-r/interact/lab/index.html?path=a_notebook.Rmd)
:::

[]{.nb-start}

::: nb-only
Find this notebook on the web at @nte-a_notebook.
:::

Here, again, is a paragraph.

`{r} a <- 10`

More text.

[]{.nb-end}

:::{.callout-note}
## End of notebook: A notebook

The notebook (`a_notebook`) starts at @nte-a_notebook.
:::"""


def test_examples():
    in_doc = fmt2fmt(INP_RMD, out_fmt='panflute')
    is_nb_div = lambda e, d: pnd.is_nb_div(e)
    assert check_contains(in_doc, is_nb_div)
    out_doc = filter_doc(in_doc, pnd)
    assert not check_contains(out_doc, is_nb_div)
    out_md = fmt2fmt(out_doc, out_fmt='markdown')
    # When we don't know the output format, we get the LaTeX version.
    # assert out_md == LATEX_RMD
