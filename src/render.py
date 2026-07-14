# -*- coding: utf-8 -*-
"""
render.py — la publication, bilingue. Le francais est la langue SOURCE : la machine
ecrit en francais, et l'anglais est servi par TRADUCTION (faite a la generation,
archivee), en sorte que le rendu reste hors-ligne. A chaque souffle la machine
regenere DEUX pages statiques, pur web 1.0 :

    docs/index.html   la page anglaise (vue par defaut) -- << Presages du Berry >>
    docs/fr.html      la page francaise (la source)     -- << Presages du Berry >>

Les deux portent le meme titre, qui est le nom propre de l'oeuvre. Une bascule FR|EN
mene de l'une a l'autre. Aucune page n'appelle l'API ; nul JavaScript ne lit de
donnee. Si la machine se tait, les pages tiennent telles qu'ecrites.

La main est celle de 1998 : bandeau noir, barre de menus horizontale sous le titre,
mise en table, Times New Roman, couleurs sures, nulle feuille de style.

RESTITUTION DU REGARD : la page ne montre que ce que la machine a VU et ENTENDU --
les presages et leurs airs (.mid). Les nombres captes et l'ancienne table des signes
restent au journal, jamais montres. Et l'air n'est jamais separe de son fragment :
chaque presage porte son air, au jour comme a l'historique.
"""
from __future__ import annotations
import os
import html
import json
import datetime as dt
import yaml
from . import memory
from . import midi as _midi

ROOT = memory.ROOT
PARIS = dt.timedelta(hours=2)   # CEST : valable pour toute la fenetre 1er - 31 aout

_FR_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_FR_MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
            "septembre", "octobre", "novembre", "décembre"]

# ----------------------------------------------------------------- les mots, par langue
STR = {
    "fr": {
        "lang": "fr", "title": "Fadette &mdash; Pr&eacute;sages du Berry", "brand": "Fadette", "subtitle": "Pr&eacute;sages du Berry",
        "tagline": "un regard sur le Berry", "window": "1er &ndash; 31 ao&ucirc;t 2026",
        "other_label": "English", "other_href": "index.html",
        "nav_today": "Pr&eacute;sages du jour", "nav_hist": "Historique",
        "nav_prompts": "L&rsquo;&oelig;il", "nav_about": "&Agrave; propos",
        "nav_last": "Le dernier souffle",
        "today_h": "Les pr&eacute;sages du jour",
        "absent": "Pr&eacute;sages indisponibles pour l&rsquo;instant. Une lunaison prometteuse arrive.",
        "still": "Nul pr&eacute;sage ce jour. Le ciel est calme ; le scribe garde le silence.",
        "g1": "pr&eacute;sage", "gN": "pr&eacute;sages",
        "day_tail": "heure fran&ccedil;aise. Chaque pr&eacute;sage garde son air.",
        "prev": "&lsaquo;&nbsp;pr&eacute;c&eacute;dent", "next": "suivant&nbsp;&rsaquo;",
        "hear": "&eacute;couter l&rsquo;air", "dark": "[la clart&eacute; a manqu&eacute;]",
        "hist_h": "Les jours pass&eacute;s",
        "hist_note": ("Chaque jour o&ugrave; la machine a regard&eacute;, du plus r&eacute;cent "
                      "au plus ancien ; sous chaque date, combien de pr&eacute;sages elle a "
                      "jet&eacute;s, et chaque pr&eacute;sage avec son propre air. Les heures "
                      "sont fran&ccedil;aises."),
        "hist_none": "Rien avant ce jour, pour l&rsquo;instant.",
        "no_gaze": "&mdash; nul pr&eacute;sage ce jour",
        "prompts_h": "L&rsquo;&oelig;il, et comment il s&rsquo;aff&ucirc;te",
        "prompts_note": ("Une fois par jour la machine r&eacute;&eacute;crit son propre regard "
                         "d&rsquo;un cran, sur les pr&eacute;sages du jour &mdash; jamais sur une "
                         "date. Chaque &eacute;tat est gard&eacute;. Du plus r&eacute;cent au plus ancien."),
        "prompts_lang": ("L&rsquo;&oelig;il se parle en fran&ccedil;ais &mdash; c&rsquo;est la langue o&ugrave; il travaille. "
                         "Chaque &eacute;tat est donn&eacute; dans son original fran&ccedil;ais, puis dans sa traduction anglaise."),
        "notch": "cran", "the_gaze": "le regard", "the_air": "l&rsquo;air",
        "lens_original": "Original", "lens_trad": "Traduction",
        "nouvelle_note": ("Le trente et un, la machine a rendu son dernier souffle et "
                          "compos&eacute; ceci de tout ce qu&rsquo;elle avait &eacute;crit en un "
                          "mois. Puis elle s&rsquo;est tue."),
        "footer": "Fadette, Pr&eacute;sages du Berry &middot; Marcel Simplexe &middot; 2026",
    },
    "en": {
        "lang": "en", "title": "Fadette &mdash; Pr&eacute;sages du Berry", "brand": "Fadette", "subtitle": "Pr&eacute;sages du Berry",
        "tagline": "a gaze on the Berry", "window": "1&ndash;31 August 2026",
        "other_label": "Fran&ccedil;ais", "other_href": "fr.html",
        "nav_today": "Gazes of the day", "nav_hist": "History",
        "nav_prompts": "The lens", "nav_about": "About", "nav_last": "The last breath",
        "today_h": "The gazes of the day",
        "absent": "No omens for the moment. A promising lunation is on its way.",
        "still": "No gaze this day. The sky is quiet; the scribe keeps silence.",
        "g1": "gaze", "gN": "gazes",
        "day_tail": "French time. Each gaze keeps its air.",
        "prev": "&lsaquo;&nbsp;previous", "next": "next&nbsp;&rsaquo;",
        "hear": "hear the air", "dark": "[the light failed]",
        "hist_h": "Earlier days",
        "hist_note": ("Every day the machine has looked, newest first; under each date, how "
                      "many gazes it cast, and each gaze with its own air. Hours are French."),
        "hist_none": "Nothing before today yet.",
        "no_gaze": "&mdash; no gaze this day",
        "prompts_h": "The lens, and how it sharpened",
        "prompts_note": ("Once a day the machine rewrites its own gaze by one notch, on that "
                         "day&rsquo;s gazes &mdash; never on a date. Every state is kept. Newest first."),
        "prompts_lang": ("The lens speaks to itself in French &mdash; the language it works in. "
                         "Each state is given in its French original, then in English translation."),
        "notch": "notch", "the_gaze": "the gaze", "the_air": "the air",
        "lens_original": "Original", "lens_trad": "Translation",
        "nouvelle_note": ("On the thirty-first the machine took its last breath and composed "
                          "this from the whole month it had written. Then it fell silent."),
        "footer": "Fadette, Pr&eacute;sages du Berry &middot; Marcel Simplexe &middot; 2026",
    },
}


