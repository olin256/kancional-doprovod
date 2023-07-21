import re
import glob
import json
import os

from ordered_set import OrderedSet

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

    stanza_names =  [", ".join(OrderedSet(filter(None, (s["section"] for s in song_json["stanzas"][a:b])))) for a, b in zip(stanzas_zero_based, stanzas_zero_based[1:]+[None])]


    xmlfiles = glob.glob("../musicxml_source/"+cislo+"*.musicxml")

    if len(xmlfiles) != len(stanza_sheets):
        print(cislo, "ruzny pocet")
        continue

    html_select[cislo] = song["name"]

    for xmlfile, stanza_no, stanza_name in zip(xmlfiles, stanza_sheets, stanza_names):

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

        with open("../musicxml/"+cislo+"-"+stanza_no+".xml", "w", encoding="utf-8") as f:
            f.write(outp)

with open("selection_candidate.json", "w", encoding="utf-8") as f:
    json.dump(html_select, f)