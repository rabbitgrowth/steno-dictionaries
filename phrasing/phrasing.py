import collections
import functools
import itertools
import json
import operator
import pathlib

from plover_stroke import BaseStroke


class Stroke(BaseStroke):
    pass

Stroke.setup(
    '# S- T- K- P- W- H- R- A- O- * -E -U -F -R -P -B -L -G -T -S -D -Z'.split(),
    'A- O- * -E -U'.split(),
)


def stack(strokes):
    return functools.reduce(operator.add, strokes)

# sum() doesn't work as expected:
# >>> stack((Stroke('THA'), Stroke('AEU')))
#     THAEU
# >>> sum(Stroke('THA'), Stroke('AEU'))
#     THAEU
# >>> sum((Stroke('THA'), Stroke('AEU'))) # 0 + ...
#     6724
# >>> Stroke(sum((Stroke('THA'), Stroke('AEU'))))
#     THOEU

def join(chunks):
    return ' '.join(filter(None, chunks)).replace(' ^', '')


# I     am 'm was    \       \           \
#                    |       |           |
# you   \            |       | have 've  |
# we    | are 're    |       |           |
# they  /            | were  /           | had
#                    |                   |
# he    \            |       \           |
# she   | is 's was  |       | has       |
# it    /            /       /           /

patterns = []

# "be"

i = {"KWR": "I"}

plural_pronoun_left = {
    "U":   "you",
    "W":   "we",
    "THE": "they",
}

singular_pronoun_left = {
    "H":  "he",
    "SH": "she",
    "T":  "it", # or thing
}

pronoun_left = i | plural_pronoun_left | singular_pronoun_left

am = {
    "-PL": "am",
    "*PL": "^'m",
    "-FS": "was",
}

are = {
    "-R": "are",
    "*R": "^'re",
}

is_ = {
    "-S":  "is",
    "*S":  "^'s",
    "-FS": "was",
}

were = {"-RP": "were"} # used with all pronouns in the subjunctive

maybe_the = {
    "":   "",
    "-T": "the",
}

patterns.extend([
    (i,                     am,   maybe_the),
    (plural_pronoun_left,   are,  maybe_the),
    (singular_pronoun_left, is_,  maybe_the),
    (pronoun_left,          were, maybe_the),
])

# "have"

have = {
    "-F": "have",
    "*F": "^'ve",
}

has = {"-Z": "has"}
had = {"-D": "had"} # used with all pronouns

maybe_been = {
    "":   "",
    "-B": "been",
}

patterns.extend([
    (i | plural_pronoun_left, have, maybe_been, maybe_the),
    (singular_pronoun_left,   has,  maybe_been), # -TZ requires Philly shift, and -BTZ is impossible
    (pronoun_left,            had,  maybe_been), # -TD feels weird, and -BTD violates inversion rule
])

# Modal verbs

modal_verb_right = {
    "-BG":  "can",
    "-BGD": "could",
    "-RB":  "shall",
    "-RBD": "should",
    "-L":   "will",
    "-LD":  "would",
    "*L":   "^'ll",
    "*D":   "^'d", # could be short for "had" too, so use *D instead of *LD
}

patterns.append((pronoun_left, modal_verb_right))


phrasing = {}

def update(dictionary, stroke, translation):
    rtfcre = str(stroke)
    assert rtfcre not in dictionary, (
        f'Trying to define {rtfcre} as "{translation}" '
        f'but that\'s already defined as "{dictionary[rtfcre]}"'
    )
    dictionary[rtfcre] = translation

for pattern in patterns:
    for combination in itertools.product(*(p.items() for p in pattern)):
        strokes, phrase = zip(*combination)
        stroke = stack(map(Stroke, strokes))
        translation = join(phrase)
        update(phrasing, stroke, translation)

        # "I'*" special case
        if Stroke('KWR*') in stroke and translation.startswith("I'"):
            stroke = stroke - Stroke('KWR*') + Stroke('AOEU')
            update(phrasing, stroke, translation)


remaps = {
    "EUD":    "idea",
    "EULD":   "ideal",
    "HREULD": "ideally",
    "*EUD":   "id", # as in psychoanalysis

    "TEPL": "item",

    "TH-FT": "theft", # E got stolen? or associate with TKPW-PB "gun"

    "WR":   "where",
    "WR-T": "where the",
    "WRU":  "where you",
}

remaps_reversed = {
    translation: rtfcre
    for rtfcre, translation in remaps.items()
}

for rtfcre, translation in remaps.items():
    stroke = Stroke(rtfcre)
    update(phrasing, stroke, translation)


# Add dummy entry to ensure trailing comma after each real entry
phrasing['WUZ/WUZ'] = '{#}'


parent_dir = pathlib.Path(__file__).parent

with parent_dir.parent.joinpath('main.json').open() as f:
    main = json.load(f)

main_reversed = collections.defaultdict(list)
for rtfcre, translation in main.items():
    main_reversed[translation].append(rtfcre)


wrote = False

with parent_dir.joinpath('report.txt').open('w') as f:
    for translation, rtfcres in main_reversed.items():
        remaps = {}
        for rtfcre in rtfcres:
            if rtfcre in phrasing and phrasing[rtfcre] != translation:
                remaps[rtfcre] = phrasing[rtfcre]
        if remaps:
            if wrote:
                f.write('\n')
            suffix = '' if translation not in remaps_reversed else f' -> {remaps_reversed[translation]}'
            f.write(f'{translation}{suffix}\n')
            wrote = True
            for rtfcre in rtfcres:
                suffix = '' if rtfcre not in remaps else f' -> {remaps[rtfcre]}'
                f.write(f'  {rtfcre}{suffix}\n')

with parent_dir.joinpath('phrasing.json').open('w') as f:
    json.dump(phrasing, f, indent=4)
