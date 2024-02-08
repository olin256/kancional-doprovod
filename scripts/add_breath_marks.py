from lxml import etree
from get_lengths import note_regex, extract_music
import re


def add_breath_marks(part, lyfile, has_repeat):
    music = extract_music(lyfile.read(), has_repeat)
    regex = note_regex + r"|\\breathe"
    positions = []
    curr_pos = -1
    for m in re.finditer(regex, music):
        if m[0] == "\\breathe":
            positions.append(curr_pos)
        else:
            curr_pos += 1
    if positions:
        notes = [n for n in part.iter("note") if (n.find("rest") is None) and (n.find("chord") is None) and (n.findtext("voice") == "1")]
        for pos in positions:
            if pos >= len(notes):
                continue
            note = notes[pos]
            if (notations := note.find("notations")) is None:
                notations = etree.SubElement(note, "notations")
            etree.SubElement(etree.SubElement(notations, "articulations"), "breath-mark")