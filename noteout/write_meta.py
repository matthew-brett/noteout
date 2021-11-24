import os
import os.path as op
import json
from contextlib import contextmanager

import panflute as pf


@contextmanager
def new_fobj(template, max_n=1000):
    for i in range(max_n):
        fname = template.format(i)
        if not op.exists(fname):
            break
    else:
        raise RuntimeError(
            f'Ran out of files with max n {max_n} and template "{template}"')
    with open(fname, 'wt') as fobj:
        yield fobj


def dump_meta(doc):
    d = doc.get_metadata()
    d['env'] = dict(os.environ)
    with new_fobj('meta_{:03d}.json') as fobj:
        json.dump(d, fobj, indent=2)


def action(elem, doc):
    pass


def main(doc=None):
    return pf.run_filter(action,
                         prepare=dump_meta,
                         doc=doc)


if __name__ == "__main__":
    main()
