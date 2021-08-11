import os
import os.path as op
import json

import panflute as pf


def dump_meta(doc):
    d = doc.get_metadata()
    d['env'] = dict(os.environ)
    for i in range(1000):
        fname = f'meta_{i:03d}.json'
        if not op.exists(fname):
            break
    else:
        raise RuntimeError('Ran out of files')
    with open(fname, 'wt') as fobj:
        json.dump(d, fobj, indent=2)


def action(elem, doc):
    pass


def main(doc=None):
    return pf.run_filter(action,
                         prepare=dump_meta,
                         doc=doc)


if __name__ == "__main__":
    main()
