# -*- coding: utf-8 -*-
"""
memory.py — the archive. Everything that moves is written down and dated, the
prompts included. Nothing is erased.

  journal/YYYY-MM-DD.json   - the day's breaths (the source of truth)
  history/lens.json         - the current state of the prompts (text + score)
  history/drift/YYYY-MM-DD.json - one snapshot of the lens per day (the drift)
  docs/work/                - the served artifacts: the .mid files
                              (under docs/ so GitHub Pages serves them)
"""
from __future__ import annotations
import os
import json
import datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL = os.path.join(ROOT, "journal")
HISTORY = os.path.join(ROOT, "history")
DRIFT = os.path.join(HISTORY, "drift")
WORK = os.path.join(ROOT, "docs", "work")        # served by GitHub Pages

for d in (JOURNAL, HISTORY, DRIFT, WORK):
    os.makedirs(d, exist_ok=True)


def _config() -> dict:
    import yaml
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


# ----------------------------------------------------------------- breaths
def add_breath(breath: dict) -> None:
    path = os.path.join(JOURNAL, f"{today()}.json")
    day = read_day(today())
    day.setdefault("date", today())
    day.setdefault("breaths", []).append(breath)
    _write(path, day)


def add_breath_on(date_iso: str, breath: dict) -> None:
    """Append a breath to a GIVEN day (the POC writes on a simulated date)."""
    path = os.path.join(JOURNAL, f"{date_iso}.json")
    day = read_day(date_iso)
    day.setdefault("date", date_iso)
    day.setdefault("breaths", []).append(breath)
    _write(path, day)


def read_day(date: str) -> dict:
    path = os.path.join(JOURNAL, f"{date}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def all_days() -> list:
    out = []
    for f in sorted(x for x in os.listdir(JOURNAL) if x.endswith(".json")):
        with open(os.path.join(JOURNAL, f), encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


# ----------------------------------------------------------------- the lens
def read_lens() -> dict:
    """The live prompts. If lens.drift is false, they come straight from config
    (config is authoritative). If true, from history/lens.json once it exists,
    seeded from config on the first run."""
    conf = _config()
    p = conf.get("prompts", {}) or {}
    seed = {"notch": 0, "text": p.get("presage", ""), "score": p.get("air", ""),
            "text_en": p.get("presage_en", ""), "score_en": p.get("air_en", "")}
    if not conf.get("lens", {}).get("drift", True):
        seed["frozen"] = True
        return seed
    path = os.path.join(HISTORY, "lens.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return seed


def write_lens(prompts: dict, date: str | None = None) -> None:
    prompts = dict(prompts)
    prompts["updated_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    _write(os.path.join(HISTORY, "lens.json"), prompts)
    _write(os.path.join(DRIFT, f"{date or today()}.json"), prompts)   # dated snapshot: the drift


# ----------------------------------------------------------------- the final work
def write_work(name: str, content) -> str:
    """Write a served artifact (a .mid) under docs/work/. Returns the
    site-relative path ('work/<name>') for donnees.json."""
    path = os.path.join(WORK, name)
    if isinstance(content, (bytes, bytearray)):
        with open(path, "wb") as f:
            f.write(content)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return f"work/{name}"


def work_path(name: str) -> str:
    return os.path.join(WORK, name)


def _write(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
