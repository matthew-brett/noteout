""" Filter to write JSON for input document

Useful for debugging Quarto's intermediate files.
"""
import json
from io import StringIO

import panflute as pf


from .write_meta import new_fobj


def dump_doc(doc):
    with new_fobj('doc_{:03d}.json') as fobj:
        out = StringIO()
        pf.dump(doc, out)
        out_dict = json.loads(out.getvalue())
        json.dump(out_dict, fobj, indent=2)


def action(elem, doc):
    pass


def main(doc=None):
    return pf.run_filter(action,
                         prepare=dump_doc,
                         doc=doc)


if __name__ == "__main__":
    main()
