import string

ceske = "říšžťčýůňúěďáéó"

chars = string.ascii_lowercase + ceske

chars_to_int = {c: 1+chars.find(c) for c in chars}

def word_to_seq(word):
    return [chars_to_int.get(c, 0) for c in word]