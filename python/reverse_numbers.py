LONGEST_KEY = 1

def lookup(strokes):
    (stroke,) = strokes
    if 'U' not in stroke:
        raise KeyError
    stroke = stroke.replace('U', '')
    if not stroke.isdigit():
        raise KeyError
    return stroke[::-1]
