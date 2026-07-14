# Fadette — Contrôles avant lancement

*Essai du 15 au 31 juillet 2026 · Ouverture le 1er août 2026*

Pré-vol à dérouler avant la naissance de la machine. Le plus court chemin pour la
plupart des points : `python tools/check_feeds.py` (teste endpoint + parsing d'un
coup).

> **La fenêtre de vie de l'ŒUVRE est le 1er–31 août 2026.** Hors fenêtre,
> `conductor.in_window()` refuse de respirer : le cron tourne à vide, rien ne s'écrit,
> rien ne dérive. La fenêtre est donc l'unique commutateur — et c'est elle, et elle seule,
> que `tools/rearm.py` déplace pour l'essai de juillet.

---

## 0. Le calendrier

- [ ] **Dépôt neuf, vierge d'historique.** Verrouiller l'identité git **avant le premier
      commit** (§ 5). Le dépôt est public : le nom du dépôt **est** l'URL.
- [ ] **Acte I — l'essai, du 15 au 31 juillet, sur `main`** : `python tools/rearm.py --test`
      → fenêtre 15–31 juillet, archive vierge, optique à sa graine.
      **Les crons ne tournent que sur la branche par défaut** : l'essai doit donc tourner
      sur `main` — et **Pages reste ÉTEINT**, pour que le lien public ne montre jamais une
      répétition. La page se vérifie en local.
- [ ] **Le 31 juillet à 23h30 UTC, le finale se déclenche** (`today == death`).
      **C'est la seule répétition générale que la nouvelle aura jamais.** La lire.
- [ ] **Acte II — l'ouverture, le 1er août, sur `main`** : si l'essai tient, **on ne change
      rien au code**. `python tools/rearm.py --open` → fenêtre 1–31 août, archive purgée,
      optique neuve. Puis **activer Pages** (`main` / `/docs`).

> **L'essai ne peut PAS éprouver le flot** : il n'y a pas d'éclipse en juillet. Le flot ne
> se prouve que par **rejeu hors ligne** (§ 3), et cette preuve est **obligatoire** avant
> l'ouverture. C'est le seul point que seize jours de vrai ciel laisseront en blanc.

## 1. Préalables — dépôt et secrets

- [ ] Dépôt GitHub **public** (Actions gratuites + Pages auto-hébergées).
- [ ] **GitHub Pages** activé, source = branche `main`, dossier `docs/`.
- [ ] **Secrets** définis : `INFOMANIAK_TOKEN`, `INFOMANIAK_PRODUCT_ID`.
- [ ] `pip install -r requirements.txt` (mido, ephem, PyYAML) sans erreur.

## 2. Captation des données — `python tools/check_feeds.py`

