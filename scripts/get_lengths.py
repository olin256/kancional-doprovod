import re
from itertools import count
from collections import deque

note_regex = (
    r"(?<!\S)"
    r"(?:es|as|[a-h](?:[ei]s)?)"
    r"[,']?"
    r"[\?!]?"
    r"(?=$|[\^\d\s\)\]]|\\breve)"
)
repeat_regex = (
    r"\\repeat\s+volta\s+(?P<reps>\d+)\s+"
    r"\{(?P<bn>\d+)@(?P<content>.*?)\}(?P=bn)@"
    r"\s*"
    r"(?:\\alternative\s+\{(?P<cn>\d+)@(?P<altcontent>.*?)\}(?P=cn)@)?"
)

def multiply_volta(m):
    reps = max(2, int(m["reps"]))
    content = m["content"]
    if altcontent := m["altcontent"]:
        altpart_iter = re.finditer(
            r"\{(?P<bn>\d+)@(?P<altpart>.*?)\}(?P=bn)@",
            altcontent,
            flags=re.DOTALL
        )
        alternatives = deque(n["altpart"] for n in altpart_iter)
        first = alternatives[0]
        for _ in range(reps-len(alternatives)):
            alternatives.appendleft(first)
        return " " + " ".join(f"{content} {alt}" for alt in alternatives) + " "
    else:
        return reps * (" " + content) + " "

def extract_music(fcont, has_repeat=False):
    _, relsplit = fcont.split("\\relative", 1)

    fragments = re.split(r"([\{\}])", relsplit)

    expand_repeats = (not has_repeat) and ("\\repeat" in relsplit)

    op = 0
    matched = False
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

    for bracket in ["(", ")", "[", "]"]:
        music = music.replace(bracket, " "+bracket+" ")

    if expand_repeats:
        music = re.sub(repeat_regex, multiply_volta, music, flags=re.DOTALL)
        music = re.sub(r"([\{\}])\d+@", r"\1", music)

    return music


def get_lengths(fcont):
    music = extract_music(fcont)

    if not music:
        return None

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