""" Utilities for filters and notebook processing
"""

from copy import deepcopy
import json

import panflute as pf


class Filter:
    """ Class to contain standard functions for Panflute filter

    * ``action``
    * ``prepare``
    * ``finalize``

    as well as:

    * ``main`` with which to run the filter.

    It anticipates filtering ``div`` and ``span`` elements in the Panflute
    output, and implements 
    """

    @classmethod
    def get_bad_names(cls, doc):
        """ Get class names for divs and spans to filter
        """
        raise NotImplementedError

    @classmethod
    def prepare(cls, doc):
        doc.bad_names = cls.get_bad_names(doc)

    @classmethod
    def action(cls, elem, doc):
        """ Filter out divs and spans with given unwanted classes
        """
        bad_names = doc.bad_names
        if (isinstance(elem, (pf.Div, pf.Span)) and
            bad_names.intersection(elem.classes)):
            return []

    @classmethod
    def finalize(cls, doc):
        del doc.bad_names

    @classmethod
    def main(cls, doc=None):
        return pf.run_filter(cls.action,
                             prepare=cls.prepare,
                             finalize=cls.finalize,
                             doc=doc)


def fmt2fmt(inp, in_fmt=None, out_fmt='gfm'):
    """ Convert doc `inp` in one Pandoc / Panflute format to another

    Parameters
    ----------
    inp : :class:`pf.Element` or str
        Input document as str or Panflute Doc or Element.
    in_fmt : None or str, optional
        Input format.  If `inp` is a Panflute Doc or Element, default (selected
        by None) corresponds to a Panflute object (via JSON), otherwise default
        to `markdown`.
    in_fmt : str, optional
        Output format.

    Returns
    -------
    out : :class:`pf.Element` or str
        Output in Panflute or text format.
    """

    is_doc = hasattr(inp, 'to_json')
    return pf.convert_text(
        json.dumps(inp.to_json()) if is_doc else inp,
        input_format=in_fmt if in_fmt else (
            'json' if is_doc else 'markdown'),
        output_format=out_fmt,
        standalone=True)


def filter_doc(doc, filt_container):
    """ Filter Panflute document `doc` with filter defined in `filt_container`

    Parameters
    ----------
    doc : :class:`pf.Element`
        Input document Panflute Doc or Element.
    filt_container : object
        Object with `action` attribute, and (optionally) `prepare` and / or
        `finalize` attribute.

    Returns
    -------
    out_doc : :class:`pf.Element`
        Document filtered as specified by `filt_container`.
    """
    copied = deepcopy(doc)
    pf.run_filter(filt_container.action,
                  prepare=getattr(filt_container, 'prepare', None),
                  finalize=getattr(filt_container, 'finalize', None),
                  doc=copied)
    return copied
