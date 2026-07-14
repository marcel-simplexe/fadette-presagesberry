# Fadette — Operating Manual

The machine sleeps until **1 August 2026**, wakes on its own, lives one month, and
falls silent on the 31st. The public URL never changes: it shows the *absent* sign
now, and the living journal from the first breath of August.

> **The one rule, above all:** never write a **date**, nor the word **eclipse**, into
> a prompt. Fadette is built blind on purpose; the eclipse must enter only as an
> observed anomaly. Section 7 says where every prompt is and how to change it safely.

---

## 0. What you need

- A GitHub account (free).
- An Infomaniak **AI Services** product: a **token** and a **product id**.
- Five minutes in `config.yaml`.

## 1. Put Fadette on GitHub (5 min)

1. Create a repository, e.g. `fadette` (public, so Pages is free).
2. Upload the whole contents of this folder (or `git push` it).
3. Confirm: `config.yaml`, `src/`, `tools/`, `docs/`, `journal/`, `history/`, and
   `.github/workflows/fadette.yml` are present.

> **The repository is public.** Nothing in it — no file, no commit message, no git
> config, no PDF metadata — may carry the author's civil name. Marcel Simplexe is the
> author here, and the only one. Check it before the first push, and remember that
> **git keeps history**: a name removed in a later commit is still readable in the log.

## 2. The two secrets (3 min)

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|---|---|
| `INFOMANIAK_TOKEN` | your Infomaniak AI Services token |
| `INFOMANIAK_PRODUCT_ID` | your AI Services product id |

They are read from the environment; they never appear in the code or the archive.

## 3. Confirm the night station (5 min)

One thing must match your chosen station:

1. **The night station.** In `config.yaml`, set `feeds.tess_station` to a real
   **dark-site** TESS / STARS4ALL station (see the IoT-EELab dashboard at
   `tess.stars4all.eu`), and confirm the per-station reading path in
   `src/feeds.py:sky_brightness`.

> **Known, and open.** In the run so far, this feed **never answered**: every breath
> recorded `want_source: fallback-gift`, meaning ground observation was mute and the
> machine ran on **computed** geometry. The gift covers the eclipse, so nothing is
> lost of the culmination — but the doctrine says *observation first*, and the daytime
> RTE path has **never been exercised**, for want of a single daytime omen. From the
> first days of August there will be daytime omens: **look at `want_source` in the
> journal.** If it ever reads `observed`, the eye is truly open.

