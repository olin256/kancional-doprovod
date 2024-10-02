from glob import iglob
from fname_utils import purify
from itertools import groupby
import json

for fname in iglob("../song_data/*.json"):
    with open(fname, "r", encoding="utf-8") as f:
        stanzas = json.load(f)["stanzas"]

    for sheet, data in groupby(stanzas, lambda s: s["stanza_sheet"]):
        lyr_lens = [len(s["lyrics"].replace("-", " ").split()) for s in data]
        if len(set(lyr_lens)) > 1:
            print(purify(fname), sheet, lyr_lens)