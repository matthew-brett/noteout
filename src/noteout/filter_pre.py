#!/usr/bin/env python3
""" Panflute filter to drop divs, spans before rest of processing.
"""

from noteout.filter_divspans import DivSpanFilter


class PreFilter(DivSpanFilter):

    metadata_field = 'noteout.pre-filter'


def main(doc=None):
    PreFilter.main(doc=doc)


if __name__ == "__main__":
    main()
