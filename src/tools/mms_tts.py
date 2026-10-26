#!/usr/bin/env python3
"""Synthesize Tibetan word clips with facebook/mms-tts-adx (Amdo, offline).

Every item is synthesized with a trailing tsheg ་ (after ཾ/ྃ->མ, any final
shad removed); this is the default for all future words.

Usage: HF_HUB_OFFLINE=1 python tts.py items.tsv
items.tsv: one `id<TAB>text` per line. Output: <id>.mp3 + manifest.tsv here.
"""
import os
import subprocess
import sys
import unicodedata

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import torch
from transformers import AutoTokenizer, VitsModel

OUT = os.path.dirname(os.path.abspath(__file__))
MODEL = "facebook/mms-tts-adx"  # Amdo Tibetan (ISO 639-3 adx)
SPEAKING_RATE = 0.8
LEAD_SIL = 0.08
TAIL_SIL = 0.35
FADE = 0.020
PEAK_DBFS = -1.0
TRIM_DB = -40.0  # relative to the clip's peak
LEAD_PAD = 0.015  # kept before the first above-threshold sample
TRIM_PAD = 0.030  # kept after the last one (fade lives inside this)

SUBST = {"ཾ": "མ", "ྃ": "མ"}  # ཾ ྃ -> མ


def prepare(text):
    text = "".join(SUBST.get(c, c) for c in text)
    # Default for all words (synthesis only; manifest keeps the original text):
    # adx tends to swallow or weaken the final syllable (ཀུན་ལ -> "kün"), so
    # every item gets a trailing tsheg. Any trailing shad is dropped first.
    text = text.rstrip().rstrip("།").rstrip()
    if not text.endswith("་"):
        text += "་"
    return text


def dropped_chars(tok, text):
    """Characters the tokenizer silently drops (not in its vocab)."""
    vocab = tok.get_vocab()
    norm = tok.normalize_text(text) if hasattr(tok, "normalize_text") else text
    if getattr(tok, "do_lower_case", False):
        norm = norm.lower()
    return sorted({c for c in norm if c not in vocab})


def trim(wav, sr):
    peak = np.max(np.abs(wav)) or 1.0
    thr = peak * 10 ** (TRIM_DB / 20)
    win = int(sr * 0.01)
    env = np.convolve(np.abs(wav), np.ones(win) / win, mode="same")
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return wav
    # keep a margin so soft onsets/codas are not clipped
    start = max(0, idx[0] - int(sr * LEAD_PAD))
    end = min(len(wav), idx[-1] + int(sr * TRIM_PAD))
    return wav[start:end]


def post(wav, sr):
    wav = trim(wav, sr)
    peak = np.max(np.abs(wav)) or 1.0
    wav = wav * (10 ** (PEAK_DBFS / 20) / peak)
    # trim() keeps TRIM_PAD of below-threshold decay after the last syllable;
    # the 20 ms fade covers only that decay, never the syllable itself.
    n_fade = int(sr * FADE)
    wav = wav.astype(np.float32)
    wav[-n_fade:] *= np.linspace(1.0, 0.0, n_fade, dtype=np.float32)
    lead = np.zeros(int(sr * LEAD_SIL), dtype=np.float32)
    tail = np.zeros(int(sr * TAIL_SIL), dtype=np.float32)
    return np.concatenate([lead, wav, tail])


def main(items_path):
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = VitsModel.from_pretrained(MODEL).eval()
    model.speaking_rate = SPEAKING_RATE
    sr = model.config.sampling_rate

    items = []
    with open(items_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.strip():
                iid, text = line.split("\t", 1)
                items.append((iid.strip(), unicodedata.normalize("NFC", text.strip())))

    warnings, rows = [], []
    for iid, text in items:
        synth = prepare(text)
        bad = dropped_chars(tok, synth)
        if bad:
            warnings.append(f"{iid}\t{text}\tdropped: {' '.join('U+%04X' % ord(c) for c in bad)}")
        inputs = tok(synth, return_tensors="pt")
        torch.manual_seed(0)
        with torch.no_grad():
            wav = model(**inputs).waveform[0].numpy()
        wav = post(wav, sr)
        mp3 = os.path.join(OUT, f"{iid}.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1",
             "-i", "pipe:0", "-ar", "22050", "-ac", "1", "-b:a", "64k", mp3],
            input=wav.astype("<f4").tobytes(), check=True)
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
            capture_output=True, text=True, check=True).stdout.strip())
        rows.append((iid, f"{iid}.mp3", f"{dur:.3f}", text))
        print(iid, f"{dur:.3f}", text, flush=True)

    with open(os.path.join(OUT, "manifest.tsv"), "w", encoding="utf-8") as f:
        f.write("id\tfile\tduration_seconds\ttext\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    with open(os.path.join(OUT, "tokenizer_warnings.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(warnings) + ("\n" if warnings else ""))

    durs = [float(r[2]) for r in rows]
    print(f"files={len(rows)} min={min(durs):.3f} max={max(durs):.3f} warnings={len(warnings)}")
    for w in warnings:
        print("WARN", w)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "items.tsv"))
