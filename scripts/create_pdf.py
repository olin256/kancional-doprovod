import json
import subprocess
import re
import argparse
import os
from glob import iglob
from fname_utils import purify
from musicxml_to_ly import musicxml_to_ly, keys as fifths_to_pitch
from ordered_set import OrderedSet
from tqdm import tqdm

easy_keys = [
    "c", "des", "d", "es", "e", "f", "fis", "g", "as", "a", "bes", "b"
]


def transpose_str(fifths, shift):
    semitones_from_c = (7 * fifths) % 12
    target = semitones_from_c + shift
    octave_mark = ""
    if target >= 12:
        octave_mark = "'"
    elif target < 0:
        octave_mark = ","
    return f"{fifths_to_pitch[fifths]} {easy_keys[target % 12]}{octave_mark}"


def get_templates(ext):
    available_files = (
        fn for fn in iglob(f"../{ext}_templates/*.{ext}")
        if purify(fn) != "common"
    )
    ret = {}
    for fn in available_files:
        for char in purify(fn):
            ret[char] = fn
    return ret


def lyrics_repetition(m):
    lyrs = m[1]
    if lyrs[-1] == ".":
        return f" {lyrs[:-1]}, {lyrs} "
    else:
        return f" {lyrs} {lyrs} "


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--full", action=argparse.BooleanOptionalAction)
parser.add_argument("-i", "--inspect", action=argparse.BooleanOptionalAction)
parser.add_argument("-s", "--skip-bad", action=argparse.BooleanOptionalAction)
args = parser.parse_args()

if args.full:
    trs = range(-7, 8)
else:
    trs = range(1)

with open("selection_candidate.json", "r") as f:
    songs = json.load(f)

with open("typy_pisni.tsv", "r") as f:
    types = dict(l.strip().split("\t") for l in f)

with open("../ly_templates/pocty_systemu.tsv", "r") as f:
    system_counts = dict(l.strip().split("\t") for l in f)

ly_templates = get_templates("ly")
ly_template_contents = {}
for fname in set(ly_templates.values()):
    with open(fname, "r", encoding="utf-8") as f:
        ly_template_contents[fname] = f.read()

tex_templates = get_templates("tex")
bad = set(map(purify, iglob("../log_ly/*.log")))

roman = (
    "I,II,III,IV,V,VI,VII,VIII,IX,X,XI,XII,XIII,XIV,XV,XVI,"
    "XV,XVI,XVII,XVIII,XIX,XX,XXI,XXII,XXIII,XXIV,XXV"
).split(",")

