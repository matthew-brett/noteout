import json

import panflute as pf


def dump_meta(doc):
    with open('meta.json', 'wt') as fobj:
        json.dump(doc.get_metadata(), fobj, indent=2)


def action(elem, doc):
    pass


def main(doc=None):
    return pf.run_filter(action,
                         prepare=dump_meta,
                         doc=doc)


if __name__ == "__main__":
    main()
