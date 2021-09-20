""" Test nb-only filter
"""

from io import StringIO

from noteout.nb_only import NbonlyFilter as nnbo

from .tutils import (read_md, assert_json_equal, filter_doc)


def test_nb_only():
    content = """/
Some text [notebook only]{.nb-only}more text.

::: nb-only
Only in notebook.
:::

More text.
"""
    doc = read_md(StringIO(content))
    filtered = filter_doc(doc, nnbo)
    exp_content = """/
Some text more text.

More text.
"""
    exp_doc = read_md(StringIO(exp_content))
    assert_json_equal(filtered, exp_doc)
