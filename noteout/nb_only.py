""" Panflute filter to drop divs and spans for nb-only class.
"""

import panflute as pf


class Filter:

    @classmethod
    def get_bad_names(cls, doc):
        raise NotImplementedError

    @classmethod
    def prepare(cls, doc):
        doc.bad_names = cls.get_bad_names(doc)

    @classmethod
    def action(cls, elem, doc):
        bad_names = doc.bad_names
        if (isinstance(elem, (pf.Div, pf.Span)) and
            bad_names.intersection(elem.classes)):
            return []

    @classmethod
    def finalize(cls, doc):
        del doc.bad_names

    @classmethod
    def main(cls, doc=None):
        return pf.run_filter(cls.action,
                             prepare=cls.prepare,
                             finalize=cls.finalize,
                             doc=doc)


class NbonlyFilter(Filter):

    bad_names = {'nb-only'}

    @classmethod
    def get_bad_names(cls, doc):
        return cls.bad_names


def main(doc=None):
    NbonlyFilter.main(doc=doc)


if __name__ == "__main__":
    main()