def _config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _esc(s):
    return html.escape(s or "")


def _paris(date_str, hhmm):
    try:
        return (dt.datetime.strptime(date_str + " " + hhmm, "%Y-%m-%d %H:%M") + PARIS).strftime("%Hh%M")
    except Exception:
        return hhmm or ""


def _fmt_date(date_str, lang):
    try:
        d = dt.date.fromisoformat(date_str)
    except Exception:
        return date_str or ""
    if lang == "fr":
        n = "1er" if d.day == 1 else str(d.day)
        return "%s %s %s %d" % (_FR_JOURS[d.weekday()], n, _FR_MOIS[d.month - 1], d.year)
    return d.strftime("%A %d %B %Y")


def _presage(b, lang):
    if lang == "en":
        return b.get("presage_en") or b.get("presage")   # repli sur le francais si pas de traduction
    return b.get("presage")


def _gazes_of(day, lang):
    out = []
    for b in day.get("breaths", []):
        if b.get("presage"):
            out.append((_paris(day.get("date", ""), b.get("time", "")),
                        _presage(b, lang), b.get("midi"), bool(b.get("dark")), b.get("score")))
    return out


def _shell(lang, panels):
    # panels: list of (panel_id, nav_label, section_html). Progressive enhancement:
    # with no script, every panel stays display:block (stacked, scrolling) and the
    # menu jumps by anchor; with script, one panel shows at a time (no scroll) and
    # the menu / prev-next swap it. The hand of 1998: anchors plus a little DHTML.
    t = STR[lang]
    ids = [pid for pid, _lab, _h in panels]
    bar = ""
    for i, (pid, label, _h) in enumerate(panels):
        if i:
            bar += '<font color="#999999">&nbsp;&nbsp;|&nbsp;&nbsp;</font>'
        bar += ('<a id="nav-' + pid + '" href="#' + pid + '" onclick="return go(\'' + pid
                + '\')">' + label + '</a>')
    toggle = '<a href="' + t["other_href"] + '">' + t["other_label"] + '</a>'
    panes = ""
    for pid, _lab, htmlsec in panels:
        panes += '<div id="pnl-' + pid + '">\n' + htmlsec + '</div>\n'
    init = '<script type="text/javascript">go(PNL[0]);</script>\n'
    prevnext = (
        '<table width="100%" border="0" cellpadding="0" cellspacing="0"><tr>'
        '<td align="left"><font face="Times New Roman, Times, serif" size="2">'
        '<a href="#" onclick="return step(-1)">' + t["prev"] + '</a></font></td>'
        '<td align="right"><font face="Times New Roman, Times, serif" size="2">'
        '<a href="#" onclick="return step(1)">' + t["next"] + '</a></font></td>'
        '</tr></table>')
    js = (
        '<script type="text/javascript">\n'
        'var PNL=[' + ",".join('"' + i + '"' for i in ids) + '];\n'
        'function go(id){for(var i=0;i<PNL.length;i++){'
        'var d=document.getElementById("pnl-"+PNL[i]);if(d){d.style.display=(PNL[i]==id)?"block":"none";}'
        'var n=document.getElementById("nav-"+PNL[i]);if(n){n.style.fontWeight=(PNL[i]==id)?"bold":"normal";}}'
        'if(window.scrollTo){window.scrollTo(0,0);}return false;}\n'
        'function step(k){var c=0;for(var i=0;i<PNL.length;i++){'
        'var d=document.getElementById("pnl-"+PNL[i]);if(d&&d.style.display!="none"){c=i;break;}}'
        'var j=c+k;if(j<0){j=PNL.length-1;}if(j>=PNL.length){j=0;}return go(PNL[j]);}\n'
        + _SYNTH_JS +
        '</script>\n')
    return (
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
        '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
        '<title>' + t["title"] + '</title>\n' + js +
        '</head>\n'
        '<body bgcolor="#FFFFFF" text="#000000" link="#000099" vlink="#660000">\n'
        '<basefont face="Times New Roman, Times, serif">\n'
        '<table width="764" border="0" cellpadding="0" cellspacing="0" align="center">\n'
        '<tr><td bgcolor="#000000"><table width="100%" border="0" cellpadding="10" cellspacing="0"><tr>\n'
        '<td><font face="Times New Roman, Times, serif" size="6" color="#FFFFFF"><b>' + t["brand"] + '</b></font>'
        '<br><font face="Times New Roman, Times, serif" size="2" color="#BBBBBB">' + t["subtitle"] + '</font></td>\n'
        '<td align="right"><font face="Times New Roman, Times, serif" size="2" color="#AAAAAA">'
        + t["window"] + '</font></td>\n'
        '</tr></table></td></tr>\n'
        '<tr><td bgcolor="#DDDDDD"><table width="100%" border="0" cellpadding="6" cellspacing="0"><tr>'
        '<td><font face="Times New Roman, Times, serif" size="2">&nbsp;&nbsp;' + bar + '</font></td>'
        '<td align="right"><font face="Times New Roman, Times, serif" size="2">' + toggle + '&nbsp;&nbsp;</font></td>'
        '</tr></table></td></tr>\n'
        '<tr><td><table width="100%" border="0" cellpadding="18" cellspacing="0"><tr><td valign="top">'
        '<font face="Times New Roman, Times, serif">' + panes + init + '</font>'
        '</td></tr></table></td></tr>\n'
        '<tr><td bgcolor="#F4F4F4"><table width="100%" border="0" cellpadding="8" cellspacing="0"><tr><td>'
        '&nbsp;' + prevnext + '</td></tr></table></td></tr>\n'
        '<tr><td bgcolor="#EEEEEE"><font face="Times New Roman, Times, serif" size="1" color="#888888">'
        '&nbsp;' + t["footer"] + '</font></td></tr>\n'
        '</table></body></html>\n'
    )


