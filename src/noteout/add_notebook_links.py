#!/usr/bin/env python3
""" Panflute filter to write notebook downloads and associated links

See ``mark_notebooks.py`` for the overall structure of processing.

This is the last of the three processing steps for notebooks.

In this step, work out which notebooks have data files associated, write out
zips for download of notebooks with data files, and drop interact and download
links into the originating document.   (We have to do this last step separately
because we don't know what the download links should link to until we know
whether the notebooks have data files, and should therefore be ``.zip``
download links instead of notebook download links).

* The notes should suitably create Interact and Download buttons or the LaTeX
  URL equivalents, depending on output format.
* For the LaTeX / PDF output, the links should be absolute web links.  For
  HTML, the links should be relative to the output page.
"""
