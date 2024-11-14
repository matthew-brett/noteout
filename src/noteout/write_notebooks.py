#!/usr/bin/env python3
""" Placeholder for earlier filter

Please instead use the two-pass method, described in ``mark_notebooks.py``,
by running the ``mark_notebooks.py`` filter before running any Quarto
processing, and then, after Quarto filters, running the ``export_notebooks.py``
filter.
"""

def main(doc=None):
    raise RuntimeError(
        'Please use 2-pass `mark_notebooks` and `export_notebooks` '
        'method instead of `write_notebooks`.')


if __name__ == "__main__":
    main()
