#!/usr/bin/env python3
"""Word timeline for Talk mode: the SCRIPT's spelling + Whisper's word timing.
Whisper mishears Hinglish (and writes Hindi in Devanagari), so captions never come from it directly.
This aligns every script word to the heard words (Devanagari is transliterated, vowels are fuzzy),
takes the timing, and interpolates words Whisper missed.

usage: python3 align.py <whisper.json> <SCRIPT.md|script.txt> <out words.json>
       python3 align.py --selftest
SCRIPT.md: the teleprompter lines (starting with '>') are used if any exist, else every non-heading line.
whisper.json: `whisper <take> --output_format json --word_timestamps True` (any language setting).
Output rows: {id, w, t0, t1, line, heard, score[, interp]}. Rows with score < 0.45 or interp are worth a listen.
ponytail: O(script words x heard words) alignment, fine up to a few thousand words; chunk longer takes."""
import json, re, sys, difflib

C = dict(zip("कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह",
             ["k", "kh", "g", "gh", "n", "ch", "chh", "j", "jh", "n", "t", "th", "d", "dh", "n", "t", "th", "d", "dh", "n",
              "p", "ph", "b", "bh", "m", "y", "r", "l", "v", "sh", "sh", "s", "h"]))
C.update({"क़": "k", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "rh", "फ़": "f"})
V = {"अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u", "ए": "e", "ऐ": "e", "ओ": "o", "औ": "o", "ऑ": "o", "ऋ": "ri"}
M = {"ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "े": "e", "ै": "e", "ो": "o", "ौ": "o", "ॉ": "o", "ृ": "ri",
     "ं": "n", "ँ": "n", "ः": "h", "्": "", "़": ""}


def tr(w):  # Devanagari -> rough Roman
    out = ""
    for i, ch in enumerate(w):
        if ch in C: out += C[ch] + ("a" if i + 1 < len(w) and (w[i + 1] in C or w[i + 1] in V) else "")
        elif ch in V: out += V[ch]
        elif ch in M: out += M[ch]
        else: out += ch
    return out


def norm(w):
    w = re.sub(r"[^a-z0-9]", "", tr(w).lower())
    for a, b in (("w", "v"), ("ph", "f"), ("z", "j"), ("q", "k"), ("x", "ks"), ("ee", "i"), ("oo", "u"), ("aa", "a"), ("c", "k")):
        w = w.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", w)


def sk(w):  # consonant skeleton, tolerant of vowel spelling
    return re.sub(r"[aeiouyh]", "", norm(w)) or norm(w)


def sim(a, b):
    return max(difflib.SequenceMatcher(None, norm(a), norm(b)).ratio(), 0.9 * difflib.SequenceMatcher(None, sk(a), sk(b)).ratio())


def script_lines(text):
    lines = [l.rstrip() for l in text.splitlines()]
    tele = [l.lstrip("> ").strip() for l in lines if l.startswith(">")]
    return [l for l in (tele or [l.strip() for l in lines if l.strip() and not l.lstrip().startswith(("#", "|", "-", "*"))]) if l]


def align(wh, lines):
    W = [(x["word"].strip(), x["start"], x["end"]) for s in wh["segments"] for x in s.get("words", []) if x["word"].strip()]
    S = [(tok, li) for li, line in enumerate(lines) for tok in line.split()]
    n, m, GAP = len(S), len(W), -0.35
    D = [[0.0] * (m + 1) for _ in range(n + 1)]; B = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1): D[i][0] = i * GAP; B[i][0] = 1
    for j in range(1, m + 1): D[0][j] = j * GAP; B[0][j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = [D[i - 1][j - 1] + sim(S[i - 1][0], W[j - 1][0]) - 0.3, D[i - 1][j] + GAP, D[i][j - 1] + GAP]
            k = max(range(3), key=lambda q: c[q]); D[i][j] = c[k]; B[i][j] = k
    i, j, pair = n, m, {}
    while i > 0 or j > 0:
        k = B[i][j]
        if k == 0: pair[i - 1] = j - 1; i -= 1; j -= 1
        elif k == 1: i -= 1
        else: j -= 1
    out = []
    for i, (tok, li) in enumerate(S):
        j = pair.get(i)
        out.append({"id": i, "w": tok, "t0": round(W[j][1], 2) if j is not None else None, "t1": round(W[j][2], 2) if j is not None else None,
                    "line": li, "heard": W[j][0] if j is not None else "", "score": round(sim(tok, W[j][0]), 2) if j is not None else 0})
    end = wh["segments"][-1]["end"] if wh.get("segments") else 0.0
    i = 0
    while i < n:  # fill gaps between timed neighbours, weighted by word length
        if out[i]["t0"] is None:
            k = i
            while k < n and out[k]["t0"] is None: k += 1
            a = out[i - 1]["t1"] if i else 0.0; b = out[k]["t0"] if k < n else end
            tot = sum(len(out[q]["w"]) + 1 for q in range(i, k)); t = a
            for q in range(i, k):
                d = (b - a) * (len(out[q]["w"]) + 1) / tot
                out[q].update(t0=round(t, 2), t1=round(t + d * 0.9, 2), interp=True); t += d
            i = k
        else: i += 1
    for q in range(1, n):  # keep times monotonic
        if out[q]["t0"] < out[q - 1]["t0"]: out[q]["t0"] = out[q - 1]["t0"]
        out[q]["t1"] = max(out[q]["t1"], out[q]["t0"] + 0.04)
    return out, m, len(pair)


def selftest():
    heard = {"segments": [{"end": 3.0, "words": [{"word": " एक", "start": 0.1, "end": 0.3}, {"word": " सवाल", "start": 0.35, "end": 0.8},
             {"word": " PopDex", "start": 1.0, "end": 1.4}, {"word": " पे", "start": 1.45, "end": 1.6}, {"word": " tools", "start": 2.2, "end": 2.6}]}]}
    out, _, _ = align(heard, script_lines("# Script\n> Ek sawaal.\n> PopDEX pe kitne tools?"))
    got = {o["w"]: o for o in out}
    assert [o["w"] for o in out] == ["Ek", "sawaal.", "PopDEX", "pe", "kitne", "tools?"], "script spelling must survive"
    assert got["sawaal."]["t0"] == 0.35 and got["PopDEX"]["t0"] == 1.0 and got["tools?"]["t0"] == 2.2, "Devanagari/English timing"
    assert got["kitne"].get("interp") and 1.6 <= got["kitne"]["t0"] < 2.2, "missed word interpolated between neighbours"
    print("align selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    if len(sys.argv) != 4: sys.exit(__doc__)
    wh = json.load(open(sys.argv[1])); lines = script_lines(open(sys.argv[2]).read())
    out, m, matched = align(wh, lines)
    json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, indent=0)
    weak = [o for o in out if o["score"] < 0.45 and not o.get("interp")]
    print(f"script words {len(out)}, heard words {m}, matched {matched}, interpolated {sum(1 for o in out if o.get('interp'))}, weak (<0.45) {len(weak)}")
    li = -1
    for o in out:
        if o["line"] != li: li = o["line"]; print(f"\nL{li} {o['t0']:7.2f} ", end="")
        print(f"{o['w']}{'~' if o.get('interp') else ''}{'?' if o in weak else ''}", end=" ")
    print()