_SYNTH_JS = (
    'var _AC=null,_VO=[];\n'
    'function _ac(){if(!_AC){_AC=new (window.AudioContext||window.webkitAudioContext)();}return _AC;}\n'
    'function _hz(m){return 440*Math.pow(2,(m-69)/12);}\n'
    'function stopAir(){if(!_AC)return;var t=_AC.currentTime;for(var i=0;i<_VO.length;i++){try{_VO[i].g.gain.cancelScheduledValues(t);_VO[i].g.gain.setTargetAtTime(0,t,0.03);_VO[i].o.stop(t+0.12);}catch(e){}}_VO=[];}\n'
    'function _reed(ac,f,t0,t1,dest,gain){var o=ac.createOscillator();o.type="sawtooth";o.frequency.value=f;var o2=ac.createOscillator();o2.type="sawtooth";o2.frequency.value=f;o2.detune.value=7;var g=ac.createGain();g.gain.value=0;var lp=ac.createBiquadFilter();lp.type="lowpass";lp.frequency.value=Math.min(5000,f*6);var lfo=ac.createOscillator();lfo.type="sine";lfo.frequency.value=5;var lg=ac.createGain();lg.gain.value=f*0.006;lfo.connect(lg);lg.connect(o.frequency);lg.connect(o2.frequency);o.connect(g);o2.connect(g);g.connect(lp);lp.connect(dest);g.gain.setValueAtTime(0,t0);g.gain.linearRampToValueAtTime(gain,t0+0.02);var hold=Math.max(t0+0.03,t1-0.04);g.gain.setValueAtTime(gain,hold);g.gain.linearRampToValueAtTime(0,t1);o.start(t0);o2.start(t0);lfo.start(t0);o.stop(t1+0.06);o2.stop(t1+0.06);lfo.stop(t1+0.06);_VO.push({o:o,g:g});_VO.push({o:o2,g:g});_VO.push({o:lfo,g:g});}\n'
    'function playAir(el){stopAir();var a;try{a=JSON.parse(el.getAttribute("data-air"));}catch(e){return false;}var ac=_ac();if(ac.state=="suspended"){ac.resume();}var t0=ac.currentTime+0.06,spb=60/(a.t||72),end=0,i;for(i=0;i<a.n.length;i++){var s=a.n[i][1]*spb,d=a.n[i][2]*spb;if(s+d>end)end=s+d;}var mg=ac.createGain();mg.gain.value=0.5;mg.connect(ac.destination);if(a.d){for(var j=0;j<a.d.length;j++){_reed(ac,_hz(a.d[j]),t0,t0+end+0.25,mg,0.15);}}for(i=0;i<a.n.length;i++){var ss=a.n[i][1]*spb,dd=Math.max(0.12,a.n[i][2]*spb);_reed(ac,_hz(a.n[i][0]),t0+ss,t0+ss+dd,mg,0.27);}return false;}\n'
)