- [ ] **RTE solaire** : `national_mw` revient. (Champ `solaire` en MW, MAJ tous les ¼ h ;
      quota 50 000 appels/mois — la machine en consomme ~750 sur le mois d'août.)
- [ ] **NOAA SWPC** (vent solaire / Kp / X-ray) : les valeurs reviennent.
- [ ] **METAR** : la chaîne LFLD → LFOA → LFLX répond. *Le METAR n'est plus seulement
      capté : il est désormais **lu** — le vent, l'orage, la brume, la chaleur passent
      dans l'œil sous forme de sensations. S'il est muet, la journée perd sa texture.*
- [ ] **Infomaniak** : `swiss-ai/Apertus-70B-Instruct-2509` présent dans la liste des
      modèles (présages et finale l'utilisent) ; une complétion d'un mot répond.
- [ ] **TESS** *(le chantier ouvert)* : sur toute la période écoulée, ce capteur **n'a
      jamais répondu** — chaque souffle a enregistré `want_source: fallback-gift`, c'est-
      à-dire que l'observation au sol était **muette** et que la machine tournait sur la
      géométrie **calculée**. Choisir une station de site sombre sur
      `tess.dashboards.stars4all.eu`, lire l'API réelle (`STARS4ALL/photometer-api`) pour
      le vrai base URL + la route « dernière lecture » + les noms de champs, remplacer
      `feeds.tess_station` dans `config.yaml`, ajuster `sky_brightness` si la route diffère.
      *Non bloquant — le filet calculé couvre l'éclipse — mais la doctrine dit
      « l'observation d'abord ».*
- [ ] **La voie RTE de jour n'a jamais été éprouvée**, faute d'un seul présage diurne
      jusqu'ici. Dès les premiers jours d'août il y en aura : **surveiller `want_source`
      dans le journal.** S'il passe à `observed`, l'œil est vraiment ouvert.

## 3. Sensibilité aux éclipses

- [ ] **Filet calculé** (dans check_feeds) : `want ≈ 0,89` au 12 août 18:15 UTC.
- [ ] **PREUVE OBLIGATOIRE DU FLOT, par rejeu hors ligne.** Il n'y a pas d'éclipse en
      juillet : seize jours d'essai en vrai ciel laisseront ce point — le cœur de l'œuvre —
      entièrement en blanc. Rejouer `sky.state` + `tempo.how_many` au 12 août ~18:00 UTC
      → confirmer le **flot au plafond** (12 présages, contre 2-4 pour toute une journée
      ordinaire). *Sans cette preuve, on n'ouvre pas.*
- [ ] **Le 28 août est marginal, et c'est ainsi.** L'éclipse lunaire tombe à l'aube, lune
      à ~4° au-dessus de l'horizon : depuis le Berry, la machine réagira faiblement, ou
      pas du tout. **Ne pas la forcer.** Elle répond à ce qu'elle voit, non à ce que
      l'almanach promet — un regard qui inonderait sur commande ne serait pas aveugle.
- [ ] **Calibration** : une fois RTE/TESS câblés, confronter les seuils (`×700` du
      solaire, `msas 19–22`, `want_surge 14`, `want_power 2`) aux vraies valeurs.
      **Ne pas toucher `want_surge × want²` sans rejouer le 12 août** : c'est le flot.

## 4. Fonctionnement technique

- [ ] `python -m py_compile src/*.py` → OK.
- [ ] `python -m src.render` → régénère `docs/` sans erreur (état vide avant le 1er août :
      normal, c'est le panneau d'absence).
- [ ] **Bout-en-bout** : un `workflow_dispatch` sur la branche de répétition → un souffle
      réel. Vérifier que sortent un **présage**, un **air**, un **augure**, et que le
      **commit** se fait.

### Les cinq contrôles qui prouvent la réparation

- [ ] **Le `.mid` pèse plus de 36 octets.** 36 octets = un fichier MIDI **vide** (en-tête
      + piste sans une seule note). C'était le symptôme : la partition ne revenait plus.
- [ ] **Le `"score"` du journal n'est pas `[]`.** C'est la même chose, vue depuis l'archive.
- [ ] **L'air se joue dans la page.** Ouvrir `docs/fr.html`, cliquer « entendre l'air » →
      anches + bourdon. *S'il n'y a **aucun lien**, c'est voulu : une partition illisible
      ne donne pas de lien mort.* **Invérifiable hors navigateur — à faire à la main.**
- [ ] **Deux présages consécutifs ne se ressemblent pas.** S'ils se paraphrasent, l'optique
      a pourri : vérifier `history/lens.json` — son champ `text` doit être **une consigne**,
      jamais un présage fini.
- [ ] **Plusieurs présages dans la journée, à des heures différentes.** Un seul, toujours
      vers 20 h UTC, signale que la texture du jour ne remonte pas (METAR muet, ou les
      réglages `tempo` perdus).

## 5. Identité, anonymat, cécité

> **Le dépôt est public, et le nom ne fuit pas par les fichiers — il fuit par les
> commits.** Le workflow force l'identité de la machine à l'intérieur du runner ; il ne
> protège **que les commits de la machine**. Les tiens portent la configuration globale
> de ton poste, qui te nomme. C'est le seul vecteur qui survit à un dépôt neuf.

- [ ] **`python tools/check_identity.py "Prenom Nom" "ton-adresse"` → EXIT 0.**
      Il inspecte tous les fichiers (binaires compris), la configuration git **qui
      signera tes commits**, et **chaque commit de l'historique** (auteur, committeur,
      message). *Lancer avant chaque push.*
      **Ce script ne nomme personne** : il fonctionne par liste blanche, et les chaînes
      interdites se passent en argument, jamais écrites sur le disque. *Une check-list
      qui écrit le secret pour attester qu'il est absent n'est pas un contrôle : elle EST
      la fuite. C'est exactement ce qui s'est produit.*
- [ ] **Identité git LOCALE fixée avant le premier commit** :
      `git config user.name "Marcel Simplexe"` et
      `git config user.email "<ID>+marcel-simplexe@users.noreply.github.com"`
      (adresse *noreply* du compte pseudonyme : elle empêche aussi GitHub de rattacher le
      commit à un autre compte).
- [ ] **`git config commit.gpgsign false`** — sinon la *signature* porte l'identité de la
      clé, même si le texte du commit est propre.
- [ ] **Le dépôt appartient au compte `marcel-simplexe`**, dont le profil public ne porte
      ni nom civil, ni adresse, ni photo identifiante. *Vérifier déconnecté.*
- [ ] **Pied de page** = « Fadette, Présages du Berry · Marcel Simplexe · 2026 » (site
      FR/EN + préversion).
- [ ] Aucune signature de l'outil de génération (nom de l'assistant ou de son éditeur)
      nulle part dans le dépôt.
