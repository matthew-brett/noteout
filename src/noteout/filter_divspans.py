#!/usr/bin/env python3
""" Panflute filter to drop divs and spans
"""

from noteout.nutils import Filter


class DivSpanFilter(Filter):

    metadata_field = 'noteout.filter-divspans'

    @classmethod
    def get_bad_names(cls, doc):
        dds = doc.get_metadata(cls.metadata_field)
        if dds is not None:
            return {dds} if isinstance(dds, str) else set(dds)
        return set()


def main(doc=None):
    DivSpanFilter.main(doc=doc)


if __name__ == "__main__":
    main()
