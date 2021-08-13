""" Panflute filter to drop divs and spans
"""

import panflute as pf


def get_bad_names(doc):
    dds = doc.get_metadata('noteout.filter-divspans')
    if dds is not None:
        return {dds} if isinstance(dds, str) else set(dds)
    return set()


def prepare(doc):
    doc.bad_names = get_bad_names(doc)


def action(elem, doc):
    bad_names = doc.bad_names
    if (isinstance(elem, (pf.Div, pf.Span)) and
        bad_names.intersection(elem.classes)):
        return []


def finalize(doc):
    return
    del doc.bad_names


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
