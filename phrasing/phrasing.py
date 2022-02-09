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


stack = functools.partial(functools.reduce, operator.or_)
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


parent_dir = pathlib.Path(__file__).parent

with parent_dir.parent.joinpath('main.json').open() as f:
    main = json.load(f)

main_reversed = collections.defaultdict(list)
for stroke, translation in main.items():
    main_reversed[translation].append(stroke)


#             I     am 'm was    \       \           \
#                                |       |           |
#          /  you   \            |       | have 've  |
# "people" |  we    | are 're    |       |           |
#          \  they  /            | were  /           | had
#                                |                   |
#          /  he    \            |       \           |
# "person" |  she   | is 's was  |       | has       |
#          \  it    /            /       /           /


# "be"

patterns = []

i = {"KWR": "I"}

people = {
    "U":   "you",
    "W":   "we",
    "THE": "they",
}

person = {
    "H":  "he",
    "SH": "she",
    "T":  "it", # or thing
}

everyone = i | people | person

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
    (i,        am,   maybe_the),
    (people,   are,  maybe_the),
    (person,   is_,  maybe_the),
    (everyone, were, maybe_the),
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
    (i | people, have, maybe_been, maybe_the),
    (person,     has,  maybe_been), # -TZ requires Philly shift, and -BTZ is impossible
    (everyone,   had,  maybe_been), # -TD feels weird, and -BTD violates inversion rule
])


# "I'*" special case

i_special = {"AOEU": "I"}

i_special_contractions = {
    "-PL": "^'m",
    "-F":  "^'ve",
    "-FB": "^'ve been",
}

patterns.append((i_special, i_special_contractions, maybe_the))


dictionary = {}

for pattern in patterns:
    for combination in itertools.product(*(p.items() for p in pattern)):
        strokes, phrase = zip(*combination)
        stroke = str(stack(map(Stroke, strokes)))
        translation = join(phrase)
        assert stroke not in dictionary, (
            f'Trying to define {stroke} as "{translation}" '
            f'but that\'s already defined as "{dictionary[stroke]}"'
        )
        dictionary[stroke] = translation

remappings = {
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

remappings_reversed = {
    translation: stroke
    for stroke, translation in remappings.items()
}

dictionary |= remappings
dictionary['WUZ/WUZ'] = '{#}' # to ensure trailing comma after each real entry

wrote = False

with parent_dir.joinpath('report.txt').open('w') as f:
    for translation, strokes in main_reversed.items():
        remappings = {}
        for stroke in strokes:
            if stroke in dictionary and dictionary[stroke] != translation:
                remappings[stroke] = dictionary[stroke]
        if remappings:
            if wrote:
                f.write('\n')
            suffix = '' if translation not in remappings_reversed else f' -> {remappings_reversed[translation]}'
            f.write(f'{translation}{suffix}\n')
            wrote = True
            for stroke in strokes:
                suffix = '' if stroke not in remappings else f' -> {remappings[stroke]}'
                f.write(f'  {stroke}{suffix}\n')

with parent_dir.joinpath('phrasing.json').open('w') as f:
    json.dump(dictionary, f, indent=4)
