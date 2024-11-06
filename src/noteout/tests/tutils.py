""" Test utilities
"""

from copy import deepcopy
import json

from noteout.nutils import fmt2fmt


def dump_json(d, fname):
    """ Function for interactive debugging
    """
    if hasattr(d, 'to_json'):
        d = d.to_json()
    with open(fname, 'wt') as fobj:
        json.dump(d, fobj, indent=2)


def check_contains(doc, checkfunc):
    doc = deepcopy(doc)
    doc.metadata['contains'] = False

    def find(elem, doc):
        if checkfunc(elem, doc):
            doc.metadata['contains'] = True

    doc.walk(find)

    return doc.get_metadata('contains')


def get_contents(file_like):
    """ Read contents of file-like

    Parameters
    ----------
    file_like : object
        Object with `open` method, or `read` method.

    Returns
    -------
    contents : str
        Contents of `file_like`.
    """
    if hasattr(file_like, 'open'):
        with file_like.open(encoding='utf-8') as fobj:
            return fobj.read()
    return file_like.read()


def md2fmt(txt, out_fmt):
    return fmt2fmt(txt, in_fmt='markdown', out_fmt=out_fmt)


def read_md(file_like, output_format='panflute'):
    return md2fmt(get_contents(file_like), output_format)


def assert_json_equal(doc1, doc2):
    assert doc1.to_json() == doc2.to_json()


def filter_doc(doc, filt_mod):
    copied = deepcopy(doc)
    pf.run_filter(filt_mod.action,
                  prepare=getattr(filt_mod, 'prepare', None),
                  finalize=getattr(filt_mod, 'finalize', None),
                  doc=copied)
    copied.metadata = {}
    return copied
