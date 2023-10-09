import re
import tensorflow as tf
import numpy as np

from break_utils import word_to_seq

with open("exceptions.txt", "r", encoding="utf-8") as f:
    vyjimky = {w.replace("--", ""): w.replace("--", "|") for w in filter(None, (x.strip() for x in f))}

cutoff = .15

kratke = list("ksvz")

model = tf.keras.models.load_model("tf_cz_model.h5")

unisyls = set(list("aáeéiíoóuúůyý"))
sylcores = unisyls.union("ěrl")

def break_word_pattern(word, pattern):
    wlen = len(word)

    if wlen <= 2:
        return word

    wordlow = word.lower()

    if wordlow in vyjimky:
        i = 0
        outp = ""
        for c in vyjimky[wordlow]:
            if c == "|":
                outp += "--"
            else:
                outp += word[i]
                i += 1
        return outp

    pt = np.array([1.0] + pattern.tolist())
    pt[wlen] = 1.0

    break_pos = [i for i, val in enumerate(pt) if val > cutoff]


    while True:
        if len(break_pos) <= 2:
            break

        syls = [wordlow[a:b] for a, b in zip(break_pos, break_pos[1:])]

        bad_syls = [i for i, syl in enumerate(syls) if (not sylcores.intersection(syl)) or (len(syl)==1 and syl not in unisyls)]
        if not bad_syls:
            break

        pre_breaks = [break_pos[i] for i in bad_syls]
        post_breaks = [break_pos[i+1] for i in bad_syls]

        pre_break_p = pt[pre_breaks]
        post_break_p = pt[post_breaks]

        worst_pre_break = np.argmin(pre_break_p)
        worst_pre_break_p = pre_break_p[worst_pre_break]
        worst_post_break = np.argmin(post_break_p)
        worst_post_break_p = post_break_p[worst_post_break]

        if worst_pre_break_p < worst_post_break_p:
            union_pos = bad_syls[worst_pre_break]
        else:
            union_pos = bad_syls[worst_post_break]+1

        del break_pos[union_pos]


    outp = "--".join([word[a:b] for a, b in zip(break_pos, break_pos[1:])])


    return outp


def break_lyrics(lyrs, preserve_whitespace=False):
    lyrs = lyrs.strip()
    if preserve_whitespace:
        lyr_parts_full = re.split(r"(\s+)", lyrs)
        lyr_parts = lyr_parts_full[::2]
        whitespace = lyr_parts_full[1::2] + [""]
        outp = []
    else:
        lyr_parts = lyrs.split()
        outp = ""

    words_to_break = list(set([w.lower() for w in re.findall(r"\w+", lyrs) if len(w) > 2]))
    seqs_to_break = tf.ragged.constant([word_to_seq(v) for v in words_to_break])
    preds = model.predict(seqs_to_break, verbose=0)

    breaks = {w: p.numpy() for w, p in zip(words_to_break, preds)}

    for i, word in enumerate(lyr_parts):
        m = re.fullmatch(r"(.*?)([\w-]+)(.*?)", word)
        if m is None:
            if preserve_whitespace:
                outp.append(word)
            else:
                outp += word + " "
            continue


        core = m.group(2)
        corelow = core.lower()

        if corelow in kratke:
            if preserve_whitespace:
                outp.append(word)
                whitespace[i] = "_"
            else:
                outp += m.group(1) + core + "_"
        else:
            parts = core.split("-")
            partslow = corelow.split("-")
            newcore = "-".join([(break_word_pattern(p, breaks[pl]) if pl in breaks else p) for p, pl in zip(parts, partslow)])
            newword = m.group(1) + newcore + m.group(3)
            if preserve_whitespace:
                outp.append(newword)
            else:
                outp += newword + " "

    if preserve_whitespace:
        return "".join(word+space for word, space in zip(outp, whitespace))
    else:
        return outp.strip()