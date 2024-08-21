""" Notebook parsing filters for Pandoc
"""

__version__ = '0.0.3a7'

# Patch Panflute for Quarto RawBlocks:
# https://github.com/sergiocorreia/panflute/pull/251

import panflute as _pf

_pf.elements.RAW_BLOCKS.add('latex-merge')
