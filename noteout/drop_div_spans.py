""" Panflute filter to drop divs and spans
"""

import panflute as pf


def prepare(doc):
    dds = doc.get_metadata('drop_div_spans')
    if dds is None:
        dds = []
        edition = doc.get_metadata('rsbook_edition')
        if edition is not None:
            edition = edition.lower()
            if edition == 'python':
                dds = ['R']
            elif edition == 'r':
                dds = ['Python']
    doc.bad_names = {dds} if isinstance(dds, str) else set(dds)


def action(elem, doc):
    bad_names = doc.bad_names
    if isinstance(elem, (pf.Div, pf.Span)) and (
        elem.identifier in bad_names or
        bad_names.intersection(elem.classes)):
        return []


def finalize(doc):
    del doc.bad_names


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)


if __name__ == "__main__":
    main()