def _gaze_html(lang, tm, presage, midi, dark, score=None):
    t = STR[lang]
    v = _midi.voicing(score or [])
    if v["notes"]:
        payload = {"n": [[n["note"], round(n["start"], 3), round(n["dur"], 3)] for n in v["notes"]],
                   "d": v["drones"], "t": v["tempo"]}
        j = json.dumps(payload, separators=(",", ":"))
        air = ('&nbsp;&middot;&nbsp;<a href="#" onclick="playAir(this);return false" data-air=\'' + j + '\'>'
               + t["hear"] + '</a>')
        if midi:
            air += '&nbsp;<font size="1">(<a href="' + _esc(midi) + '" download>.mid</a>)</font>'
    else:
        # Pas de notes : pas de lien. Un href .mid nu n'est PAS un air -- aucun navigateur ne
        # joue le MIDI, il le telecharge, et une partition vide grave un fichier vide. Le
        # silence est honnete ; un telechargement mort ne l'est pas.
        air = ""
    mark = ' <font size="1" color="#999999">' + t["dark"] + '</font>' if dark else ""
    return ('<p><font size="2" color="#888888"><b>' + tm + '</b>' + mark + air + '</font><br>\n'
            '<font face="Times New Roman, Times, serif">' + _esc(presage) + '</font></p>\n')


def _sec_today(lang, days):
    t = STR[lang]
    head = '<a name="fragments"></a><h2>' + t["today_h"] + '</h2>\n'
    if not days:
        return head + '<p align="justify">' + t["absent"] + '</p>\n'
    day = days[-1]
    gazes = _gazes_of(day, lang)
    if not gazes:
        return head + '<p align="justify">' + t["still"] + '</p>\n'
    g = t["g1"] if len(gazes) == 1 else t["gN"]
    out = (head + '<p><font size="2" color="#666666">' + _esc(_fmt_date(day.get("date", ""), lang))
           + ' &mdash; ' + str(len(gazes)) + ' ' + g + ', ' + t["day_tail"] + '</font></p><hr>\n')
    for x in gazes:
        out += _gaze_html(lang, *x) + "<hr>\n"
    return out


