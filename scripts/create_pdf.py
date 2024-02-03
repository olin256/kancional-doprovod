import json
import subprocess
import re
from glob import iglob
from fname_utils import purify
from musicxml_to_ly import musicxml_to_ly
from ordered_set import OrderedSet

with open("selection_candidate.json", "r") as f:
    songs = json.load(f)

with open("typy_pisni.tsv", "r") as f:
    types = dict(l.strip().split("\t") for l in f)

templates = dict()
for fname in iglob("../ly_templates/*.ly"):
    with open(fname, "r", encoding="utf-8") as f:
        templates[purify(fname)] = f.read()

trs = {0: "c c", 1: "c cis", 2: "c d", 3: "c es", 4: "c e", 5: "c f", 6: "c fis", 7: "c g", -1: "c b,", -2: "c bes,", -3: "c a,", -4: "c as,", -5: "c g,", -6: "c fis,", -7: "c f,"}
# trs = {0: "c c"}
# trs = {-2: "c bes,"}

roman = "I,II,III,IV,V,VI,VII,VIII,IX,X,XI,XII,XIII,XIV,XV,XVI,XV,XVI,XVII,XVIII,XIX,XX,XXI,XXII,XXIII,XXIV,XXV".split(",")

for song, song_name in songs.items():
    with open("../song_data/"+song+".json", "r", encoding="utf-8") as f:
        stanzas = json.load(f)["stanzas"]

    stanza_sheets = OrderedSet(s["stanza_sheet"] for s in stanzas)

    song_type = types[song]
    if song_type not in templates:
        continue

    current_template = templates[song_type]

    if song_type == "p":
        fn = song+"-1"
        in_fn = "../musicxml/"+fn+".xml"

        current_template, score_template = current_template.split("% SCORE", 1)

        current_template = current_template.replace("TITLE", song_name, 1).replace("SUBTITLE", song, 1)

        with open(in_fn, "r", encoding="utf-8") as f:
            voices = musicxml_to_ly(f)

        current_template = current_template.replace("% VOICES", voices, 1)

        ly_lyrics = ""

        for i, s in enumerate(stanzas):
            lyrics = s["lyrics"]
            lyrics = re.sub(r"-+", " -- ", lyrics)
            lyrics = re.sub(r"[:(.*?):]", " \1 \1 ", lyrics)
            lyrics = re.sub(r"\s+", " ", lyrics)
            ly_lyrics += f"sloka{roman[i]} = \\lyricmode {{ \\set stanza = \"{str(i+1)}.\"\n"
            ly_lyrics += lyrics
            ly_lyrics += "\n}\n\n"

        current_template = current_template.replace("% LYRICS", ly_lyrics, 1)

        tex_source = ""
        tex_source += f"\\def\\cislo{{{song}}}\n\\def\\jmeno{{{song_name}}}\n"
        max_sloka = len(stanzas)
        tex_source += f"\\def\\maxsloka{{{max_sloka}}}\n\\def\\pretokslok{{{(max_sloka-1)%3}}}\n"
        for i, s in enumerate(stanzas[1:], 2):
            stanza_lyrics = s["lyrics"].replace("--", "").replace("_", " ").split("\n")
            tex_source += f"\\sloka{{{i}}}{{%\n"
            tex_source += "\n".join(f"    \\slokaline{{{sl}}}" for sl in stanza_lyrics)
            tex_source += "}\n"

        for shift, tr in trs.items():
            fn_shift = fn+"_"+str(shift)
            pdf_fname = "../pdf_tmp/"+fn_shift
            crop_fname = "../pdf_crop/"+fn_shift+".pdf"
            score_template_transposed = score_template.replace("% TRANSPOSE", tr, 1)
            ly_source = current_template
            for i in range(len(stanzas)):
                curr_score_template = score_template_transposed.replace("\\SLOKA", "\\sloka"+roman[i], 1)
                if i:
                    ly_source += "\\pageBreak\n\n"
                ly_source += curr_score_template

            res = subprocess.run(["lilypond", "-dinclude-settings=../ly_templates/common.ly", "-o", pdf_fname, "-"], shell=True, encoding="utf-8", text=True, input=ly_source, capture_output=True)
            stderr = res.stderr.lower()
            if ("varov" in stderr) or ("chyba" in stderr):
                print(fn + " bad")
                with open("../ly/"+fn_shift+".ly", "w", encoding="utf-8") as f:
                    f.write(ly_source)
                with open("../log_ly/"+fn+".log", "w", encoding="utf-8") as f:
                    f.write(res.stderr)
                break

            subprocess.run(["pdfcrop", pdf_fname, crop_fname], shell=True, capture_output=True)

            transp_str = ("transpozice "+str(shift).replace("-", "−")) if shift else "původní tónina"
            with open("../tex/"+fn_shift+".tex", "w", encoding="utf-8") as f:
                f.write(tex_source)
                f.write(f"\\def\\transpozice{{{transp_str}}}")

            subprocess.run(["luatex", "--jobname="+fn_shift, "--output-directory=../pdf", "../tex_templates/p"], shell=True, capture_output=True)
