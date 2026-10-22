# verktoy/ikea – monteringsrettleiing i IKEA-stil frå 3D-delar

`bygg.py` lagar ei monteringsrettleiing (PDF, side-PNG, kontaktark og rapport) frå ei JSON-spesifikasjon og delane som STL, GLB eller enkle primitiv. Stilen følgjer referansesidene i [`referansar/ikea-monteringsstil/`](../../referansar/ikea-monteringsstil):

- svart strek på kvitt, med sideramme og sidetal
- nummer i sirkel med mengd (①x1) og bokstavar for beslag (A x8)
- eksplodert oversikt med nummer på kvar del
- stegsider med beslagkolonne til høgre, stipla innstikksliner med «Ax4», piler for større delar, hole piler (⇨) mellom delsteg, forstørringsbobler, store multiplikatorar (x2), åtvaringar og ikon

```bash
npm install --prefix verktoy                  # three.js; Playwright/Chromium må finnast
python3 verktoy/ikea/bygg.py verktoy/ikea/eksempel/entropi-a3.json [utmappe]
```

Utdata: `rettleiing.pdf`, `sider/side-NN.png`, `kontaktark.png` og `rapport.json`. Rapporten har sjekksum, figurinfo og `åtvaringar`: avvik mellom beslag brukte i stega og mengda i dellista, steg utan ny del, tomme figurar og tekst som overlappar figurar eller annan tekst. Sjå alltid gjennom kontaktarket før levering. Figurane blir cacha under `utmappe/_arbeid/` og blir berre rendra på nytt når scena eller ei fil endrar seg.

## Spesifikasjon

Alle stiar er relative til spesifikasjonsfila. Alle delar må liggje i same monteringsramme (mm), slik at `at` og `explode` er forskyvingar i den ramma. Sjå [`eksempel/entropi-a3.json`](eksempel/entropi-a3.json).

```json
{
  "meta": {"title": "...", "subtitle": "...", "footer": "...", "orientation": "portrait"},
  "style": {"line": 3, "crease": 38, "min_px": 30, "new_fill": [236, 236, 236], "ghost_grey": 150},
  "views": {"iso": {"dir": [0.95, -0.85, 0.75], "up": [0, 0, 1]}},
  "parts": {
    "kropp":  {"mesh": "delar/kropp.stl", "id": "1", "qty": 1, "kind": "printed", "crease": 55, "min_px": 400},
    "magnet": {"primitive": {"cylinder": {"r": 3, "h": 3}}, "letter": "A", "qty": 8, "kind": "hardware"},
    "stabel": {"mesh": ["proxy/a.stl", "proxy/b.stl"], "letter": "B", "qty": 1, "kind": "hardware", "thumb_view": "iso"}
  },
  "pages": [ ... ]
}
```

**Delar.** `mesh` er éi fil eller ei liste som blir slått saman. `primitive` er `cylinder {r, h}` eller `box [x, y, z]`, sentrert i origo med valfri `axis`. `kind: "hardware"` gir bokstav og beslagkolonne, alt anna gir nummer. `crease` (grader) og `min_px` (minste strek i pikslar) per del dempar krot på tette Tripo-flater.

**Scene.** Ei liste av `{"part", "role", "at", "explode", "line"}`:

- `role`: `context` (kvit, standard), `new` (grå fyll, flytt med `explode`, med pil eller stipla line), `ghost` (gjennomsiktig grå kontur, for delar som elles skjuler innmaten) eller `exploded` (berre forskyving).
- `at`: liste av posisjonar, éin per eksemplar.
- `line`: `dashed` eller `arrow`. Standard er stipla for beslag og pil for andre delar.

**Sidetypar** (`type`):

| Type | Felt |
| --- | --- |
| `cover` | `title`, `view`, `scene` |
| `inventory` | `parts` (standard: alle som ikkje er beslag), `cols` |
| `hardware` | `parts` (standard: alle beslag), `cols`, `proportional` (storleik etter verkeleg storleik, standard på) |
| `exploded` | `view`, `scene` med `explode` på delane, `inset {scene, view, multiplier}`, `all_instances` |
| `step` | `title`, `icons` (`lim`, `snu`, `ok`, `atvaring`, `klikk`), `figures`, `flow` (`down`/`right`), `hardware` (standard: talt frå nye beslag), `note`, `warning` |
| `warnings` | `items`, `icons` |

