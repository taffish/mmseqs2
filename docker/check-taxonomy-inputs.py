#!/usr/bin/python3
"""Fail before implicit createtaxdb network access; do not alter scientific arguments."""
import os
from pathlib import Path
import sys

args = sys.argv[1:]
if not args or any(a in ('-h', '--help') for a in args):
    sys.exit(0)
permission = os.environ.get('TAFFISH_MMSEQS2_ALLOW_DOWNLOAD', '0')
if permission not in ('0', '1'):
    sys.exit('mmseqs: TAFFISH_MMSEQS2_ALLOW_DOWNLOAD must be 0 or 1')
if permission == '1':
    sys.exit(0)
def option(name):
    for i, value in enumerate(args):
        if value == name and i + 1 < len(args):
            return args[i + 1]
    return None
database = args[0]
tax = option('--ncbi-tax-dump')
mapping = option('--tax-mapping-file')
tax_ready = Path(database + '_taxonomy').is_file() or all(Path(database + '_' + n).is_file() for n in ('nodes.dmp', 'names.dmp', 'merged.dmp', 'delnodes.dmp'))
map_ready = Path(database + '_mapping').is_file()
if not tax_ready and not (tax and all((Path(tax) / n).is_file() for n in ('nodes.dmp', 'names.dmp', 'merged.dmp', 'delnodes.dmp'))):
    sys.exit('mmseqs: missing local taxonomy; provide --ncbi-tax-dump with nodes/names/merged/delnodes.dmp. Network requires explicit TAFFISH_MMSEQS2_ALLOW_DOWNLOAD=1.')
if not map_ready and not (mapping and Path(mapping).is_file()):
    sys.exit('mmseqs: missing local mapping; provide --tax-mapping-file. Network requires explicit TAFFISH_MMSEQS2_ALLOW_DOWNLOAD=1.')
