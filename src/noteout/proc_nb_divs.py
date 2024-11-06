#!/usr/bin/env python3
""" Panflute filter to mark up text for notebooks.

The first pass (pre-pass) does these steps:

* Flatten notebook divs.
* Drop in Quarto notes before and after flatted div.
* The notes should suitably create Interact and Download buttons or the LaTeX
  URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
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

The HTML output should be::

    Some text.

    ::: {#nte-a_notebook .callout-note}
    ## Notebook: A notebook

    <div class="nb-links">
    <a class="notebook-link" href="notebooks/a_notebook.Rmd">Download notebook</a>
    <a class="interact-button" href="/interact/lab/index.html?path=a_notebook.Rmd">Interact</a>\n')
    </div>
    :::
    []{.nb-start}

    ::: nb-only
    Find this notebook on the web at @nte-a_notebook.
    :::

    Here, again, is a paragraph.

    ```{r}
    a <- 10
    ```

    More text.

    []{.nb-end}
    ::: {.callout-note}
    ## End of notebook: A notebook

    The notebook (`a_notebook`) starts at @nte-a_notebook.
    :::

The LaTeX output (or when we don't know the output format) differs only in the
interact and download links:

    ::: {#nte-a_notebook .callout-note}
    ## Notebook: A notebook

    * [Download notebook](https://resampling-stats.github.io/latest-r/notebooks/a_notebook.Rmd)
    * [Interact](https://resampling-stats.github.io/latest-r/interact/lab/index.html?path=a_notebook.Rmd)
    :::

We have to do a first pass like this, before the Quarto filters, so Quarto can
expand Quarto-specific stuff like cross-references inside the notebook text.
"""

import panflute as pf

from noteout.nutils import fmt2fmt, FilterError

_REQUIRED_NOTEOUT_KEYS = ('book-url-root', 'nb-dir', 'nb-format')


def prepare(doc):
    params = doc.get_metadata('noteout', {})
    for key in _REQUIRED_NOTEOUT_KEYS:
        if not key in params:
            raise FilterError(f'noteout.{key} must be defined in metadata')
    if params.get('url-nb-suffix') is None:
        params['url-nb-suffix'] = '.' + params.get('nb-format', 'ipynb')
    doc._params = params


def finalize(doc):
    del doc._params


def is_nb_div(elem):
    if not isinstance(elem, pf.Div):
        return False
    return 'notebook' in elem.classes


def proc_nb_div(elem, doc):
    name = elem.attributes.get('name')
    if name is None:
        raise FilterError('Need name attribute for notebook')
    params = doc._params.copy()
    params.update({
        'name': name,
        'title': elem.attributes.get('title', name2title(name))
    })
    if doc.get_metadata('quarto-doc-params.out_format') == 'html':
        dl_inter_md = '''\
<div class="nb-links">
<a class="notebook-link" href="{nb-dir}/{name}.{nb-format}">Download notebook</a>
<a class="interact-button" href="{interact-url}{name}{url-nb-suffix}">Interact</a>\n')
</div>'''.format(**params)
    else:  # Generic format.
        dl_inter_md = '''\
* [Download notebook]({book-url-root}/{nb-dir}/{name}.{nb-format})
* [Interact]({book-url-root}{interact-url}{name}{url-nb-suffix})
'''.format(**params)
    header = '''\
::: {{#nte-{name} .callout-note}}
## Notebook: {title}

{dl_inter_md}
:::

[]{{.nb-start}}

::: nb-only
Find this notebook on the web at @nte-{name}.
:::
'''.format(**{'dl_inter_md': dl_inter_md, **params})
    footer = '''\
[]{{.nb-end}}

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
