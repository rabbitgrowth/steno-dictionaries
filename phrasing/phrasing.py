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

def maybe(component):
    return {"": "", **component}


patterns = []

# "be"

i    = {"KWR": "I"}
you  = {"U":   "you"}
he   = {"H":   "he"}
she  = {"SH":  "she"}
it   = {"T":   "it"}
we   = {"W":   "we"}
they = {"THE": "they"}
this = {"TH":  "this"}
that = {"THA": "that"}

plural_pronoun   = you | we | they
singular_pronoun = he | she | it | this | that
pronoun          = i | plural_pronoun | singular_pronoun

is_  = {"-S":  "is",  "*S":  "^'s"}
am   = {"-PL": "am",  "*PL": "^'m"}
are  = {"-R":  "are", "*R":  "^'re"}
was  = {"-FS": "was"}
were = {"-RP": "were"}
the  = {"-T":  "the"}

patterns.extend([
    (i,                am  | was, maybe(the)),
    (plural_pronoun,   are,       maybe(the)),
    (singular_pronoun, is_ | was, maybe(the)),
    (pronoun,          were,      maybe(the)),
])

# "have"

have = {"-F": "have", "*F": "^'ve"}
has  = {"-Z": "has"} # is    -> ^'s
had  = {"-D": "had"} # would -> ^'d
been = {"-B": "been"}

patterns.extend([
    (i | plural_pronoun, have, maybe(been), maybe(the)),
    (singular_pronoun,   has,  maybe(been)), # -TZ requires Philly shift, and -BTZ is impossible
    (pronoun,            had,  maybe(been)), # -TD feels weird, and -BTD violates inversion rule
])

# wh-words

wh_word = {
    "KPH": "which",
    "WHO": "who",
    "WHA": "what",
    "WH":  "when",
    "WHR": "where",
    "KWH": "why",
}

patterns.extend([
    (wh_word, is_ | are | was | were, maybe(the)), # exclude "am" and keep WHOPL as "whom"
    (wh_word, have,      maybe(been), maybe(the)),
    (wh_word, has | had, maybe(been)),
])

# Verbs

negative = {
    "O":  "don't",
    "EU": "didn't",
    "A":  "can't",
    "U":  "couldn't",
}

extra_nt = {"-PBT": ""}

verb = {
    "-BL":  "believe",
    "-FL":  "feel",
    "-FD":  "find",
    "-GT":  "get",
    "-FPL": "like", # borrowed from Stanley Sakai
    "-RPL": "remember",
    "-PBG": "think",
    "-PT":  "want",
}

verb_past_tense = {
    "-FLT": "felt",
    "-BS":  "said",
}

patterns.extend([
    (i, negative, extra_nt | verb),
    (pronoun | wh_word, verb | verb_past_tense),
])

# Modal verbs

medial_pronoun = {
    "EU": "I",
    "E":  "he",
    "U":  "you",
}

modal_verb = {
    "-BG":  "can",
    "-BGD": "could",
    "-RB":  "shall",
    "-RBD": "should",
    "-L":   "will",
    "-LD":  "would",
    "*L":   "^'ll",
    "*D":   "^'d", # could be short for "had" too, so use *D instead of *LD
}

patterns.extend([
    (pronoun | wh_word, modal_verb),
    (that | wh_word, medial_pronoun, modal_verb | verb),
])


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

        # Filter out "this's", "which're", etc.
        if "s'" in translation or "ch'" in translation:
            continue

        # Use AOEU instead of KWR* for "I'*" to avoid *
        if Stroke('KWR*') in stroke and translation.startswith("I'"):
            stroke = stroke - Stroke('KWR*') + Stroke('AOEU')

        update(phrasing, stroke, translation)


remaps = {
    "TEPL":    "item",
    "TH-FT":   "theft", # E got stolen? or associate with TKPW-PB "gun"
    "THAUFLT": "thoughtful",

    "WHA*BG":  "whack",
    "WHAOL":   "whale", # arbitrary vowel
    "HO":      "whole",
    "WHAOUS":  "whose",

    "TPHOFRBG": "economic",
    "TPHOFRL":  "economical",

    "EUD":    "idea",
    "EULD":   "ideal",
    "HREULD": "ideally",
    "*EUD":   "id", # as in psychoanalysis

    "WR":   "where",
    "WR-T": "where the",
    "WRU":  "where you",

    "UFRT": "unfortunate",
    "UFRL": "unfortunately",
    "-FRT": "fortunate",
    "-FRL": "fortunately",
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
        remaps = {
            rtfcre: phrasing[rtfcre]
            for rtfcre in rtfcres
            if rtfcre in phrasing and phrasing[rtfcre] != translation
        }
        if remaps:
            if wrote:
                f.write('\n')
            f.write(translation)
            if translation in remaps_reversed:
                f.write(f' -> {remaps_reversed[translation]}')
            f.write('\n')
            wrote = True
            for rtfcre in rtfcres:
                f.write(f'  {rtfcre}')
                if rtfcre in remaps:
                    f.write(f' -> {remaps[rtfcre]}')
                f.write('\n')

with parent_dir.joinpath('phrasing.json').open('w') as f:
    json.dump(phrasing, f, indent=4)
