import re

def multiply_volta(m):
    reps = max(2, int(m.group(1)))
    return reps * (" " + m.group(2)) + " "

def extract_music(fcont):
    relsplit = fcont.split("\\relative")

    if len(relsplit) != 2:
        return None

    fragments = re.split(r"(\{|\})", relsplit[1])

    op = 0
    matched = False
    for i, bracket in enumerate(fragments[1::2]):
        if bracket == "{":
            op += 1
        else:
            op -= 1
        if op == 0:
            matched = True
            break

    if not matched:
        return None

    music = " ".join(fragments[2:2*i+1])

    music = re.sub(r"\\key\s.*?\\", "", music)
    music = re.sub(r"\\repeat\s+volta\s+(\d+)\s+\{(.*?)\}", multiply_volta, music, flags=re.DOTALL)

    return music


def get_lengths(fcont):
    music = extract_music(fcont)

    if not music:
        return None

    for bracket in ["(", ")", "[", "]"]:
        music = music.replace(bracket, " "+bracket+" ")

    regex = r"(?<!\S)(?:es|as|[a-h](?:[ei]s)?)[,']?[\?!]?(?=$|[\^\d\s]|\\breve)|[\(\[\)\]]"

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