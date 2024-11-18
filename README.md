# Noteout

Pandoc filters for, among other things, extracting embedded notebooks,
replacing with suitable link material.

See the example [Quarto](https://quarto.org) book project in
`quarto-example` for a quickstart.

If you are using these filters with Quarto, as we are, you will need Quarto >=
1.4, because it has mechanisms to run filters at different stages of the
filtering process.  See [this change
note](https://quarto.org/docs/prerelease/1.4/lua_changes.html#more-precise-targeting-of-ast-processing-phases)
for more information.

Install with:

```
pip install noteout
```

or (for latest git version):

```
pip install git+https://github.com/matthew-brett/noteout
```

This allows you to delineate notebooks in your pages with markup of form:

~~~
Information in page.

::: {.notebook name="a_notebook"}
Some text.

```{r}
# Some code
```
:::

More information in page.

::: {.notebook name="b_notebook"}
More text.

```{r}
# More code
```
:::
~~~

Say your filters are in a subdirectory `filters`.

Start by copying `extras/wrap_noteout.py` and `extras/add-meta.lua` to your `filters` directory above.

Make the Noteout code into local executable filters with:

```bash
cd filters
ln -s wrap_notebooks.py mark_notebooks.py
ln -s wrap_notebooks.py export_notebooks.py
ln -s wrap_notebooks.py add_notebook_links.py
```

This linking sets up the filters by making them single executable files in your Quarto tree — a requirement for Quarto filters.   You could also have copied the relevant files from the Noteout source.

Use these filters with something like the following in your `_quarto.yml` file.  Remember, Noteout depends on features in Quarto 1.4, so expect this configuration to fail in earlier versions.

```yaml
filters:
  - at: pre-ast
    path: filters/add-meta.lua
  - at: pre-ast
    type: json
    path: filters/mark_notebooks.py
  - at: post-quarto
    type: json
    path: filters/export_notebooks.py
  - at: post-quarto
    type: json
    path: filters/filter_nb_only.py

noteout:
  nb-format: Rmd
  interact-url: "/interact/lab/index.html?path="
  url-root: https://resampling-stats.github.io
  book-url-root: https://resampling-stats.github.io/latest-r
  nb-dir: notebooks
```

By default, Noteout writes your notebooks to your Quarto `output-dir`. In the
example above, Noteout would write `a_notebook.Rmd` and `b_notebook.Rmd` to
your `output-dir` directory.

See the [Resampling book](https://resampling-stats.github.io/resampling-with)
for a fully worked example, with extra configuration, and the [Resampling-with
Github repository](https://github.com/resampling-stats/resampling-with) for the
configuration and text source files.
