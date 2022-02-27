import collections
import functools
import itertools
import json
import operator
import pathlib
import re

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

i = {"KWR": "I"}

plural_pronoun = {
    "U":   "you",
    "W":   "we",
    "THE": "they",
}

singular_pronoun = {
    "H":  "he",
    "SH": "she",
    "T":  "it",
    "TH": "this",
}

pronoun = i | plural_pronoun | singular_pronoun

starter = {
    "SKP":  "and",
    "THA":  "that",
    "WHA":  "what",
    "WH":   "when",
    "WHR":  "where", # overrides "whether"
    "SKPH": "which", # KH doubled horizontally
    "WHO":  "who",
    "TWH":  "why",   # looks like Y
}

to = {
    "TO":    "to",
    "SKPAO": "and to",
    "SRAO":  "have to",
}

is_  = {"-S":  "is",  "*S":  "^'s"}
am   = {"-PL": "am",  "*PL": "^'m"}
are  = {"-R":  "are", "*R":  "^'re"}
was  = {"-FS": "was"}
were = {"-RP": "were"}
be   = {"-B":  "be"}
been = {"-B":  "been"}

be_forms = is_ | are | was | were # exclude "am"

have = {"-F": "have", "*F": "^'ve"}
has  = {"-Z": "has"} # is    -> ^'s
had  = {"-D": "had"} # would -> ^'d

have_forms = have | has | had

the = {"-T": "the"}

patterns.extend([
    (i,                am  | was, maybe(the)),
    (plural_pronoun,   are,       maybe(the)),
    (singular_pronoun, is_ | was, maybe(the)),
    (pronoun,          were,      maybe(the)),
    (starter,          be_forms,  maybe(the)),
    (to,               be,        maybe(the)),

    (i | plural_pronoun, have | had, maybe(been), maybe(the)),
    (singular_pronoun,   has  | had, maybe(been), maybe(the)),
    (starter,            have_forms, maybe(been), maybe(the)),
    (to,                 have,       maybe(been), maybe(the)),
])

# Verbs

verb = {
    "-BL":   "believe",
    "-FL":   "feel",
    "-FD":   "find",
    "-GT":   "get",
    "-GS":   "guess",
    "-FPL":  "know",
    "-LG":   "like",
    "*FL":   "love",
    "-RPL":  "remember",
    "-PBG":  "think",
    "-PT":   "want",
}

verbs = {
    "-BLZ":   "believes",
    "-FLZ":   "feels",
    "-FDZ":   "finds",
    "-GTS":   "gets",
    "-FPLZ":  "knows",
    "-LGZ":   "likes",
    "*FLZ":   "loves",
    "-RPLZ":  "remembers",
    "-PBGZ":  "thinks",
    "-PTS":   "wants",
}

verbed = {
    "-FLT": "felt",
    "-GD":  "got",
    "-BS":  "said",
}

modal_verb = {
    "-BG":   "can",
    "-BGD":  "could",
    "-RB":   "shall",
    "-RBD":  "should",
    "-L":    "will",
    "-LD":   "would",
    "-FR":   "may", # overrides "ever"
    "-FRT":  "might",
    "-FRTS": "must",
    "*L":    "^'ll",
    "*D":    "^'d", # could be short for "had" too, so use *D instead of *LD
}

negative = {
    "O":  "don't",
    "EU": "didn't",
    "A":  "can't",
    "U":  "couldn't",
}

really = {"-RL": "really"}

patterns.extend([
    (i | plural_pronoun, verb         | verbed | modal_verb | really),
    (singular_pronoun,          verbs | verbed | modal_verb | really),
    (starter,            verb | verbs | verbed | modal_verb | really),
    (i, negative,        verb                               | really),
    (to,                 verb                               | really),
])

# Three-part phrases with medial pronouns

if_ = {"STP": "if"} # with arbitrary S

medial_i   = {"EU": "I"}
medial_you = {"U":  "you"}
medial_he  = {"E":  "he"}

medial_pronoun = medial_i | medial_you | medial_he

