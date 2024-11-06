#!/usr/bin/env python3
""" Panflute filter to drop divs and spans for nb-only class.
"""

from noteout.nutils import Filter


class NbonlyFilter(Filter):

    bad_names = {'nb-only'}

    @classmethod
    def get_bad_names(cls, doc):
        return cls.bad_names


def main(doc=None):
    NbonlyFilter.main(doc=doc)


if __name__ == "__main__":
    main()
