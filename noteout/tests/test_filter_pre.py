""" Test nb-only filter
"""

from io import StringIO

from noteout.filter_pre import PreFilter as nopf

from .tutils import (read_md, assert_json_equal, filter_doc)


def test_filter_pre():
    content = """/
Some text [do this]{.todo}more text.

::: todo
A todo item
:::

More text.

::: comment
A comment
:::

Afterword.
"""
    doc = read_md(StringIO(content))
    filtered = filter_doc(doc, nopf)
    assert_json_equal(filtered, doc)
    doc.metadata['noteout'] = {"pre-filter": ['todo', 'comment']}
    exp_content = """/
Some text more text.

More text.

Afterword.
"""
    exp_doc = read_md(StringIO(exp_content))
    filtered = filter_doc(doc, nopf)
    assert_json_equal(filtered, exp_doc)
    doc.metadata['noteout'] = {"pre-filter": ['todo']}
    exp_content = """/
Some text more text.

More text.

::: comment
A comment
:::

Afterword.
"""
    exp_doc = read_md(StringIO(exp_content))
    filtered = filter_doc(doc, nopf)
    assert_json_equal(filtered, exp_doc)
    doc.metadata['noteout'] = {"pre-filter": ['comment']}
    exp_content = """/
Some text [do this]{.todo}more text.

::: todo
A todo item
:::

More text.

Afterword.
"""
    exp_doc = read_md(StringIO(exp_content))
    filtered = filter_doc(doc, nopf)
    assert_json_equal(filtered, exp_doc)
