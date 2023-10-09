import re
import glob
import json
import os
import re

from ordered_set import OrderedSet
from collections import deque

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


song_dir = "../song_data/"

with open("kancional.json", "r", encoding="utf-8") as f:
    kancional = [s for s in json.load(f)["song"].values() if s["number"] >= 100]

html_select = {}

for song in kancional:
    cislo = str(song["number"]).rjust(3, "0") + song["letter"]

    if not (os.path.isfile(song_dir+cislo+".json")):
        print(cislo, "chybi json")
        continue

    with open(song_dir+cislo+".json", "r", encoding="utf-8") as f:
        song_json = json.load(f)

    stanza_sheets = list(song_json["stanza_lengths"].keys())

    stanzas_zero_based = [int(s)-1 for s in stanza_sheets]

    stanza_names = [", ".join(OrderedSet(filter(None, (s["section"] for s in song_json["stanzas"][a:b])))) for a, b in zip(stanzas_zero_based, stanzas_zero_based[1:]+[None])]


    xmlfiles = glob.glob("../musicxml_source/"+cislo+"*.musicxml")

    if len(xmlfiles) != len(stanza_sheets):
        print(cislo, "ruzny pocet")
        continue

    html_select[cislo] = song["name"]

    for xmlfile, stanza_no, stanza_name in zip(xmlfiles, stanza_sheets, stanza_names):
        tot_fname = cislo + "-" + stanza_no

        cislo_enr = cislo
        if stanza_name:
            cislo_enr += " (" + stanza_name + ")"

        with open(xmlfile, "r", encoding="utf-8") as f:
            xmlcontent = f.read()

        ident_pos = xmlcontent.find("  <identification>")

        outp = ""
        outp += xmlcontent[:ident_pos]
        outp += "  <work>\n"
        outp += "    <work-number>" + cislo_enr + "</work-number>\n"
        outp += "    <work-title>" + song["name"] + "</work-title>\n"
        outp += "    </work>\n"
        outp += xmlcontent[ident_pos:]

        beam_file = "../beam_data/"+tot_fname+".json"
        if os.path.isfile(beam_file):
            with open(beam_file, "r", encoding="utf-8") as f:
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

            parts = outp.split('<part id="P2">')

            parts[0] = re.sub(r"(<note[\s>].*?)(\s*)</note>", fix_beams, parts[0], flags=re.DOTALL)

            outp = '<part id="P2">'.join(parts)

        with open("../musicxml/"+tot_fname+".xml", "w", encoding="utf-8") as f:
            f.write(outp)

with open("selection_candidate.json", "w", encoding="utf-8") as f:
    json.dump(html_select, f)