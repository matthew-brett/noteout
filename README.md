# Noteout

Pandoc filters for, among other things, extracting embedded notebooks,
replacing with suitable link material.

See the example [Quarto](https://quarto.org) book project in
`noteout/tests/qbook` for a quickstart.

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

Use with something like the following in your `_quarto.yml` file:

```yaml
filters:
  - quarto
  - noteout-write-notebooks

noteout:
  nb-format: Rmd
```

By default, Noteout writes your notebooks to your Quarto `output-dir`. In the example above, Noteout would write `a_notebook.Rmd` and `b_notebook.Rmd` to your `output-dir` directory.

See the [Resampling book](https://resampling-stats.github.io/resampling-with)
for a fully worked example, with extra configuration, and the [Resampling-with
Github repository](https://github.com/resampling-stats/resampling-with) for
the configuration and text source files.
