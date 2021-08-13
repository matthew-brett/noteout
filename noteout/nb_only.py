""" Panflute filter to drop divs and spans for nb-only class.
"""

import panflute as pf


def action(elem, doc):
    if (isinstance(elem, (pf.Div, pf.Span)) and 'nb-only' in elem.classes):
        return []


def main(doc=None):
    return pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