for song, song_name in tqdm(songs.items()):
    with open(f"../song_data/{song}.json", "r", encoding="utf-8") as f:
        stanzas = json.load(f)["stanzas"]

    for s in stanzas:
        s["section"] = str(s["section"] or "")

    stanza_sheets = OrderedSet(s["stanza_sheet"] for s in stanzas)
    song_type = types[song]

    if song_type not in ly_templates:
        continue

    if song_type in ["m", "p"]:
        last_section = ""

        for stanza_sheet in stanza_sheets:
            fn = f"{song}-{stanza_sheet}"
            if args.skip_bad and fn in bad:
                continue

            current_template = ly_template_contents[ly_templates[song_type]]
            current_stanzas = {
                i: s for i, s in enumerate(stanzas, 1)
                if s["stanza_sheet"] == stanza_sheet
            }

            stanza_nos = list(current_stanzas.keys())
            in_fn = f"../musicxml/{fn}.xml"

            if not os.path.isfile(in_fn):
                print(f"chybi xml: {fn}")
                continue

            current_template, score_template = current_template.split(
                "% SCORE", 1
            )
            current_template = current_template.replace(
                "TITLE", song_name, 1
            ).replace(
                "SUBTITLE", song, 1
            )

            if fn in system_counts:
                current_template = current_template.replace(
                    "% SYSTEM_COUNT", f"system-count = {system_counts[fn]}", 1
                )

            with open(in_fn, "r", encoding="utf-8") as f:
                voices = musicxml_to_ly(f)
                f.seek(0)
                fifths = int(re.search(r"<fifths>(-?\d)</fifths>", f.read())[1])

            current_template = current_template.replace("% VOICES", voices, 1)
            ly_lyrics = ""

            for i, (s_no, s) in enumerate(current_stanzas.items()):
                lyrics = s["lyrics"]
                lyrics = re.sub(r"-+", " -- ", lyrics)
                lyrics = re.sub(
                    r"\[:\s*(.*?)\s*:\]", lyrics_repetition,
                    lyrics, flags=re.DOTALL
                )
                lyrics = re.sub(r"\s+", " ", lyrics)
                ly_lyrics += (
                    f"sloka{roman[i]} = \\lyricmode {{ "
                    f"\\set stanza = \"{s_no}.\"\n"
                    f"{lyrics}\n}}\n\n"
                )

            current_template = current_template.replace("% LYRICS", ly_lyrics, 1)

            tex_source = (
                f"\\def\\cislo{{{song}}}\n\\def\\jmeno{{{song_name}}}\n"
            )
            podnadpis = ", ".join(OrderedSet(
                s["section"] for s in current_stanzas.values()
            ))
            tex_source += f"\\def\\podnadpis{{{podnadpis}}}\n"
            pocet_slok = len(current_stanzas)
            max_sloka = stanza_nos[-1]
            min_sloka = stanza_nos[0]
            tex_source += (
                f"\\def\\minsloka{{{min_sloka}}}\n"
                f"\\def\\maxsloka{{{max_sloka}}}\n"
                f"\\def\\pretokslok{{{(pocet_slok - 1) % 3}}}\n"
            )

            last_section = list(current_stanzas.values())[0]["section"]
            for s_no, s in list(current_stanzas.items())[1:]:
                curr_section = s["section"]
                if curr_section == last_section:
                    curr_section = ""
                else:
                    last_section = curr_section

                stanza_lyrics = s["lyrics"].replace(
                    "--", ""
                ).replace(
                    "_", " "
                ).replace(
                    "[:", "\n[:"
                ).split("\n")

                tex_source += (
                    f"\\sloka{{{s_no}}}{{{curr_section}}}{{%\n"
                    + "\n".join(
                        f"    \\slokaline{{{sl}}}" for sl in map(
                            lambda x: x.strip(), stanza_lyrics
                        ) if sl
                    )
                    + "}\n"
                )

            for shift in trs:
                fn_shift = f"{fn}_{shift}"
                pdf_fname = f"../pdf_tmp/{fn_shift}"
                crop_fname = f"../pdf_crop/{fn_shift}.pdf"
                final_fname = f"../pdf/{fn_shift}.pdf"

                if os.path.isfile(final_fname):
                    continue

                score_template_transposed = score_template.replace(
                    "% TRANSPOSE", transpose_str(fifths, shift), 1
                )

                ly_source = current_template
                last_section = ""
                section_counter = 1

                for i, s in enumerate(current_stanzas.values()):
                    curr_score_template = score_template_transposed.replace(
                        "\\SLOKA", f"\\sloka{roman[i]}", 1
                    )
                    section = s["section"]
                    if section:
                        if section == last_section:
                            section_counter += 1
                            piece = f"{section} {section_counter}"
                        else:
                            piece = section
                            section_counter = 1
                        curr_score_template = curr_score_template.replace(
                            "% SCORE_TITLE", f'piece = "{piece}"', 1
                        )
                        last_section = section
                    else:
                        last_section = ""
                        section_counter = 1

                    if i:
                        ly_source += "\\pageBreak\n\n"
                    ly_source += curr_score_template

                res = subprocess.run(
                    [
                        "lilypond",
                        "-dinclude-settings=../ly_templates/common.ly",
                        "-o", pdf_fname, "-"
                    ],
                    shell=True, encoding="utf-8", text=True,
                    input=ly_source, capture_output=True
                )

                stderr = res.stderr.lower()
                if "varov" in stderr or "chyba" in stderr:
                    print(f"{fn} bad")
                    with open(f"../ly/{fn_shift}.ly", "w", encoding="utf-8") as f:
                        f.write(ly_source)
                    with open(f"../log_ly/{fn}.log", "w", encoding="utf-8") as f:
                        f.write(res.stderr)
                    break

                if args.inspect:
                    break

                subprocess.run(
                    ["pdfcrop", pdf_fname, crop_fname],
                    shell=True, capture_output=True
                )

                transp_str = (
                    f"transpozice {str(shift).replace('-', '−')}"
                    if shift else "původní tónina"
                )
                with open(f"../tex/{fn_shift}.tex", "w", encoding="utf-8") as f:
                    f.write(tex_source)
                    f.write(f"\\def\\transpozice{{{transp_str}}}")

                subprocess.run(
                    [
                        "luatex",
                        f"--jobname={fn_shift}",
                        "--output-directory=../pdf",
                        tex_templates[song_type]
                    ],
                    shell=True, capture_output=True
                )
