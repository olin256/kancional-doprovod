from apply_breaks_tf import break_lyrics
from get_lengths import get_lengths
from compact_json_encoder import CompactJSONEncoder

import re
import glob
import os
import json
import tqdm

def purify(fname):
    return os.path.splitext(os.path.basename(fname))[0]

lily_dir = "../lily_source/"
lily_dir_alt = "../lily_source_alt/"

lily_files = {purify(fname): fname for fname in glob.glob(lily_dir + "*.ly")}

for fname in glob.glob(lily_dir_alt + "*.ly"):
    song_no = purify(fname)
    if song_no not in lily_files:
        lily_files[song_no] = fname

available_lily_sources = set(sn[:-2] for sn in lily_files.keys() if sn.endswith("-1"))


with open("kancional.json", "r", encoding="utf-8") as f:
    kancional = [s for s in json.load(f)["song"].values() if s["number"] >= 100]

for song in tqdm.tqdm(kancional):
    cislo = str(song["number"]).zfill(3) + song["letter"]

    if cislo not in available_lily_sources:
        continue

    lily_sources = [sn for sn in lily_files.keys() if sn.startswith(cislo+"-")]

    stanza_sheets = [int(sn.split("-")[-1]) for sn in lily_sources]

    stanza_lengths = {}

    for sn, num in zip(lily_sources, stanza_sheets):
        with open(lily_files[sn], "r", encoding="utf-8") as f:
            fcont = f.read()
        stanza_lengths[num] = get_lengths(fcont)

    stanzas = []
    stanza_no = 0

    for stanza in song["stanza"].values():
        stanza_no += 1
        if stanza_no in stanza_sheets:
            stanza_sheet = stanza_no
        if stanza["stanza_section"]:
            section = stanza["stanza_section"]["description"]
        else:
            section = None
        broken_lyrics = break_lyrics(stanza["content"], preserve_whitespace=True)
        stanzas.append({"stanza_sheet": stanza_sheet, "section": section, "lyrics": broken_lyrics})

    outp = {"stanzas": stanzas, "stanza_lengths": stanza_lengths}

    # delky = [len(re.split(r"\s+|-+", sl["lyrics"])) for sl in outp["stanzas"]]
    # if len(set(delky)) > 1:
        # print(cislo, delky)

    with open("../song_data/"+cislo+".json", "w", encoding="utf-8") as f:
        json.dump(outp, f, ensure_ascii=False, cls=CompactJSONEncoder)
