""" Test detection and writing of notebooks

Here we are doing the second step of three.

* Parse the start and end markers to find the notebooks, then write out the
  notebook files after suitable processing.
"""

from pathlib import Path

import noteout.export_notebooks as enb

from noteout.nutils import fmt2fmt, filter_doc

from .tutils import fmt2md
from .test_mark_notebooks import LATEX_RMD as MARKED_RMD


def test_basic(in_tmp_path):
    in_doc = fmt2fmt(MARKED_RMD, out_fmt='panflute')
    in_doc.metadata['noteout'] = {'nb-format': 'Rmd'}
    out_doc = filter_doc(in_doc, enb)
    # We don't modify the input document.
    assert fmt2md(out_doc) == fmt2md(in_doc)
    # We do write out a notebook.
    out_nb_path = Path('notebooks') / 'a_notebook.Rmd'
    assert out_nb_path.is_file()
    nb_back = fmt2md(out_nb_path.read_text())
    assert nb_back == fmt2md('''\
# This is a notebook

Find this notebook on the web at @nte-a_notebook.

Here, again, is a paragraph.

```{r}
a <- 10
```

More text.''')
