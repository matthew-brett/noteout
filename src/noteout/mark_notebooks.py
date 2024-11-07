#!/usr/bin/env python3
""" Panflute filter to mark up text for notebooks.

Filtering is in three stages (see below for why):

* Replace notebook Pandoc divs with notebook start and end markers.  (Why?
  Because the divs prevent Quarto from doing it's normal contents table.  And
  because we want to drop #nte-my_notebook section markers which we can use to
  reference the notebook).
* (At some point, run the Quarto filters, then):
* Parse the start and end markers to find the notebooks, then write out the
  notebook files after suitable processing.
* In a last step, work out which notebooks have data files associated, write
  out zips for download of notebooks with data files, and drop interact and
  download links into the originating document.   (We have to do this last step
  separately because we don't know what the download links should link to until
  we know whether the notebooks have data files, and should therefore be
  ``.zip`` download links instead of notebook download links).

This first pass does these steps:

* Flatten notebook divs.
* Drop in Quarto notes before and after flatted div.
* As well as the top-note, there should be a nb-only div with a link back to
  the web version of the notebook.  This could be a link to the note label for
  HTML output, but maybe we can omit this for the LaTeX case (because we won't
  generally be generating the notebooks from the LaTeX build).

For example, given::

    Some text.

    ::: {.notebook name="a_notebook" title='A notebook'}
    Here, again, is a paragraph.

    ```{r}
    a <- 10
    ```

    More text.
    :::

The output should be::

    Some text.

    ::: {#nte-a_notebook .callout-note, name="a_notebook", title="A notebook"}
    ## Notebook: A notebook
    :::

    ::: nb-only
    Find this notebook on the web at @nte-a_notebook.
    :::

    Here, again, is a paragraph.

    ```{r}
    a <- 10
    ```

    More text.

    ::: {.callout-note .end-nb}
    ## End of notebook: A notebook

    The notebook (`a_notebook`) starts at @nte-a_notebook.
    :::

We have to do a first pass like this, before the Quarto filters, so Quarto can
expand Quarto-specific stuff such cross-references inside the notebook text.
"""

import panflute as pf

from noteout.nutils import fmt2fmt, FilterError

def prepare(doc):
    pass


def finalize(doc):
    pass


def is_nb_div(elem):
    if not isinstance(elem, pf.Div):
        return False
    return 'notebook' in elem.classes


def proc_nb_div(elem, doc):
    name = elem.attributes.get('name')
    if name is None:
        raise FilterError('Need name attribute for notebook')
    params = {
        'name': name,
        'title': elem.attributes.get('title', name2title(name))
    }
    header = '''\
::: {{#nte-{name} .callout-note name="{name}" title="{title}"}}
## Notebook: {title}
:::

::: nb-only
Find this notebook on the web at @nte-{name}.
:::
'''.format(**params)
    footer = '''\
::: {{.callout-note}}
## End of notebook: {title}

The notebook `{name}` starts at @nte-{name}.
:::'''.format(**params)
    return (fmt2fmt(header, out_fmt='panflute').content,
            fmt2fmt(footer, out_fmt='panflute').content)


def name2title(name):
    return name.replace('_', ' ').capitalize()


def action(elem, doc):
    if not is_nb_div(elem):
        return
    # Flatten out div.  This avoids loss of Quarto
    # sections inside divs.
    elem_out = list(elem.content)
    # Add notes at beginning and end.
    # header, footer = get_header_footer(name, doc, nb_path, out_path, df_paths)
    header, footer = proc_nb_div(elem, doc)
    return list(header) + elem_out + list(footer)


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
