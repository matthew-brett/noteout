""" Pandoc / Quarto filters and scripts for embedded notebooks
"""

__version__ = '1.0.0a1'

# Patch Panflute for Quarto RawBlocks:
# https://github.com/sergiocorreia/panflute/pull/251

import panflute as _pf

_pf.elements.RAW_FORMATS.add('latex-merge')
