# When can you "reduce" outlines consisting of multiple non-overlapping strokes
# in strict steno order into one stroke?
#
# - you can reduce TPAEUPL/-S "famous" into TPAEUPLS
# - you can reduce RAB/-T "rabbit" into RABT (but RABTS doesn't work)
# - you cannot reduce HRET/-S "lettuce" into HRETS, because that's "lets"
# - you cannot reduce RUB/-GS "rubbish" into RUBGS, even though that's undefined
#
# This script does not detect reducible outlines that are not explicitly defined
# in the dictionary, like TPEUPB/-GS "finish". (Phoenix only separately defines
# TPEUPB "fin" and -GS "-ish".)

import argparse
import csv
import functools
import itertools
import json
import operator
import pathlib

from plover_stroke import BaseStroke

parser = argparse.ArgumentParser()
parser.add_argument('dictionary_file', type=pathlib.Path)
parser.add_argument('output_file',     type=pathlib.Path)
args = parser.parse_args()

class Stroke(BaseStroke):
    pass

Stroke.setup(
    '# S- T- K- P- W- H- R- A- O- * -E -U -F -R -P -B -L -G -T -S -D -Z'.split(),
    'A- O- * -E -U'.split(),
    '#',
    {
        'S-': '1-',
        'T-': '2-',
        'P-': '3-',
        'H-': '4-',
        'A-': '5-',
        'O-': '0-',
        '-F': '-6',
        '-P': '-7',
        '-L': '-8',
        '-T': '-9',
    }
)

INFLECTED_ENDINGS = set(map(Stroke, [
    '-G',
    '-D',
    '-Z',
    '-GZ',
    '-RG',
    '-RD',
    '-RZ',
    '-PBG',
    '-PBD',
    '-PBZ',
    '-LG',
    '-LD',
    '-LZ',
]))

def highest_bit(n):
    return 2 ** (n.bit_length() - 1)

def lowest_bit(n):
    return n & -n

def do_not_overlap(strokes):
    return all(highest_bit(int(stroke1)) < lowest_bit(int(stroke2))
               for stroke1, stroke2 in itertools.pairwise(strokes))

def reduce(strokes):
    return functools.reduce(operator.or_, strokes)

with args.dictionary_file.open() as f:
    dictionary = json.load(f)

with args.output_file.open('w') as f:
    writer = csv.writer(f)
    for outline, translation in dictionary.items():
        strokes = list(map(Stroke, outline.split('/')))
        if len(strokes) > 1 and strokes[-1] not in INFLECTED_ENDINGS and do_not_overlap(strokes):
            overlapped = str(reduce(strokes))
            writer.writerow((outline, translation, overlapped, dictionary.get(overlapped)))