Ein figur i `step` har `view`, `scene`, `zoom`, `callouts [{part, point, offset}]`, `arrows [[a, b]]`, `labels` (av med `false`), `multiplier` (t.d. `"x2"`) og `detail {centre, span, pos, label, scene, r}` for ei forstørringsboble.

## Avgrensingar

- Berre DejaVu Sans er brukt (det som finst i miljøet). Stegnummer blir tekne i rekkjefølgje med mindre `n` er sett.
- Det er ingen kutt- eller snittvisingar. Bruk `ghost` når ein del skjuler innmaten.
- ID-bufferen tek opptil 255 objekt per figur.
- Strekane blir rendra som raster (2400 px), medan tekst, piler, ringar og ramme er vektor i PDF-en.

## Henting av ekte IKEA-rettleiingar (`hent_manualar.py`)

`hent_manualar.py` hentar monteringsrettleiingane til heile IKEA-sortimentet som PDF, til bruk som stilreferanse. Han går frå `sitemap.xml` på ikea.com via produktsidene (JSON-blokka `assemblyAndDocuments`) til dokumentlenkjene, og lastar ned kvart unike dokument (nøkkel: `AA-nummer-revisjon`) éin gong, sjølv om fleire produkt deler det.

```bash
python3 verktoy/ikea/hent_manualar.py                          # heile no/no-sortimentet
python3 verktoy/ikea/hent_manualar.py --marknad no/no us/en de/de --tradar 16
python3 verktoy/ikea/hent_manualar.py --maks 50 --berre-indeks # rask test utan PDF-ar
python3 verktoy/ikea/hent_manualar.py --sider 3 --dpi 50       # render òg dei tre første sidene som JPG
python3 verktoy/ikea/hent_manualar.py --sok bokhylle sminkebord  # berre treffa for nokre søkjeord
python3 verktoy/ikea/hent_manualar.py --kategori 10382 20656     # berre nokre kategoriar (ID-en står sist i kategori-URL-en)
```

`--sok` og `--kategori` brukar søke-API-et til ikea.com (inntil 1000 treff per ord/kategori, med variantane) i staden for sitemapet, og er det pip-pakken [hemnes](https://pypi.org/project/hemnes/) gjorde før søkesida han skrapa forsvann; hemnes henta aldri rettleiingane.

Utdata ligg i `referansar/ikea-manualar/`:

- `indeks.jsonl` og `indeks.csv`: éi rad per dokument med `aa`, `slag` (`assembly`, `manual`, `other`, …), `url`, `fil`, `bytes`, `sider` og produkta som peikar på det (artikkelnummer, namn, type, tittel, kategori, marknad). Desse er sjekka inn, slik at korpuset kan hentast på nytt eller lenkjast direkte.
- `oppsummering.json`: tal på produkt, dokument og nedlasta byte per slag.
- `pdf/<slag>/<AA>.pdf`, `sider/<AA>/s-NN.jpg` og `_arbeid/` (sitemap- og produktcache): ikkje sjekka inn. Køyringa kan avbrytast og startast om att; alt som alt er henta blir hoppa over.

Berre `assembly` blir lasta ned om ikkje `--slag` seier noko anna; dei andre slaga blir likevel indekserte. Marknad skrivast slik han står i URL-en (`no/no`, `us/en`, `de/de`), og første marknad som nemner eit produkt vinn.

## Utvalet (`kurater.py`)

`kurater.py kandidatar` måler kvar nedlasta rettleiing (sider, raster/vektor, format, årstal), filtrerer til ståande, reine vektor-PDF-ar med 8–80 sider, favoriserer møblar og lagar eitt kontaktark (8 jamt fordelte sider) per kandidat. Eit dommarpanel (Claude med syn) skårar kontaktarka på strek, layout, klarleik, heilskap og wow i to rundar; `kurater.py utval --rangering rangering.json` kopierer vinnarane til `referansar/ikea-manualar/utval/` med kontaktark, `UTVAL.md` og heile dommarresultatet.

Status for utvalet som ligg her: 300 kandidatar frå møbelkategoriane (2 743 rettleiingar), alle skåra i runde 1 med ankerkalibrering; dei 90 beste gjekk vidare til runde 2 med tre dommarar kvar (teknisk illustratør, bokdesignar, samlar), og ei syntese skreiv grunngjevinga for dei 40 som er valde.
