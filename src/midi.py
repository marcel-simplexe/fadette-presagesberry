# -*- coding: utf-8 -*-
"""
midi.py — the engraving. The model composed a symbolic score (notes); here, with
no model, we engrave it into a deterministic .mid file, and derive the same voicing
the browser will sound. A bagpipe drone — tonic and fifth, tuned to the melody — is
held continuous beneath the chanter, for the Berry veillee air (musette du Centre).
"""
from __future__ import annotations
from collections import Counter
import mido

_TICKS = 480
_TEMPO_BPM = 72
_PROG_BAGPIPE = 109   # General MIDI: Bag pipe


def _clean(notes) -> list:
    out = []
    for n in notes or []:
        try:
            p = int(n["note"]) % 128
            s = max(0.0, float(n.get("start", 0.0)))
            d = max(0.05, float(n.get("duration", 0.5)))
            f = max(1, min(127, int(n.get("force", 70))))
        except (KeyError, TypeError, ValueError):
            continue
        out.append({"note": p, "start": s, "dur": d, "force": f})
    out.sort(key=lambda x: x["start"])
    return out


def _tonic(clean) -> int:
    """The drone's tonic: the most-sounded pitch class, tie broken low, dropped
    into a low octave so it sits under the chanter."""
    pcs = Counter(n["note"] % 12 for n in clean)
    pc = sorted(pcs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    t = pc + 36
    while t < 38:
        t += 12
    while t > 50:
        t -= 12
    return t


def voicing(notes) -> dict:
    """One legible structure, shared by the .mid and the browser: the cleaned
    chanter notes, the held drone (tonic + fifth), the tempo, the end (in beats)."""
    clean = _clean(notes)
    if not clean:
        return {"notes": [], "drones": [], "tempo": _TEMPO_BPM, "end": 0.0}
    tonic = _tonic(clean)
    end = max(n["start"] + n["dur"] for n in clean)
    return {"notes": clean, "drones": [tonic, tonic + 7], "tempo": _TEMPO_BPM, "end": end}


def engrave(notes: list, path: str) -> str:
    v = voicing(notes)
    mid = mido.MidiFile(ticks_per_beat=_TICKS)
    melody = mido.MidiTrack(); mid.tracks.append(melody)
    melody.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(_TEMPO_BPM)))
    melody.append(mido.Message("program_change", program=_PROG_BAGPIPE, time=0))

    events = []
    for n in v["notes"]:
        events.append((n["start"], "on", n["note"], n["force"]))
        events.append((n["start"] + n["dur"], "off", n["note"], 0))
    events.sort(key=lambda x: (x[0], x[1] == "on"))
    clock = 0.0
    for when, kind, note, force in events:
        delta = max(0, int(round((when - clock) * _TICKS))); clock = when
        msg = "note_on" if kind == "on" else "note_off"
        melody.append(mido.Message(msg, note=note, velocity=force, time=delta))

    if v["drones"] and v["end"] > 0:
        bass = mido.MidiTrack(); mid.tracks.append(bass)
        bass.append(mido.Message("program_change", program=_PROG_BAGPIPE, time=0))
        for d in v["drones"]:                         # tonic + fifth, struck together
            bass.append(mido.Message("note_on", note=d, velocity=42, time=0))
        last = int(round(v["end"] * _TICKS))
        for i, d in enumerate(v["drones"]):           # released together at the end
            bass.append(mido.Message("note_off", note=d, velocity=0, time=last if i == 0 else 0))

    mid.save(path)
    return path