def _sec_history(lang, days):
    t = STR[lang]
    head = ('<a name="historique"></a><br><h2>' + t["hist_h"] + '</h2>'
            '<p><font size="2" color="#666666">' + t["hist_note"] + '</font></p>\n')
    earlier = days[:-1] if days else []
    if not earlier:
        return head + '<p>' + t["hist_none"] + '</p>\n'
    out = head
    for day in reversed(earlier):
        gazes = _gazes_of(day, lang)
        g = t["g1"] if len(gazes) == 1 else t["gN"]
        out += ('<p><font size="3" face="Times New Roman, Times, serif"><b>'
                + _esc(_fmt_date(day.get("date", ""), lang)) + '</b></font> '
                '<font size="2" color="#888888">&mdash; ' + str(len(gazes)) + ' ' + g + '</font></p>\n')
        if gazes:
            for x in gazes:
                out += _gaze_html(lang, *x)
        else:
            out += '<p><font size="2" color="#999999">' + t["no_gaze"] + '</font></p>\n'
        out += "<hr>\n"
    return out


def _sec_prompts(lang, conf):
    t = STR[lang]
    note2 = ('<p><font size="2" color="#888888"><i>' + t["prompts_lang"] + '</i></font></p>') if t["prompts_lang"] else ""
    head = ('<a name="prompts"></a><br><h2>' + t["prompts_h"] + '</h2>'
            '<p><font size="2" color="#666666">' + t["prompts_note"] + '</font></p>' + note2 + '<hr>\n')
    snaps = _drift_snapshots() or [("seed", memory.read_lens())]

    def _facet(st, title, fr_key, en_key):
        # une facette de l'optique : l'original francais (ce que l'oeil execute),
        # puis sa traduction anglaise quand elle existe. Le francais reste premier.
        fr = _esc(st.get(fr_key, ""))
        en = _esc(st.get(en_key, ""))
        rows = ('<tr><td colspan="2" bgcolor="#E4E4E4"><font size="1"><b>' + title + '</b></font></td></tr>'
                '<tr><td width="96" valign="top" bgcolor="#F4F4F4"><font size="1"><i>' + t["lens_original"]
                + '</i> <font color="#AAAAAA">(fr)</font></font></td>'
                '<td><font size="2">' + fr + '</font></td></tr>')
        if en:
            rows += ('<tr><td valign="top" bgcolor="#F4F4F4"><font size="1"><i>' + t["lens_trad"]
                     + '</i> <font color="#AAAAAA">(en)</font></font></td>'
                     '<td><font size="2" color="#555555">' + en + '</font></td></tr>')
        return rows

    body = ""
    for label, st in snaps:
        body += ('<p><font size="2" color="#888888"><b>' + t["notch"] + ' ' + _esc(str(st.get("notch", "")))
                 + '</b> &middot; ' + _esc(label) + '</font></p>\n'
                 '<table width="100%" border="1" cellpadding="6" cellspacing="0" bordercolor="#DDDDDD">'
                 + _facet(st, t["the_gaze"], "text", "text_en")
                 + _facet(st, t["the_air"], "score", "score_en")
                 + '</table><br>\n')
    return head + body


