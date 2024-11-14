""" Utilities for filters and notebook processing
"""

from copy import deepcopy
from pathlib import Path
import re

import panflute as pf


class NO_DEFAULT:
    """ Indicates there should be no default value
    """


# Defaults for noteout and quarto-doc-params.
_META_DEFAULTS = {
    'noteout.book-url-root': NO_DEFAULT,
    'noteout.interact-url': NO_DEFAULT,
    'noteout.nb-dir': 'notebooks',
    'noteout.nb-format': 'ipynb',
    'quarto-doc-params.out_format': None,
    'quarto-doc-params.output_directory': '.',
    'noteout.nb-strip-header-nos': True,
    'noteout.nb-flatten-divspans': ['+'],
}

# Meaning of '+' in noteout.nb-flatten-divspans.
_FLATTEN_DS_PLUS = ('header-section-number', 'nb-only')

# Regular expression to detect ```{r} etc code blocks.
_BACKTICK_BLOCK_RE = re.compile(
    r'''^
    ^(?P<starti>\s*)```\s*
    \{(?P<lang>\w+)
    (?P<lparams>\s+.*?)?
    \}
    \s*$
    (?P<block>.*?)
    ^(?P<endi>\s*)```\s*$
    ''',
    re.VERBOSE | re.MULTILINE | re.DOTALL)

# Replacement pattern for ```{r} etc code blocks.
_BACKTICK_SUB_PAT = ('\n::: cell\n'
                     r'\g<starti>```{.\g<lang> .cell-code\g<lparams>}'
                     r'\g<block>\g<endi>```'
                     '\n\n:::\n')

# Regular expression to identify code reading data.
READ_RE = re.compile(
    r'''^\s*
    \w+\s*(=|<-)\s*
    (pd\.)*read[._]\w+\(
    ['"]
    (?P<fname>.*?)
    ['"]
    \)
    ''',
    flags=re.MULTILINE | re.VERBOSE)


class FilterError(ValueError):
    """ Exception for invalid values in filters
    """


class Filter:
    """ Class to contain standard functions for Panflute filter

    * ``action``
    * ``prepare``
    * ``finalize``

    as well as:

    * ``main`` with which to run the filter.

    It anticipates filtering ``div`` and ``span`` elements in the Panflute
    output, and implements a simple dropping of ``div``s or ``span``s with
    names specified somehow via the ``get_bad_names`` method.  Typically this
    will be via metadata in the document to be filtered.
    """

    @classmethod
    def get_bad_names(cls, doc):
        """ Get class names for divs and spans to filter
        """
        raise NotImplementedError

    @classmethod
    def prepare(cls, doc):
        doc.bad_names = cls.get_bad_names(doc)

    @classmethod
    def action(cls, elem, doc):
        """ Filter out divs and spans with given unwanted classes
        """
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


def quartoize(in_md):
    """ Parse Markdown to be compatible with Quarto filtering

    Quarto noteboks have executable code blocks of form::

        ```{r}
        a <- 1
        a
        ```

    Pandoc does not process these as code blocks, and Quarto does some
    preprocessing to allow Pandoc to work with these.  Specifically Quarto
    parsing ends up with the equivalent of this Markdown::

        ::: cell

        ```{.r .cell-code}
        a <- 1
        a
        ```

        :::

    This function does a version of preprocessing on Markdown text, so we can
    get closer to Quarto parsing in our tests.

    Parameters
    ----------
    in_md : str
        Text in Markdown format.

    Returns
    -------
    out_md : str
        Text in Markdown format with backtick code blocks in RMarkdown
        reprocessed to be standard blocks with lang as class, and wrapped in a
        cell div.

    Notes
    -----
    See `https://github.com/quarto-dev/quarto-cli/discussions/11393`_ for a
    discussion of Quarto vs Pandoc filtering.

    You won't want to use this workaround in production, but you may want to
    use it for tests.  For example, you can use it for simulating Quarto filter
    input.
    """
    return _BACKTICK_BLOCK_RE.sub(_BACKTICK_SUB_PAT, in_md)


