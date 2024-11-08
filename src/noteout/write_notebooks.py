#!/usr/bin/env python3
""" Placeholder for earlier filter

Please instead use the three-pass method, described in ``mark_notebooks.py``,
by running the ``mark_notebooks.py`` filter before running any Quarto
processing, and then running the ``export_notebooks.py`` and
``add_notebook_links.py`` filters.
"""

def main(doc=None):
    raise RuntimeError(
        'Please use 3-pass `mark_notebooks`, `export_notebooks`, '
        '`add_notebook_links` instead of `write_notebooks`.')


if __name__ == "__main__":
    main()
