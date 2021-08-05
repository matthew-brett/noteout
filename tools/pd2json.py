#!/usr/bin/env python
""" Dump file to prettified Pandoc JSON
"""

import json
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import panflute as pt


def parse_fname(fname):
    with open(fname, 'rt') as fobj:
        contents = fobj.read()
    return pt.convert_text(contents, output_format='json')


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('fname',
                        help='Filename to encode to JSON')
    parser.add_argument('--indent', default=2,
                        help='Indentation level (int)')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    out_str = parse_fname(args.fname)
    out_json = json.loads(out_str)
    out_fname = Path(args.fname).with_suffix('.json')
    with open(out_fname, 'wt') as fobj:
        json.dump(out_json, fobj, indent=args.indent)


if __name__ == '__main__':
    main()
