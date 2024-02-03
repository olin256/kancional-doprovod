from lxml import etree
from itertools import islice
from copy import deepcopy

bad_attributes = ["width", "default-x", "default-y"]
bad_elements = ["defaults", "supports", "print", "midi-instrument", "midi-device"]

def merge_parts(root):
    parts = list(root.iterchildren("part"))
    if len(parts) > 1:
        for staff, part in enumerate(parts, 1):
            staff_el = etree.Element("staff")
            staff_el.text = str(staff)
            for note in part.iter("note"):
                if note.find("staff") is None:
                    if note.find("rest") is None:
                        if (prev_el := note.find("stem")) is None:
                            prev_el = note.find("type")
                        prev_el.addnext(deepcopy(staff_el))
                    else:
                        note.append(deepcopy(staff_el))

        clefs = [part.find(".//clef") for part in parts]
        for i, clef in enumerate(clefs, 1):
            clef.set("number", str(i))
        curr_clef = clefs[0]
        for clef in clefs[1:]:
            curr_clef.addnext(clef)
            curr_clef = clef

        first_part = parts[0]
        for i, part in enumerate(parts[1:], 1):
            for voice in part.iter("voice"):
                voice.text = str(int(voice.text) + 4*i)
            for m1, m2 in zip(*(p.iterchildren("measure") for p in [first_part, part])):
                backup = m1.find("backup")
                if backup is None:
                    continue
                m1.append(deepcopy(backup))
                for el in m2.iterchildren("note", "backup"):
                    m1.append(el)
            root.remove(part)
        attributes = first_part.find(".//attributes")
        if attributes.find("staves") is None:
            staves = etree.Element("staves")
            staves.text = "2"
            attributes.find("clef").addprevious(staves)
        for score_part in islice(part_list := root.find("part-list"), 1, None):
            part_list.remove(score_part)


def remove_garbage(root, bad_elements=bad_elements, bad_attributes=bad_attributes):
    if bad_elements:
        for el in root.iter(*bad_elements):
            el.getparent().remove(el)

    if bad_attributes:
        for el in root.iter():
            for attr in bad_attributes:
                if attr in el.attrib:
                    del el.attrib[attr]


def remove_extra_clefs(part):
    for el in islice(part.iter("attributes"), 1, None):
        if el.find("clef") is not None:
            attr = el.getparent()
            if len(attr) > 1:
                attr.remove(el)
            else:
                attr.getparent().remove(attr)


def fix_pickup(part):
    first_measure = part.find("measure")
    attributes = first_measure.find("attributes")
    if (time := attributes.find("time")) is not None:
        divisions = int(attributes.findtext("divisions"))
        full_measure_len = 4*divisions*int(time.findtext("beats")) // int(time.findtext("beat-type"))
        first_measure_len = sum(int(n.findtext("duration")) for n in first_measure.iterchildren("note") if (n.findtext("voice") == "1") and (n.find("chord") is None))
        if full_measure_len != first_measure_len:
            first_measure.set("implicit", "yes")
            for i, measure in enumerate(part.iterchildren("measure")):
                measure.set("number", str(i))