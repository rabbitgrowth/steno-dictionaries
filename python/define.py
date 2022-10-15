LONGEST_KEY = 10

def lookup(strokes):
    strokes = iter(strokes)
    first = next(strokes)
    if first != 'TK*EF':
        raise KeyError
    output = '{^}"'
    for i, stroke in enumerate(strokes):
        if stroke == 'A*Z':
            output += '": "{^}'
            break
        if i:
            output += '/'
        output += stroke
    try:
        next(strokes)
    except StopIteration:
        return output
    else:
        raise KeyError