- [ ] **Cécité** : aucune date ni le mot « eclipse » dans les prompts ; l'éphéméride ne
      livre que la phase. Vérifier que `say_the_sky()` ne laisse passer **aucun** mot
      interdit — ni date, ni mois, ni unité, ni nom savant. Les seuls chiffres livrés à
      l'œil sont **la nuit de la lune** et **le compte de ce qui remue au ciel**.

## 6. Pendant la vie de la machine

- [ ] **1er août** : premier souffle — vérifier le premier commit et le site en ligne.
- [ ] **Chaque semaine** : `want_source` est-il passé à `observed` ? Le journal
      a-t-il des jours vides ? (Un cron sauté ne devrait plus rendre une journée muette.)
- [ ] **12 août** (éclipse solaire) : surveiller le flot vers **18:00–18:30 UTC**. C'est
      la culmination de l'œuvre.
- [ ] **28 août** (éclipse lunaire) : marginale depuis le Berry — **une réaction faible
      n'est pas une panne.**
- [ ] **31 août** : la nouvelle (Apertus) se génère au souffle de 23:30 UTC, puis la
      machine se tait.

---

## Commandes utiles

```bash
# Pré-vol complet (endpoint + parsing + Infomaniak + filet calculé)
python tools/check_feeds.py
INFOMANIAK_TOKEN=... INFOMANIAK_PRODUCT_ID=... python tools/check_feeds.py

# Le rituel : fenêtre, archive vierge, optique à sa graine, pages rendues
python tools/rearm.py --test        # fenêtre = 15-31 juillet (l'essai)
python tools/rearm.py --open        # fenêtre = 1-31 aout  (l'oeuvre)

# Test express des sens (une valeur = ok ; None = cassé)
python3 -c "from src import feeds, conductor as c; k=c.load_config(); [print(n, fn(k)) for n,fn in [('solaire',feeds.grid_solar),('kp',feeds.kp),('xray',feeds.xray),('metar',feeds.metar),('tess',feeds.sky_brightness)]]"

# Ce que l'oeil recoit vraiment (la cecite se verifie a l'oeil nu)
python3 -c "from src import sky, lens, conductor as c; import datetime as dt; k=c.load_config(); print(lens.say_the_sky(sky.state(k, dt.datetime.now(dt.timezone.utc))))"

# Un .mid vide pese 36 octets. Aucun ne doit les faire.
ls -l docs/work/*.mid

# Curl bruts
curl -s "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?order_by=date_heure%20desc&limit=1" | grep -i solaire
curl -s "https://aviationweather.gov/api/data/metar?ids=LFLD&format=raw&hours=2"
curl -s -H "Authorization: Bearer $INFOMANIAK_TOKEN" "https://api.infomaniak.com/2/ai/$INFOMANIAK_PRODUCT_ID/openai/v1/models" | python3 -c "import sys,json; print([m['id'] for m in json.load(sys.stdin)['data']])"
```
