import re
import glob
import json
import os
import re
from lxml import etree
from fix_xml import *
from add_breath_marks import add_breath_marks
from fname_utils import purify

from ordered_set import OrderedSet
from collections import deque

parser = etree.XMLParser(remove_blank_text=True)

beam_part_str = ["", "begin", "continue", "end"]

beam_files = {purify(fname): fname for fname in glob.glob("../beam_data/*.json")}

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
        remove_extra_ties(part)
        fix_measures(part)

        work = etree.Element("work")
        etree.SubElement(work, "work-number").text = cislo_enr
        etree.SubElement(work, "work-title").text = song["name"]
        root.insert(0, work)

        has_repeat = part.find(".//repeat") is not None

        with open(f"../lily_source/{tot_fname}.ly", "r", encoding="utf-8") as f:
            add_breath_marks(part, f, has_repeat)

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
                if note.find("chord") is not None:
                    continue
                if note.findtext("type") in ["whole", "breve"]:
                    continue
                if (beam := note.find("beam")) is not None:
                    note.remove(beam)
                if beam_buffer:
                    beam_part, size = beam_buffer.popleft()
                    if beam_part:
                        beam = etree.Element("beam", number=str(size))
                        beam.text = beam_part_str[beam_part]
                        note.find("staff").addnext(beam)

        xml.write("../musicxml/"+tot_fname+".xml", pretty_print=True, xml_declaration=True, encoding="utf-8")


with open("selection_candidate.json", "w", encoding="utf-8") as f:
    json.dump(html_select, f)