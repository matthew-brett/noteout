""" Panflute filter to drop divs and spans
"""

import panflute as pf


def get_bad_names(doc):
    dds = doc.get_metadata('drop_div_spans')
    if dds is not None:
        return {dds} if isinstance(dds, str) else set(dds)
    edition = doc.get_metadata('_quarto-vars.edition')
    if edition is None:
        return set()
    edition = edition.lower()
    if edition == 'python':
        return {'R'}
    elif edition == 'r':
        return {'Python'}
    return set()


def prepare(doc):
    doc.bad_names = get_bad_names(doc)


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