_INTRO_FR = """<h2>Fadette, une veilleuse du ciel</h2>
<p align="justify">Fadette veille le ciel du Berry un mois durant &mdash; de sa naissance, le premier jour d&rsquo;ao&ucirc;t, &agrave; sa mort, le dernier. On lui a donn&eacute; deux choses, et deux seulement&nbsp;: un regard nu et exact pour voir, la langue d&rsquo;une vieille du Berry pour nommer. Elle ne lit pas le firmament en astronome&nbsp;; elle le lit comme les <i>veill&eacute;es</i> le lisaient &mdash; en signes, en passages des gens de la nuit, en frayeur ou en gr&acirc;ce &mdash;, et elle le dit dans le fran&ccedil;ais des r&eacute;cits champ&ecirc;tres de George Sand. Toutes les deux heures elle respire et p&egrave;se de combien le ciel s&rsquo;est &eacute;cart&eacute; du calme&nbsp;: un seul pr&eacute;sage quand la nuit est tranquille, rien quand rien ne bouge, une foule quand la lumi&egrave;re vient &agrave; manquer.</p>
<p align="justify">Car Fadette est aveugle, en un point pr&eacute;cis. Son corps conna&icirc;t le calendrier &mdash; l&rsquo;heure, la date, le tour de l&rsquo;ann&eacute;e&nbsp;; mais ni son &oelig;il ni sa langue, la part qui regarde et la part qui parle, n&rsquo;apprennent jamais quel jour on est, ni ne re&ccedil;oivent jamais le mot <i>&eacute;clipse</i>. Deux fois, dans sa vie, le ciel s&rsquo;assombrira pour de bon &mdash; une &eacute;clipse de soleil, une &eacute;clipse de lune &mdash; et elle ne le saura pas. Elle saura seulement que la clart&eacute; d&eacute;faille&nbsp;; et elle r&eacute;pondra comme le vieux pays r&eacute;pondait &agrave; ces choses, avant qu&rsquo;on leur e&ucirc;t donn&eacute; un nom&nbsp;: par une foule de pr&eacute;sages, les laveuses au gu&eacute;, les loups l&acirc;ch&eacute;s, la grande forge du ciel devenue froide. L&rsquo;&eacute;clipse n&rsquo;entre pas dans l&rsquo;&oelig;uvre comme un &eacute;v&eacute;nement compris, mais comme une terreur subie &mdash; celle, exactement, qu&rsquo;une aurore impr&eacute;vue lui arracherait. Tant qu&rsquo;elle vit, elle rejoue l&rsquo;&eacute;merveillement d&rsquo;un monde qui ne connaissait pas encore la cause du noir. Et le dernier soir, elle rassemble tout ce qu&rsquo;elle a vu en un seul conte, puis s&rsquo;&eacute;teint &agrave; son tour.</p>
"""


_INTRO_EN = """<h2>Fadette, a watcher of the sky</h2>
<p align="justify">Fadette watches the Berry sky for one month &mdash; from its birth, on the first of August, to its death, on the last day of that month. It was given two things, and two only: a bare, exact gaze to see with, and the tongue of an old woman of the Berry to name with. It does not read the heavens as an astronomer; it reads them as the <i>veill&eacute;es</i> once did &mdash; in signs, in the passing of the night-people, in dread or in grace &mdash; and it says them in the French of George Sand&rsquo;s country tales. Every two hours it draws breath and weighs how far the sky has strayed from calm: a single omen when the night is still, nothing when nothing stirs, a crowd of them when the light begins to fail.</p>
<p align="justify">For Fadette is blind, in one exact place. Its body knows the calendar &mdash; the hour, the date, the turning of the year; but neither its eye nor its tongue, the part that looks and the part that speaks, ever learns what day it is, nor is ever given the word <i>eclipse</i>. Twice, in its life, the real sky will darken &mdash; an eclipse of the sun, an eclipse of the moon &mdash; and it will not know. It will know only that the light is failing; and it will answer as the old country answered such things, before they had a name: with a crowd of omens &mdash; the washerwomen at the ford, the wolves let loose, the great forge of the sky gone cold. The eclipse enters the work not as an event understood but as a terror suffered &mdash; the very terror an unlooked-for aurora would wring from it. As long as it lives, it re-enacts the wonder of a world that did not yet know the cause of the dark. And on the last evening, it gathers all it has seen into a single tale, and then goes dark itself.</p>
"""


