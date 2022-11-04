import string

LONGEST_KEY = 20

ALPHABET = dict(zip([
    'A',
    'PW',
    'KR',
    'TK',
    'E',
    'TP',
    'TKPW',
    'H',
    'EU',
    'SKWR',
    'K',
    'HR',
    'PH',
    'TPH',
    'O',
    'P',
    'KW',
    'R',
    'S',
    'T',
    'U',
    'SR',
    'W',
    'KP',
    'KWR',
    'SWR',
], string.ascii_lowercase))

def lookup(strokes):
    if len(strokes) < 5:
        raise KeyError
    letters = ''.join(ALPHABET[stroke] for stroke in strokes)
    return f'{{>}}{{&{letters}}}'
