""" Test detection and writing of notebooks

Here we are doing the second pass of the two-pass method.

* Parse the start and end markers to find the notebooks, then write out the
  notebook files after suitable processing.
* If there are data files read in the notebook, also:
    * Copy data files to notebook output directory.
    * Make a zip file for notebook with read data files.
"""

from pathlib import Path
import shutil
from zipfile import ZipFile

import noteout.export_notebooks as enb

from noteout.nutils import filter_doc

from .tutils import q2md, q2doc, fmt2md, filter_doc_nometa
from . import test_mark_notebooks as tmnb


MARKED_HEADER_FMT = '''\
# {title}

Find this notebook on the web at @nte-{name}.

'''


def _with_nb(nb_text, link_text=tmnb.DEF_LINK_TEXT):
    return tmnb.OUT_RMD.format(link_text=link_text, nb_text=nb_text)


def test_basic(in_tmp_path):
    marked_rmd = _with_nb(tmnb.SIMPLE_NB)
    in_doc = q2doc(marked_rmd)
    in_doc.metadata['noteout'] = {'nb-format': 'Rmd'}
    out_doc = filter_doc(in_doc, enb)
    # We don't modify the input document.
    assert fmt2md(out_doc) == fmt2md(in_doc)
    # We do write out a notebook.
    out_nb_path = Path('notebooks') / 'a_notebook.Rmd'
    assert out_nb_path.is_file()
    nb_back = q2md(out_nb_path.read_text())
    assert nb_back == q2md(
        MARKED_HEADER_FMT.format(name='a_notebook',
                                 title='This is a notebook')
        + tmnb.SIMPLE_NB)


def test_nb_outputs(in_tmp_path):
    metadata = {'noteout': {'nb-format': 'Rmd'}}
    data_path = Path('data')
    data_path.mkdir()
    in_data = data_path / 'df.csv'
    in_data.write_text('a,b\n1,2\n3,4')
    in_doc = q2doc(_with_nb(tmnb.DATA_NB))
    in_doc.metadata = metadata.copy()
    filter_doc_nometa(in_doc, enb)
    nb_dir = Path('notebooks')
    out_nb_path = nb_dir / 'a_notebook.Rmd'
    assert out_nb_path.is_file()
    nb_data_dir = nb_dir / 'data'
    assert (nb_data_dir / 'df.csv').is_file()
    out_zip_path = out_nb_path.with_suffix('.zip')
    with ZipFile(out_zip_path, 'r') as zf:
        assert zf.namelist() == ['a_notebook.Rmd', 'data/df.csv']
    # Two data files.
    shutil.rmtree(nb_dir)
    in_data = data_path / 'df2.csv'
    in_data.write_text('a,b\n1,2\n3,4')
    datas_in_doc = q2doc(_with_nb(tmnb.DATAS_NB))
    datas_in_doc.metadata = metadata.copy()
    filter_doc_nometa(datas_in_doc, enb)
    assert (nb_dir / 'a_notebook.Rmd').is_file()
    assert (nb_dir / 'a_notebook.zip').is_file()
    assert (nb_data_dir / 'df.csv').is_file()
    assert (nb_data_dir / 'df2.csv').is_file()


def test_no_output(in_tmp_path):
    # By default, we output the notebooks.
    in_doc = q2doc(_with_nb(tmnb.SIMPLE_NB))
    nb_dir = Path('notebooks')
    filter_doc(in_doc, enb)
    out_nb_path = nb_dir / 'a_notebook.ipynb'
    assert out_nb_path.is_file()
    shutil.rmtree(nb_dir)
    # If we specify the output format, by default, this has no effect.
    # (We still output the notebook).
    in_doc.metadata['quarto-doc-params'] = {'out_format': 'latex'}
    filter_doc(in_doc, enb)
    assert out_nb_path.is_file()
    shutil.rmtree(nb_dir)
    # But if we set nb-build-formats, this restricts the build to those
    # formats.
    in_doc.metadata['noteout'] = {'nb-build-formats': ['html']}
    filter_doc(in_doc, enb)
    assert not nb_dir.is_dir()
    # Unless there's a '*' in the build formats.
    in_doc.metadata['noteout'] = {'nb-build-formats': ['html', '*']}
    filter_doc(in_doc, enb)
    assert out_nb_path.is_file()
    shutil.rmtree(nb_dir)
    # Or the build format matches nb-build-formats.
    in_doc.metadata['noteout'] = {'nb-build-formats': ['html']}
    in_doc.metadata['quarto-doc-params'] = {'out_format': 'html'}
    filter_doc(in_doc, enb)
    assert out_nb_path.is_file()
    shutil.rmtree(nb_dir)