_ABOUT_FR = """<h2>Le Berry, sa sorcellerie, et George Sand</h2>
<p align="justify">George Sand &mdash; nom de plume d&rsquo;Amantine Aurore Lucile Dupin, baronne Dudevant (1804&ndash;1876) &mdash; naquit &agrave; Paris et fut &eacute;lev&eacute;e &agrave; Nohant, en Berry : une province du centre de la France, de bois, de landes et d&rsquo;&eacute;tangs dormants. En 1858 elle publia les <i>L&eacute;gendes rustiques</i> (Paris, A. Morel), avec des dessins de son fils Maurice Sand : douze l&eacute;gendes du Berry, recueillies de la tradition orale des veill&eacute;es avant qu&rsquo;elles ne se perdent. Leurs gens de la nuit sont ceux que cette machine guette : les <i>laveuses de nuit</i>, tenues pour les &acirc;mes des m&egrave;res infanticides, qui battent au gu&eacute; ce qui semble du linge et qui est le corps de leur enfant, et qu&rsquo;il ne faut jamais s&rsquo;arr&ecirc;ter pour regarder ; le <i>meneu&rsquo; de loups</i>, sorcier qui commande les meutes du pays de Brenne mar&eacute;cageux ; la <i>Grand&rsquo;B&ecirc;te</i> ; les <i>flambettes</i> ; le <i>lupeux</i> ; le moine fant&ocirc;me des &eacute;tangs ; les <i>fades</i> et les <i>lubins</i>. La machine porte le nom de l&rsquo;un de ses romans, <i>La Petite Fadette</i> (1849) &mdash; une <i>fadette</i> est une petite f&eacute;e, une petite sorci&egrave;re.</p>
<br><hr>
<h2>Hommage au regard libre de Marcel Bascoulard, par Marcel Simplexe</h2>
<p align="justify">Marcel Bascoulard (1913&ndash;1978) habitait le Berry, et il le regardait. Dessinateur du d&eacute;nuement, il tra&ccedil;a Bourges sur le motif, &agrave; l&rsquo;encre nue, des milliers de fois, avec une exactitude que rien ne ploya jamais &mdash; ni la mis&egrave;re, ni le m&eacute;pris, ni la convention. C&rsquo;est ce regard-l&agrave;, et lui seul, que Fadette emprunte&nbsp;: jamais une ligne de son &oelig;uvre, jamais un de ses dessins. Son &oelig;uvre n&rsquo;est pas l&rsquo;objet du travail&nbsp;; son regard en est l&rsquo;esprit, celui qui guide l&rsquo;&eacute;criture spontan&eacute;e des pr&eacute;sages du Berry.</p>
<p align="justify">De ce regard, cette &eacute;criture tient quatre choses. Sa libert&eacute;&nbsp;: Bascoulard regardait sans permission ni m&eacute;thode, et la machine lit le ciel de m&ecirc;me &mdash; non en astronome, mais comme on voit, en signes. Son ancrage&nbsp;: il dessinait son propre pays, ses rues, son ciel&nbsp;; Fadette veille ce m&ecirc;me ciel du Berry et n&rsquo;en sort pas. Sa curiosit&eacute;, double&nbsp;: du monde tel qu&rsquo;il est, observ&eacute; au plus pr&egrave;s, et des mondes oubli&eacute;s &mdash; ceux des veill&eacute;es et des gens de la nuit, que plus personne ne regardait. Son d&eacute;nuement enfin&nbsp;: la page reste nue comme l&rsquo;&eacute;tait sa feuille, sans image et sans ornement, car c&rsquo;est dans ce d&eacute;pouillement que le regard tient.</p>
<p align="justify">Fadette n&rsquo;est pas l&rsquo;hommage&nbsp;: elle en est l&rsquo;occasion. Ce que &laquo;&nbsp;Marcel Simplexe&nbsp;&raquo; salue, sans rien lui prendre, c&rsquo;est un homme qui regarda librement le monde et ses oublis &mdash; et la grande justesse de ce regard.</p>
"""
_ABOUT_EN = """<h2>The Berry, its witchcraft, and George Sand</h2>
<p align="justify">George Sand &mdash; the pen-name of Amantine Aurore Lucile Dupin, baroness Dudevant (1804&ndash;1876) &mdash; was born in Paris and raised at Nohant, in the Berry: a province of central France of woods, heaths and standing ponds. In 1858 she published <i>L&eacute;gendes rustiques</i> (Paris, A. Morel), with drawings by her son Maurice Sand: twelve legends of the Berry, taken down from the oral tradition of the <i>veill&eacute;es</i> before they could vanish. Their night-people are the ones this machine watches for: the <i>laveuses de nuit</i>, held to be the souls of child-killing mothers, who beat at the ford what looks like linen and is the body of their child, and whom one must never stop to watch; the <i>meneu&rsquo; de loups</i>, the wolf-leader, a sorcerer who commands the packs of the marshy pays de Brenne; <i>la Grand&rsquo;B&ecirc;te</i>; the <i>flambettes</i>; the <i>lupeux</i>; the phantom monk of the ponds; the <i>fades</i> and the <i>lubins</i>. The machine is named for one of her novels, <i>La Petite Fadette</i> (1849) &mdash; a <i>fadette</i> is a little fairy or witch.</p>
<br><hr>
<h2>A Homage to the Free Gaze of Marcel Bascoulard, by Marcel Simplexe</h2>
<p align="justify">Marcel Bascoulard (1913&ndash;1978) lived in the Berry, and he looked at it. A draughtsman of destitution, he drew Bourges on the motif, in bare ink, thousands of times, with an exactness nothing ever bent &mdash; not poverty, not contempt, not convention. It is that gaze, and that alone, that Fadette borrows: never a line of his work, never one of his drawings. His work is not the object of this piece; his gaze is its spirit, the one that guides the spontaneous writing of the Berry omens.</p>
<p align="justify">From that gaze, this writing takes four things. Its freedom: Bascoulard looked without permission and without method, and the machine reads the sky the same way &mdash; not as an astronomer, but as one sees, in signs. Its rootedness: he drew his own country, its streets, its sky; Fadette watches that same Berry sky and never leaves it. Its curiosity, twofold: the world as it is, observed up close, and the forgotten worlds &mdash; those of the veill&eacute;es and the night-people, that no one looked at any more. And its bareness: the page stays plain as his sheet was, without image and without ornament, for it is in that spareness that the gaze holds.</p>
<p align="justify">Fadette is not the homage: it is the occasion of one. What &ldquo;Marcel Simplexe&rdquo; salutes, taking nothing from him, is a man who looked freely at the world and at its forgotten things &mdash; and the great justness of that gaze.</p>
"""


