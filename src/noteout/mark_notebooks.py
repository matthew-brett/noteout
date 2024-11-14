#!/usr/bin/env python3
""" Panflute filter to mark up text for notebooks.

Filtering is in two stages (see below for why):

* Replace notebook Pandoc divs with notebook start and end markers.  (Why?
  Because the divs prevent Quarto from doing its normal contents table.  And
  because we want to drop #nte-my_notebook section markers which we can use to
  reference the notebook). We drop download and interaction links into these
  section markers.  Also - because we want to use callout-notes for the
  notebook head and tail markers, and these need to be processed before Quarto
  gets to them, at the (in Quarto's terms) ``pre-ast`` phase of filtering.
* (At some point, run the Quarto filters, then):
* Parse the start and end markers to find the notebooks, then write out the
  notebook files after suitable processing. In this phase, we work out which
  notebooks have data files associated, and write out zips for download of
  notebooks with data files.

This first pass does these steps:

* Flatten notebook divs.
* Drop in Quarto notes before and after flattened div, and add download links.
* Drop in nb-start and nb-end markers before and after flattened div.  We need
  separated start and end markers because Quarto won't let us add classes or
  attributes to the Quarto notes (above).  See:
  `https://github.com/quarto-dev/quarto-cli/issues/11362`_.
* As well as the top-note, there should be a nb-only div with a link back to
  the web version of the notebook.  This could be a link to the note label for
  HTML output.

For example, given::

    Some text.

    ::: {.notebook name="a_notebook" title='A notebook'}
    Here, again, is a paragraph.

    ```{r}
    a <- 10
    ```

    More text.
    :::

The output should be (in this case for default / LaTeX build)::

    Some text.

    ::: {#nte-a_notebook .callout-note,
    ## Notebook: A notebook
    * [Download notebook](https://resampling-stats.github.io/latest-r/notebooks/a_notebook.Rmd)
    * [Interact](https://resampling-stats.github.io/latest-r/interact/lab/index.html?path=a_notebook.Rmd)
    :::

    ::: {.nb-start name="a_notebook" title="A notebook"}

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
    ## End of notebook: A notebook

    `a_notebook` starts at @nte-a_notebook.
    :::

We have to do a first pass like this, before the Quarto filters, so Quarto can
expand Quarto-specific stuff such as cross-references inside the notebook text.
"""

import os.path as op

import jupytext as jpt
import panflute as pf

from noteout.nutils import (fmt2fmt, FilterError, is_div_class, name2title,
                            find_data_files, fill_params)
from noteout.export_notebooks import proc_nb_text


_REQUIRED_NOTEOUT_KEYS = ('noteout.book-url-root',
                          'noteout.interact-url')


def prepare(doc):
    p = fill_params(doc.metadata, required_keys=_REQUIRED_NOTEOUT_KEYS)
    p['interact-url'] = '/' + p['interact-url'].lstrip('/')
    doc._params = p


def finalize(doc):
    del doc._params


def is_nb_div(elem):
    return is_div_class(elem, 'notebook')


def proc_nb_div(elem, doc, n_data_files):
    name = elem.attributes.get('name')
    if name is None:
        raise FilterError('Need name attribute for notebook')
    params = {**doc._params,
              'name': name,
              'title': elem.attributes.get('title', name2title(name)),
              'link_text': get_nb_links(elem, doc, n_data_files)
    }
    header = '''\
::: {{#nte-{name} .callout-note}}
## Notebook: {title}

{link_text}
:::

::: {{.nb-start name="{name}" title="{title}"}}

:::

::: nb-only
Find this notebook on the web at @nte-{name}.
:::
'''.format(**params)
    footer = '''\
::: {{.nb-end}}

:::

::: {{.callout-note}}
## End of notebook: {title}

`{name}` starts at @nte-{name}.
:::'''.format(**params)
    return (fmt2fmt(header, out_fmt='panflute').content,
            fmt2fmt(footer, out_fmt='panflute').content)


def get_nb_links(elem, doc, n_dfs):
    params = doc._params.copy()
    params.update(elem.attributes)
    params['dl_rel_url'] = get_dl_rel_url(params, n_dfs)
    params['dl_text'] = ('notebook' if n_dfs == 0 else
                         ('zip with notebook + data file' +
                          ('s' if n_dfs > 1 else '')))
    params['inter_url'] = ('{interact-url}{name}{url-nb-suffix}'
                           .format(**params))
    if doc.get_metadata('quarto-doc-params.out_format') == 'html':
        txt = '''\
<div class="nb-links">
<a class="notebook-link" href="{dl_rel_url}">Download {dl_text}</a>
<a class="interact-button" href="{inter_url}">Interact</a>
</div>'''.format(**params)
    else:  # Generic format.
        txt = '''\
* [Download {dl_text}]({book-url-root}/{dl_rel_url})
* [Interact]({book-url-root}{inter_url})
'''.format(**params)
    return txt


def get_dl_rel_url(params, n_dfs):
    params['ext'] = 'zip' if n_dfs else params['nb-format']
    return '{nb-dir}/{name}.{ext}'.format(**params).replace(op.sep, '/')


def action(elem, doc):
    if not is_nb_div(elem):
        return
    # Flatten out div.  This avoids loss of Quarto sections inside divs.
    elem_out = list(elem.content)
    # Detect data files (for download links).
    nb_text = pf.convert_text(elem_out,
                              input_format='panflute',
                              output_format='gfm')
    dfs = find_data_files(jpt.reads(proc_nb_text(nb_text), 'Rmd'))
    # Add notes at beginning and end.
    header, footer = proc_nb_div(elem, doc, len(dfs))
    return list(header) + elem_out + list(footer)


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
