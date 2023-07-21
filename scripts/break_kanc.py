from apply_breaks_tf import break_lyrics
from get_lengths import get_lengths

import re
import glob
import os
import json
import tqdm

lily_dir = "../lily_source/"

available_lily_sources = set(os.path.basename(fname).split("-")[0] for fname in glob.iglob(lily_dir+"*-1.ly"))

with open("kancional.json", "r", encoding="utf-8") as f:
    kancional = [s for s in json.load(f)["song"].values() if s["number"] >= 100]

for song in tqdm.tqdm(kancional):
    cislo = str(song["number"]).rjust(3, "0") + song["letter"]

    if cislo not in available_lily_sources:
        continue

    lily_sources = glob.glob(lily_dir + cislo + "-*.ly")

    stanza_sheets = [int(os.path.basename(fname).split("-")[-1][:-3]) for fname in lily_sources]

    stanza_lengths = {}

    for fname, num in zip(lily_sources, stanza_sheets):
        with open(fname, "r", encoding="utf-8") as f:
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
        json.dump(outp, f, ensure_ascii=False)