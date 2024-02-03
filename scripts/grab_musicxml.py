import re
import glob
import json
import os
import re
from lxml import etree
from fix_xml import *
from fname_utils import purify

from ordered_set import OrderedSet
from collections import deque

parser = etree.XMLParser(remove_blank_text=True)

beam_part_str = ["", "begin", "continue", "end"]

def fix_beams(m):
    note = m.group(0)
    if "<voice>1</voice>" not in note:
        return note
    if ("<type>whole</type>" in note) or ("<type>breve</type>" in note) or ("<rest/>" in note):
        return note
    note_part = m.group(1)
    indent = m.group(2)
    note_outp = re.sub(r"\s*<beam[\s>].*</beam>", "", note_part, count=1, flags=re.DOTALL)
    if beam_buffer:
        beam_part, size = beam_buffer.popleft()
        if beam_part:
            note_outp += indent
            note_outp += '<beam number="'+str(size)+'">'
            note_outp += beam_part_str[beam_part]
            note_outp += '</beam>'
    note_outp += indent + "</note>"

    return note_outp


beam_files = {purify(fname): fname for fname in glob.glob("../beam_data/*.json")}
for fname in glob.glob("../beam_data_alt/*.json"):
    sn = purify(fname)
    if sn not in beam_files:
        beam_files[sn] = fname

song_dir = "../song_data/"

with open("kancional.json", "r", encoding="utf-8") as f:
    kancional = [s for s in json.load(f)["song"].values() if s["number"] >= 100]

html_select = {}

for song in kancional:
    cislo = str(song["number"]).zfill(3) + song["letter"]

    json_file = song_dir+cislo+".json"
    if not (os.path.isfile(json_file)):
        print(cislo, "chybi json")
        continue

    with open(json_file, "r", encoding="utf-8") as f:
        song_json = json.load(f)

    stanza_sheets = list(song_json["stanza_lengths"].keys())

    stanzas_zero_based = [int(s)-1 for s in stanza_sheets]

    stanza_names = [", ".join(OrderedSet(filter(None, (s["section"] for s in song_json["stanzas"][a:b])))) for a, b in zip(stanzas_zero_based, stanzas_zero_based[1:]+[None])]


    xmlfiles = glob.glob("../musicxml_source/"+cislo+"*.musicxml")

    if len(xmlfiles) != len(stanza_sheets):
        print(cislo, "ruzny pocet")
        continue

    html_select[cislo] = re.sub(r"\s+", " ", song["name"])

    for xmlfile, stanza_no, stanza_name in zip(xmlfiles, stanza_sheets, stanza_names):
        tot_fname = cislo + "-" + stanza_no

        cislo_enr = cislo
        if stanza_name:
            cislo_enr += " (" + stanza_name + ")"

        xml = etree.parse(xmlfile, parser)

        root = xml.getroot()

        remove_garbage(root)
        merge_parts(root)

        part = root.find("part")

        remove_extra_clefs(part)
        fix_pickup(part)

        work = etree.Element("work")
        etree.SubElement(work, "work-number").text = cislo_enr
        etree.SubElement(work, "work-title").text = song["name"]
        root.insert(0, work)

        if tot_fname in beam_files:
            with open(beam_files[tot_fname], "r", encoding="utf-8") as f:
                beam_data = json.load(f)

            if beam_data:
                beam_buffer = [(0,0)] * (beam_data[-1][1]+1)
                for start, end, size in beam_data:
                    beam_buffer[start] = (1, size)
                    for i in range(start+1, end):
                        beam_buffer[i] = (2, size)
                    beam_buffer[end] = (3, size)

                beam_buffer = deque(beam_buffer)
            else:
                beam_buffer = deque()

            for note in part.iter("note"):
                if note.findtext("voice") != "1":
                    continue
                if note.find("rest") is not None:
                    continue
                if note.findtext("type") in ["whole", "breve"]:
                    continue
                beam = note.find("beam")
                if beam is not None:
                    note.remove(beam)
                if beam_buffer:
                    beam_part, size = beam_buffer.popleft()
                    if beam_part:
                        etree.SubElement(note, "beam", number=str(size)).text = beam_part_str[beam_part]

        xml.write("../musicxml/"+tot_fname+".xml", pretty_print=True, xml_declaration=True, encoding="utf-8")


with open("selection_candidate.json", "w", encoding="utf-8") as f:
    json.dump(html_select, f)