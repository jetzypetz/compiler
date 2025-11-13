#! /usr/bin/env python3

# --------------------------------------------------------------------
# Requires Python3 >= 3.10

# --------------------------------------------------------------------
import argparse
import json
import os
import subprocess as sp
import sys

from bxlib.bxast        import *
from bxlib.bxerrors     import DefaultReporter
from bxlib.bxparser     import Parser
from bxlib.bxmm         import MM
from bxlib.bxsynchecker import check as syncheck

# ====================================================================
# Parse command line arguments

def parse_args():
    parser = argparse.ArgumentParser(prog = os.path.basename(sys.argv[0]))

    parser.add_argument('input', help = 'input file (.bx)')

    aout = parser.parse_args()

    if os.path.splitext(aout.input)[1].lower() != '.bx':
        parser.error('input filename must end with the .bx extension')

    return aout

# ====================================================================
# Main entry point

def _main():
    args = parse_args()

    try:
        with open(args.input, 'r') as stream:
            prgm = stream.read()

    except IOError as e:
        print(f'cannot read input file {args.input}: {e}')
        exit(1)

    reporter = DefaultReporter(source = prgm)
    prgm = Parser(reporter = reporter).parse(prgm)
    basename = os.path.splitext(args.input)[0]

    if prgm is None:
        exit(1)

    if not syncheck(prgm, reporter):
        exit(1)

    tac = MM.mm(prgm)

    aout = [dict(
        proc = '@main',
        body = [x.tojson() for x in tac],
    )]

    try:
        with open(f'{basename}.tac.json', 'w') as stream:
            json.dump(aout, stream, indent = 2)

    except IOError as e:
        print(f'cannot write outpout file {args.output}: {e}')
        exit(1)

# --------------------------------------------------------------------
if __name__ == '__main__':
    _main()
