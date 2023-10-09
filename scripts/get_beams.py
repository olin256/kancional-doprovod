import svgpathtools
import cmath
import subprocess
from collections import deque
from itertools import groupby
import glob
import tqdm
import json
import os

def left_bound(p):
    return min(pp.start.real for pp in p)

lily_command = ["lilypond", "-fsvg", "-dbackend=cairo", "-dinclude-settings=mini_settings.ly", "--output=tmp", "tmp.ly"]

for fn in tqdm.tqdm(glob.glob("../lily_source/*.ly")):
    with open(fn, "r", encoding="utf-8") as f:
        fcont = f.read()
    fcont = fcont.replace("\\relative", "\\unfoldRepeats \\relative").replace("volta 1", "volta 2")
    with open("tmp.ly", "w", encoding="utf-8") as f:
        f.write(fcont)

    subprocess.run(lily_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    paths, attributes = svgpathtools.svg2paths("tmp.svg")

    beams = [p for p, a in zip(paths, attributes) if "fill:rgb(0%,100%,0%)" in a["style"]]
    if not beams:
        outlist = []

    else:
        stems = [p for p, a in zip(paths, attributes) if "rgb(100%,0%,0%)" in a["style"]]
        stems.sort(key=left_bound)

        beam_pairs = [(p, left_bound(p)) for p in beams]
        beam_pairs.sort(key=lambda x: x[1])
        groups = [(l[0][0], len(l)) for l in (list(g) for _, g in groupby(beam_pairs, key=lambda x: x[1]))]

        beams, sizes = zip(*groups)

        beams = deque(beams)

        starts = []
        ends = []

        curr_beam = beams.popleft()
        in_beam = False

        for i, stem in enumerate(stems):
            meets = bool(len(curr_beam.intersect(stem)))
            if (not meets) and in_beam:
                ends.append(i-1)
                in_beam = False
                if beams:
                    curr_beam = beams.popleft()
                    meets = bool(len(curr_beam.intersect(stem)))
                else:
                    break
            if meets and (not in_beam):
                starts.append(i)
                in_beam = True

        if in_beam:
            ends.append(i)

        outlist = list(zip(starts, ends, sizes))

    with open("../beam_data/"+os.path.basename(fn)[:-3]+".json", "w", encoding="utf-8") as f:
        json.dump(outlist, f)

os.remove("tmp.svg")
os.remove("tmp.ly")