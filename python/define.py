LONGEST_KEY = 10

COMMANDS = {
    'TK*EF': ('A*Z', '{^}"', '": "",{#left}{#left}{^}'),
    'RA*U':  ('RA*UD', '', ''),
    'RAUR':  ('RAURD', '`', '`'),
}

def lookup(strokes):
    strokes = iter(strokes)
    first = next(strokes)
    end_stroke, start, end = COMMANDS[first]
    output = start
    for i, stroke in enumerate(strokes):
        if stroke == end_stroke:
            output += end
            break
        if i:
            output += '/'
        output += stroke
    try:
        next(strokes)
    except StopIteration:
        if not output:
            return '{#}'
        return output
    else:
        raise KeyError
