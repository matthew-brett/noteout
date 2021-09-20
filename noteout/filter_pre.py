""" Panflute filter to drop divs, spans before rest of processing.
"""

from .filter_divspans import MetaFilter


class PreFilter(MetaFilter):

    metadata_field = 'noteout.pre-filter'


def main(doc=None):
    PreFilter.main(doc=doc)


if __name__ == "__main__":
    main()
