""" Test detection and writing of notebooks

Here we are doing the second step of three.

* Parse the start and end markers to find the notebooks, then write out the
  notebook files after suitable processing.
"""

from pathlib import Path

import noteout.export_notebooks as enb

from noteout.nutils import fmt2fmt, filter_doc

from .tutils import fmt2md, filter_doc_nometa
from . import test_mark_notebooks as tmnb


MARKED_HEADER_FMT = '''\
# {title}

Find this notebook on the web at @nte-{name}.

'''


def _with_nb(nb_text, link_text=tmnb.DEF_LINK_TEXT):
    return tmnb.OUT_RMD.format(link_text=link_text, nb_text=nb_text)


def test_basic(in_tmp_path):
    marked_rmd = _with_nb(tmnb.SIMPLE_NB)
    in_doc = fmt2fmt(marked_rmd, out_fmt='panflute')
    in_doc.metadata['noteout'] = {'nb-format': 'Rmd'}
    out_doc = filter_doc(in_doc, enb)
    # We don't modify the input document.
    assert fmt2md(out_doc) == fmt2md(in_doc)
    # We do write out a notebook.
    out_nb_path = Path('notebooks') / 'a_notebook.Rmd'
    assert out_nb_path.is_file()
    nb_back = fmt2md(out_nb_path.read_text())
    assert nb_back == fmt2md(
        MARKED_HEADER_FMT.format(name='a_notebook',
                                 title='This is a notebook')
        + tmnb.SIMPLE_NB)


def test_nb_outputs(in_tmp_path):
    metadata = {'noteout': {
        'nb-format': 'Rmd',
        'book-url-root': 'https://resampling-stats.github.io/latest-r',
        'interact-url': "/interact/lab/index.html?path="}}
    data_path = Path('data')
    data_path.mkdir()
    in_data = data_path / 'df.csv'
    in_data.write_text('a,b\n1,2\n3,4')
    nb_text = '''\
```{r}
df <- read.csv("data/df.csv")
```'''
    in_doc = fmt2fmt(_with_nb(nb_text), out_fmt='panflute')
    in_doc.metadata = metadata.copy()
    out_with_data = filter_doc_nometa(in_doc, enb)
    out_nb_path = Path('notebooks') / 'a_notebook.Rmd'
    assert (out_nb_path / 'data').is_dir()
    assert (out_nb_path / 'data' / 'df.csv').is_file()
    assert (out_nb_path / 'a_notebook.zip').is_file()
    # Two data files.
    in_data = data_path / 'df2.csv'
    in_data.write_text('a,b\n1,2\n3,4')
    (out_nb_path / 'a_notebook.Rmd').write_text(
        '''\
```{r}
df <- read.csv("data/df.csv")
df2 <- read.csv("data/df2.csv")
```''')
    out_with_data2 = filter_doc_nometa(in_doc, anbL)
    assert (out_nb_path / 'data' / 'df2.csv').is_file()
    data_rmd = data_rmd.replace('+ data file', '+ data files')
    assert fmt2md(out_with_data2) == fmt2md(data_rmd)