def fmt2fmt(inp, in_fmt=None, out_fmt='gfm', standalone=True):
    """ Convert doc `inp` in one Pandoc / Panflute format to another

    Parameters
    ----------
    inp : :class:`pf.Element` or str
        Input document as str or Panflute Doc or Element.
    in_fmt : None or str, optional
        Input format.  If `inp` is a Panflute Doc or Element, default (selected
        by None) corresponds to a Panflute object (via JSON), otherwise default
        to `markdown`.
    in_fmt : str, optional
        Output format.
    standalone : {True, False}, optional
        Whether to generate standalone doc.

    Returns
    -------
    out : :class:`pf.Element` or str
        Output in Panflute or text format.
    """
    if in_fmt == 'quarto-like':
        inp = quartoize(inp)
        in_fmt = 'markdown'
    return pf.convert_text(
        inp,
        input_format=in_fmt if in_fmt else (
            'panflute' if hasattr(inp, 'to_json') else 'markdown'),
        output_format=out_fmt,
        standalone=standalone)


def filter_doc(doc, filt_container):
    """ Filter Panflute document `doc` with filter defined in `filt_container`

    Parameters
    ----------
    doc : :class:`pf.Element`
        Input document Panflute Doc or Element.
    filt_container : object
        Object with `action` attribute, and (optionally) `prepare` and / or
        `finalize` attribute.

    Returns
    -------
    out_doc : :class:`pf.Element`
        Document filtered as specified by `filt_container`.
    """
    copied = deepcopy(doc)
    pf.run_filter(filt_container.action,
                  prepare=getattr(filt_container, 'prepare', None),
                  finalize=getattr(filt_container, 'finalize', None),
                  doc=copied)
    return copied


def is_div_class(elem, class_names):
    """ True if `elem` is a div, and has classes in `class_names`
    """
    if isinstance(class_names, str):
        class_names = [class_names]
    if not isinstance(elem, pf.Div):
        return False
    return set(class_names).intersection(elem.classes)


def name2title(name):
    """ Give human-friendly title from notebook name

    `name` will generally be a valid variable name, containing only
    alphanumeric characters and underscores.
    """
    return name.replace('_', ' ').capitalize()


def find_data_files(nb):
    """ Detect data files read within notebook

    Parameters
    ----------
    nb : dict
        Parsed notebook in dictionary form.

    Returns
    -------
    out_files : list
        List of detected filenames.  These will be relative to the path assumed
        by the `nb`.
    """
    out_fnames = []
    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue
        for m in READ_RE.finditer(cell['source']):
            out_fnames.append(m.groups()[-1])
    return sorted(set(out_fnames))


def fill_params(meta, required_keys=(), key_defaults=_META_DEFAULTS):
    """ Return dictionary with useful default parameters from `meta`

    Parameters
    ----------
    meta : :class:`panflute.MetaMap
        Dictionary-like container for document metadata.
    required_keys : sequence, optional
        Key names from `key_defaults` that a) do not have defaults, and b) must
        be present.
    key_defaults : dict, optional
        key, value pairs give key name (can use dotted syntax) and default
        value, where :class:`NO_DEFAULT` means value of key is required, no
        default.

    Returns
    ------
    params : dict
        Dictionary with useful keys and values derived from metadata and
        defaults.
    """
    p = {}
    # Wrap metadata in doc in order to use get_metadata method.
    doc = pf.Doc(metadata=meta)
    mget = lambda k, d : doc.get_metadata(k, d)
    for key, default in key_defaults.items():
        v = mget(key, default)
        if v is NO_DEFAULT and key in required_keys:
            raise FilterError(f'{key} must be defined in metadata')
        p[key.split('.')[-1]] = v
    p['output_directory'] = Path(p['output_directory'])
    # Some calculated defaults.
    p['interact-nb-suffix'] = mget(
        'noteout.interact-nb-suffix', '.' + p['nb-format'])
    p['nb_out_path'] = p['output_directory'] / p['nb-dir']
    flat_ds = list(p['nb-flatten-divspans'])
    if '+' in flat_ds:
        flat_ds.remove('+')
        flat_ds += list(_FLATTEN_DS_PLUS)
    p['nb-flatten-divspans'] = set(flat_ds)
    return p
