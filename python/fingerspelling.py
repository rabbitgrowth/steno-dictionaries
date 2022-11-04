import string

from plover.steno import Stroke

ALPHABET = {
    Stroke(chord): letter
    for chord, letter in zip([
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
    ], string.ascii_lowercase)
}

FORMATS = {
    Stroke('-FPLT'):  lambda letter: f'{{&{letter.upper()}}}',
    Stroke('*FPLT'):  lambda letter: f'{{&{letter.upper()}.}}',
    Stroke('*PLT'):   lambda letter: f'{{:stitch:{letter.upper()}}}', # HR*PLT "element"
    Stroke('-RBGS'):  lambda letter: f'{{>}}{{&{letter}}}',
    Stroke('*RBGS'):  lambda letter: f'{{>}}{{&{letter}.}}',
    Stroke('*BGS'):   lambda letter: f'{{>}}{{:stitch:{letter}}}',
    Stroke('-FRBGS'): lambda letter: f'{{>}}{{^{letter}}}',
}

LEFT = Stroke('STKPWHRAOEU')
REST = Stroke('#*FRPBLGTSDZ')

LONGEST_KEY = 1

def lookup(strokes):
    stroke = Stroke(strokes[0])
    left = stroke & LEFT
    rest = stroke & REST
    letter = ALPHABET[left]
    return FORMATS[rest](letter)
