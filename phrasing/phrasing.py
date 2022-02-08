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


i = {"KWR": "I"}

i_am = {
    "KWR-PL": "I am",
    "AOEUPL": "I'm", # special case to avoid *
    "KWR-FS": "I was",
}

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

pronoun = i | people | person

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

patterns = [
    (i_am,          maybe_the),
    (people,  are,  maybe_the),
    (person,  is_,  maybe_the),
    (pronoun, were, maybe_the),
]


dictionary = {}

for pattern in patterns:
    for combination in itertools.product(*(p.items() for p in pattern)):
        strokes, phrase = zip(*combination)
        stroke = str(stack(map(Stroke, strokes)))
        translation = join(phrase)
        assert stroke not in dictionary
        dictionary[stroke] = translation

remappings = {
    "TEPL": "item",
    "WR": "where",
    "WR-T": "where the",
    "WRU": "where you",
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