patterns.extend([
    (starter | if_, medial_i,       am  | was, maybe(the)),
    (starter | if_, medial_you,     are,       maybe(the)),
    (starter | if_, medial_he,      is_ | was, maybe(the)),
    (starter | if_, medial_pronoun, were,      maybe(the)),

    (starter | if_, medial_i | medial_you, have | had, maybe(been), maybe(the)),
    (starter | if_, medial_he,             has  | had, maybe(been), maybe(the)),

    (starter | if_, medial_i | medial_you, maybe(verb  | verbed | modal_verb | really)),
    (starter | if_, medial_he,             maybe(verbs | verbed | modal_verb | really)),
])

# Special verbs

can = {"-BG": "can"}
see = {"-Z":  "see"} # clashes with "has"
say = {"-BZ": "say"} # clashes with "has been"

patterns.extend([
    (i | plural_pronoun,         maybe(can), see),
    (i | plural_pronoun,         say),
    (singular_pronoun | starter, can, see),
    (i, negative,                see | say),
    (to,                         see | say),

    (starter | if_, medial_i | medial_you, maybe(can), see),
    (starter | if_, medial_i | medial_you, say),
    (starter | if_, medial_he,             can, see),
])

# "a"

word_with_article = {
    "R":     "are",
    "TW":    "between",
    "TK":    "did",
    "TPO":   "for", # instead of TP-R
    "TPR":   "from",
    "TPH":   "in",
    "TPHAO": "into",
    "S":     "is",
    "OPB":   "on",
    "THRU":  "through",
    "W":     "with",
}

a = {"-LGTS": "a"}
article = the | a

patterns.append((starter | to | if_ | word_with_article, maybe(article)))


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

        # Filter out "this's", "which're", "and'd", etc.
        if re.search(r"(ch|d|s)'", translation):
            continue

        # Use AOEU instead of KWR* for "I'*" to avoid *
        if Stroke('KWR*') in stroke and translation.startswith("I'"):
            stroke = stroke - Stroke('KWR*') + Stroke('AOEU')

        update(phrasing, stroke, translation)


remaps = {
    "EUD":    "idea",
    "EULD":   "ideal",
    "HREULD": "ideally",
    "*EUD":   "id", # as in psychoanalysis

    "TPORPBT":  "fortunate",
    "TPORPBL":  "fortunately",
    "STPORPBT": "unfortunate",
    "STPORPBL": "unfortunately",

    "WHER":   "whether",
    "WHERT":  "whether",
    "WH*ERT": "whether",

    # EF "ever" is asymmetrical with TPHEFR "never", but -FR isn't
    # perfectly symmetrical either. EF/AF "ever after" is nice.
    "EF":      "ever",
    "TPOEF":   "forever",
    "HOUF":    "however", # standard
    "HOUFT":   "however the",
    "WHAEF":   "whatever",
    "WHAEFT":  "whatever the",
    "WHEF":    "whenever",
    "WHEFT":   "whenever the",
    "WHREF":   "wherever",
    "WHREFT":  "wherever the",
    "SKPHEF":  "whichever",
    "SKPHEFT": "whichever the",
    "WHOEF":   "whoever",
    "WHOEFT":  "whoever the",

    # Ugly compromise: add arbitrary K to words beginning with wh-
    "KWHABG":   "whack",
    "KWHAEUL":  "whale",
    "KWHEUF":   "whiff",
    "KWHEUFL":  "whiffle",
    "KWHEUPL":  "whim",
    "KWHEURL":  "whirl",
    "KWHEUFRP": "whisper",
    "KWHEULS":  "whistle",
    "KWHOEL":   "whole",
    "KWHOR":    "whore",
    "KWHORL":   "whorl",

    # Miscellaneous
    "TPAFBG": "fantastic",
    "TEPL":   "item",
    "TH-FT":  "theft", # E got stolen? or associate with TKPW-PB "gun"
    "AOULG":  "ugly",
    "WHAOUS": "whose",

    # Strokes that have been freed up
    "HAOED": "heed",
    "WAOED": "weed",
    "WAOEF": "weave",
}

remaps_reversed = {
    translation: rtfcre
    for rtfcre, translation in remaps.items()
}

phrasing |= remaps

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