The text endpoint needs no change (Infomaniak's standard OpenAI-compatible one). Set the two
model ids to models your product exposes: `infomaniak.text_model` (the daily voice) and
`finale.model` (the nouvelle — Apertus by default, the Swiss sovereign model). Both run on the
same sovereign host; confirm their ids via the models endpoint. Everything else in `config.yaml`
— the Berry, 1–31 August, the schedule — is correct.

## 4. GitHub Pages — but NOT yet

**Settings → Pages** → Source: **Deploy from a branch** → Branch **main**, folder
**/docs**. The URL is `https://<you>.github.io/<repo>/`, and **the repository's name IS
the URL** — so name the repository exactly as the link you have already given out.

> **Leave Pages OFF until the opening.** The trial of 15–31 July runs on `main` (see §5),
> and a public page must never show a rehearsal. Turn Pages on at the reset, on the eve
> of 1 August: the page opens on the *absent* sign, then comes alive on its own. **This
> is the link to send to the biennale**; you never send another.

## 5. The trial, then the opening

The work's window of life is **1–31 August 2026**. But before letting it live, it is run
for real: **a full-scale trial, 15–31 July**.

`conductor.in_window()` refuses to breathe outside its window — the window is therefore
the only switch, and `tools/rearm.py` performs the whole ritual in one command: it sets
the window, purges the archive, brings the lens back to its seed, re-renders the pages.

**ACT I — the trial, 15–31 July, on `main`.**

```bash
python tools/rearm.py --test        # window = 15-31 July, virgin archive, lens at its seed
git add -A && git commit -m "the trial" && git push
```

> **Why on `main`, and why Pages stays OFF.**
> GitHub's scheduled workflows **only ever fire on the default branch**. A test branch
> would get no cron — no heartbeat, hence no trial at all. So the trial must run on
> `main`, and therefore **Pages must stay off until the opening**: the public link must
> never show a rehearsal. The page is checked locally (`docs/fr.html`) — it is a static
> file, so that proves everything.

What the trial proves, and nothing else will:

- **the real cadence**, over sixteen days of true sky — the dawns, the heat, the storms;
- **the drift**, sixteen notches running, with its guard;
- **the DAYTIME observation path (RTE)**, which has **never** been exercised, for want of
  a single daytime omen. Watch `want_source`: if it ever reads `observed`, the eye is open;
- **the finale.** The trial window dies on 31 July: at the 23:30 UTC breath, `today ==
  death` fires the closing nouvelle. **This is the only dress rehearsal `finale.py` will
  ever get.** Do not suppress it — read what it writes.

What the trial **cannot** prove: **the flood**. There is no eclipse in July. The flood is
therefore proven **by replay, offline**, on 12 August at 18:15 UTC — and that proof is
mandatory before the opening (see `CONTROLES-AVANT-LANCEMENT.md`).

After each day, check: a **new** presage (not a paraphrase of the last); a `.mid`
**heavier than 36 bytes** (36 is an empty file); the air **playing in the page**; several
omens across the day, at different hours; and in the journal, a non-empty `"score"`.

**ACT II — the opening, 1 August, on `main`.**

If the trial holds, **nothing in the code changes.** What ran is what opens. Only the
machine is reset, and its true window given back:

```bash
python tools/rearm.py --open        # window = 1-31 August, archive purged, lens at its seed
git add -A && git commit -m "Fadette wakes: 1-31 August 2026" && git push
```

Then **Settings → Pages → `main` / `/docs`**. The page opens on the absent sign, and the
machine speaks for itself at the first breath of August.

## 6. From 1 August it runs itself

No further action. Each breath is a commit; the page updates within a minute or two.

| What | UTC | Paris (summer) |
|---|---|---|
| a breath (the heartbeat) | every 2 h | every 2 h |
| the lens is refined | 23:30 | 01:30 |

Each heartbeat utters as many omens as the sky stirs: none from a still hour, one at
the point of day or the falling evening, more under a storm or a pressing heat, a crowd
when the light fails. An ordinary day speaks two to four times, at different hours. The
cadence is set by `tempo` in `config.yaml`.

The **finale** — one dense nouvelle of about twenty pages, written by Apertus — lands in
the small hours of **1 September** (the 23:30 UTC run of 31 August). Then Fadette falls
silent; the page stays up, the journal closed by the finale.

---

## 7. Acting on the prompts

Every instruction the language model receives lives in **`config.yaml`**, under
`prompts:`. Edit them there — no code to touch.

> **The rule, again:** never write a **date**, nor the word **eclipse**, into any
> prompt. That blindness is the work.

The seven prompts, what each does, and when it fires:

| key in `config.yaml` | what it does | when |
|---|---|---|
| `prompts.system` | the persona — a scribe of the Berry in George Sand's voice. Used by **every** text call; change it to change the voice everywhere. | every call |
| `prompts.presage` | turns the sky into the day's **fragment** (the omen). | every breath |
| `prompts.air` | turns the fragment into a **score** of notes. Keep it asking for a bare JSON list `[{"note":…,"start":…,"duration":…,"force":…}]` — this is a **contract**, not a style. | every breath |
| `prompts.refiner` | the daily **re-prompt** — rewrites `presage` and `air` one notch. Fires only if `lens.drift` is true. | once a day |
| `prompts.finale.matter` | distils the month's omens into the **matter** of a tale. | the last day |
| `prompts.finale.frame` | lays the **frame** of the nouvelle in `finale.movements` titled movements (nine by default). | the last day |
| `prompts.finale.movement` | writes **each movement**, upon the last. Keep `{n}`, `{total}`, `{frame}`, `{written}` — the machine fills them in. | the last day (one call each) |

**The drift is guarded, and you should know how.** `drift.one_notch()` no longer
believes what the model hands back. A refined gaze must still *read as an instruction*
(Sand's voice, the count of sentences, no date, no fenced example); a refined air must
still *demand its JSON score*. A candidate that fails either test is **thrown away** and
the lens keeps its state — you will see it in the run log: *"notch skipped"*. A lens
that has already rotted is **restored to its seed**. This is not timidity: it is the one
guarantee that the machine cannot spend a month paraphrasing a single night.

Two levers that govern *how* the prompts are used, also in `config.yaml`:

- **`lens.drift`** — whether the lens refines itself daily.
  - `true` (default): the machine rewrites `presage` / `air` one notch a day; the
    **live** prompt then lives in `history/lens.json`. To change the live prompt
    mid-run, edit `history/lens.json` (its `text` / `score` fields); to start over from
    your `config.yaml` seeds, run `python tools/rearm.py --open`, or simply delete
    `history/lens.json`.
  - `false`: the machine never refines — **`config.yaml` is authoritative.** Edit
    `prompts.presage` / `prompts.air` and they take effect on the next breath. Use this
    to keep the voice fixed exactly as written.
- **`infomaniak.text_model`** — which model writes the daily text (the presages and the
  airs); **`finale.model`** — which model writes the closing nouvelle (Apertus by default). Not
  prompts, but the other half of the voice.

One more thing you can shape, in **`src/lens.py`**, the function **`say_the_sky`**: it
turns the measured numbers into the bare **sensations** the model is shown — the moon
and her night; the quality of the light (*"the sun touches the earth, and the whole
country turns red"*); the weather as it is felt (*"the wind is rising"*, *"the storm
growls over by the wood"*, *"the heat presses, and the country is thirsty"*); and one
bare figure, *the count of what stirs in the sky*, which the seed prompt orders the eye
to read — and which must therefore be given to it. Editing those phrasings changes *what
the model sees* before it writes: the transcription itself. Same rule: sensations only,
never a date, never an instrument, never "eclipse".

That is the full inventory.

## 8. Good to know

- **The cron is best-effort.** GitHub Actions can start a few minutes late, sometimes
  more under load, and sometimes skips a beat entirely. This is why the day's omens are
  spread over several hours rather than resting on one: a missed beat no longer costs a
  silent day.
- **A push that loses a race loses a breath.** The workflow rebases before pushing, and
  retries once. If a breath is missing from the journal, look at the Actions log first.
- **The served files** (`.mid`) live under `docs/work/` so Pages serves them. Don't
  move them out of `docs/`.
- **An empty `.mid` weighs 36 bytes.** If you ever see one, the score came back
  unreadable — and the page will show **no air link at all**, which is the intended
  behaviour: a link that only downloads a dead file is worse than silence.
- **The archive is the truth.** `journal/` and `history/` hold every breath and every
  state of the lens, dated. The two pages — `index.html` (English, the default landing,
  translated from the French) and `fr.html` (French, the source) — under `docs/` are
  regenerated from it at every breath.

*Marcel Simplexe, 2026.*
