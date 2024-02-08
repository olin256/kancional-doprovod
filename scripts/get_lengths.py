import re
from itertools import count

note_regex = r"(?<!\S)(?:es|as|[a-h](?:[ei]s)?)[,']?[\?!]?(?=$|[\^\d\s\)\]]|\\breve)"

def multiply_volta(m):
    reps = max(2, int(m.group("reps")))
    return reps * (" " + m.group("content")) + " "

def extract_music(fcont, has_repeat=False):
    _, relsplit = fcont.split("\\relative", 1)

    fragments = re.split(r"([\{\}])", relsplit)

    expand_repeats = (not has_repeat) and ("\\repeat" in relsplit)

    op = 0
    matched = False
    # for i, bracket in enumerate(fragments[1::2]):
    for i, bracket in zip(count(1, 2), fragments[1::2]):
        if bracket == "{":
            if expand_repeats:
                fragments[i] = "{" + str(op) + "@"
            op += 1
        else:
            op -= 1
            if expand_repeats:
                fragments[i] = "}" + str(op) + "@"
        if op == 0:
            matched = True
            break

    if not matched:
        return None

    music = " ".join(fragments[2:i])

    music = re.sub(r"\\key\s.*?\\", "", music)

    if expand_repeats:
        music = re.sub(r"\\repeat\s+volta\s+(?P<reps>\d+)\s+\{(?P<bnum>\d+)@(?P<content>.*?)\}(?P=bnum)@", multiply_volta, music, flags=re.DOTALL)
        music = re.sub(r"([\{\}])\d+@", r"\1", music)

    return music


def get_lengths(fcont):
    music = extract_music(fcont)

    if not music:
        return None

    for bracket in ["(", ")", "[", "]"]:
        music = music.replace(bracket, " "+bracket+" ")

    regex = note_regex + r"|[\(\[\)\]]"

    notes_brackets = re.findall(regex, music)

    out_lengths = []

    in_bracket = False
    for fragment in notes_brackets:
        if in_bracket:
            if fragment in ")]":
                in_bracket = False
            elif fragment not in "([":
                out_lengths[-1] += 1
        else:
            if fragment in "([":
                in_bracket = True
            elif fragment not in ")]":
                out_lengths.append(0)

    return out_lengths