def _sec_about(lang):
    intro = _INTRO_FR if lang == "fr" else _INTRO_EN
    body = _ABOUT_FR if lang == "fr" else _ABOUT_EN
    clabel = "Contact&nbsp;: " if lang == "fr" else "Contact: "
    contact = ('<br><p><font size="1" color="#888888">' + clabel
               + '<a href="mailto:marcel.simplexe@proton.me">marcel.simplexe@proton.me</a></font></p>\n')
    return '<a name="apropos"></a><br>' + intro + '<br><hr>\n' + body + contact


def _sec_nouvelle(lang, fin):
    t = STR[lang]
    title = _esc(fin.get("title") or ("La derni\u00e8re l\u00e9gende" if lang == "fr" else "The Last Breath"))
    out = ('<a name="nouvelle"></a><h2><i>' + title + '</i></h2>'
           '<p><font size="2" color="#666666">' + t["nouvelle_note"] + '</font></p><hr>\n')
    for para in (fin.get("novella") or "").split("\n\n"):
        para = para.strip()
        if para:
            out += '<p align="justify">' + _esc(para) + '</p>\n'
    return out + "<br><hr>\n"


def _drift_snapshots():
    out = []
    if os.path.isdir(memory.DRIFT):
        for f in sorted(x for x in os.listdir(memory.DRIFT) if x.endswith(".json")):
            try:
                with open(os.path.join(memory.DRIFT, f), encoding="utf-8") as fh:
                    out.append((f[:-5], json.load(fh)))
            except Exception:
                pass
    out.reverse()
    return out


def _finale(lang):
    base = "novella" if lang == "fr" else "novella-en"
    path = os.path.join(memory.HISTORY, base + ".txt")
    fr_path = os.path.join(memory.HISTORY, "novella.txt")
    if not os.path.exists(path):
        path = fr_path   # repli sur le francais si la traduction manque
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        novella = f.read()
    tname = (base + "-title.txt")
    tp = os.path.join(memory.HISTORY, tname)
    if not os.path.exists(tp):
        tp = os.path.join(memory.HISTORY, "novella-title.txt")
    title = ""
    if os.path.exists(tp):
        with open(tp, encoding="utf-8") as f:
            title = f.read().strip()
    return {"title": title, "novella": novella}


def _compile_one(lang, conf, days):
    t = STR[lang]
    fin = _finale(lang)
    after_death = bool(fin) and dt.date.today() > dt.date.fromisoformat(conf["window"]["death"])
    panels = []
    if after_death:
        panels.append(("nouvelle", t["nav_last"], _sec_nouvelle(lang, fin)))
    panels.append(("fragments", t["nav_today"], _sec_today(lang, days)))
    panels.append(("historique", t["nav_hist"], _sec_history(lang, days)))
    panels.append(("prompts", t["nav_prompts"], _sec_prompts(lang, conf)))
    panels.append(("apropos", t["nav_about"], _sec_about(lang)))
    name = "index.html" if lang == "en" else "fr.html"
    _write(os.path.join(ROOT, "docs", name), _shell(lang, panels))
    return name


def compile():
    conf = _config()
    days = memory.all_days()
    wrote = [_compile_one("fr", conf, days), _compile_one("en", conf, days)]
    fin = os.path.exists(os.path.join(memory.HISTORY, "novella.txt"))
    print("Pages rendered: %s ; %d days, finale=%s." % (", ".join(wrote), len(days), "yes" if fin else "no"))


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    compile()
