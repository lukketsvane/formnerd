---
name: ikea-rettleiing
description: Lag ei monteringsrettleiing som ser ut som ein ekte IKEA-manual, frå ei CAD-samanstilling (STEP, STL, GLB eller delar i felles mm-ramme). Dekkjer sidefølgje, figurar med verktoy/ikea/bygg.py, målte stilreglar frå dei beste IKEA-PDF-ane, samanlikning side mot side og kontroll før levering. Bruk han når brukaren vil ha monteringsrettleiing, monteringsmanual, byggjerettleiing, assembly instructions eller «IKEA-stil» for eit produkt i formnerd, eller vil forbetre ein eksisterande manual mot IKEA-referansane, sjølv om dei ikkje seier «skill».
---

# IKEA-rettleiing frå CAD

Målet er ein manual som ein IKEA-teiknar kunne ha levert: svart strek på kvitt, eitt stort stegnummer, mengder ved handlinga, nesten ingen ord. Stilen er ikkje ein pynt oppå geometrien. Han er ein **visuell grammatikk**: få element med fast tyding, brukte likt på kvar side, slik at lesaren slepp å tolke.

Skriv tekst i manualen og i README på nynorsk, og så lite av han som mogleg.

## Kjelder å byggje på

| Kjelde | Kva ho gir |
| --- | --- |
| `referansar/ikea-manualar/utval/` | Dei 40 finaste ekte IKEA-manualane, rangerte av eit dommarpanel. `UTVAL.md` grunngjev kvar, `kontaktark/` viser 8 sider per manual. Topp 3: MILSBO, PAX, MOSSJÖN. |
| `referansar/ikea-monteringsstil/` | Ti einskildsider, éi per sidetype (framside, deloversikt, beslag, eksplodert, steg, åtvaring). |
| `A1/Stereo-Multigrip-R04-USB18/manual-r09/` | Beste eigne døme. `ikea-reference-audit.md` og `ikea-comparison.md` viser korleis 26 sider vart til 17 og kva som vart målt i MILSBO, PAX og MOSSJÖN. |
| `kamera-boge-r01/manual/`, `A4/Entropi-A3-print/montering/` | Tidlegare manualar i same stil, M06 og A3. |
| `verktoy/ikea/bygg.py` | Motoren: JSON-spesifikasjon og delar til PDF, side-PNG, kontaktark og `rapport.json`. Sjå `verktoy/ikea/README.md` for alle felt. |
| `verktoy/ikea/hent_manualar.py`, `kurater.py` | Hentar fleire ekte manualar frå ikea.com og lagar kontaktark, om du treng referansar for ein ny produkttype. |

IKEA-sidene er tredjepartsmateriale. Bruk dei som grafisk arbeidsmåte, men kopier aldri logo, figurar, verktøyteikningar, IKEA-mannen eller skrifta inn i vår manual.

## Arbeidsflyt

### 1. Grunnlag frå CAD

- Alle delar i éi monteringsramme i mm. `at` og `explode` i spesifikasjonen er forskyvingar i den ramma.
- Lås del-ID-ar og mengder mot BOM og printfiler. Same ID i deloversikt, steg og filnamn. Repetisjon blir ei mengd (4x), aldri fire like steg.
- Les monteringsrekkjefølgja ut av geometrien: kva må inn før kva, kva retning går innføringa, kva held delen på plass. Ein manual kan ikkje vere meir rett enn CAD-en.
- Merk **portar**: handlingar som enno ikkje er verifiserte (t.d. at eit kort kan førast inn). Ein port står som ei eiga, roleg side før monteringa, med sluttstilling og stopptekst og utan falsk innføringspil. Han skal aldri gøymast i eit vedlegg.
- Endre aldri CAD for å få ei penare teikning.

### 2. Vel referansar før du teiknar

Finn 2 til 3 manualar i `utval/` som liknar objektet (storleik, tal på delar, typen handling). Rasteriser sidene som svarar til sidetypane du treng og sjå på dei:

```bash
pdftoppm -r 60 -png -f 11 -l 11 "referansar/ikea-manualar/utval/01-MILSBO-AA-2094158-9.pdf" /tmp/ref-milsbo
```

Skriv ned i ein tabell (`ikea-reference-audit.md` i manualmappa): referanse, fysisk sidenummer, kva grep sida gjer, og korleis det blir overført. Dette er det som gjorde R04-manualen god; han vart betre av å sjå på sider, ikkje av å lese om stil.

### 3. Storyboard

Standard sidefølgje, tilpassa objektet:

1. **Framside**: produktnamnet stort, éin komplett isometrisk figur av ferdig produkt, nesten ingenting anna. Inga innhaldsliste, ingen ingress.
2. **Delar**: form, ID og mengd i rutenett. Nye og gjenbrukte delar kan stå på kvar si side.
3. **Beslag**: bokstav eller familie-ID over, mengd under, i reell storleik der det går.
4. **Verktøy og førebuing**, berre dersom det trengst. Åtvaringar der risikoen er, ikkje på ei generell side.
5. **Eksplodert oversikt**, når delane har eit samanheng som ikkje er openbert.
6. **Steg**: éi hovudhandling per steg. To påfølgjande handlingar på same objekt kan dele side (plassér, så lås).
7. **Kontroll**: eitt stort ferdigbilete og ei svært kort sjekkliste.
8. **Opne og feil**, om produktet skal kunne takast frå kvarandre.
9. **Bakside**: ferdig produkt frå ein annan nyttig vinkel, revisjon og kjeldelenkje.

Kutt alt som ikkje lærer montering: printhistorikk, filamentval, teknisk proveniens, nominelle mål og gjentekne forklaringar høyrer heime i README. Ikkje fyll ei side for å nå eit sidetal.

### 4. Figurar

Bygg figurane frå same CAD-geometri. Med `verktoy/ikea/bygg.py`:

```bash
npm install --prefix verktoy               # three.js; Playwright/Chromium må finnast
python3 verktoy/ikea/bygg.py P/rettleiing/spesifikasjon.json P/rettleiing/ut
```

Start frå `verktoy/ikea/eksempel/entropi-a3.json`. Sidetypar: `cover`, `inventory`, `hardware`, `exploded`, `step`, `warnings`. I scenane er `role` `context` (kvit), `new` (grå fyll, med pil eller stipla line), `ghost` (gjennomsiktig kontur) eller `exploded`. Tette Tripo- eller meshflater får krot: auk `crease` og `min_px` for den delen.

Reglane som gjer figurane rette:

- **Same kamera og skala** gjennom ein samanhengande sekvens. Byt berre synsretning for å vise ei skjult handling, og vis vendinga med ein liten vendingsfigur eller pil først. I `bygg.py` gir same `centre` og `span` på alle figurane i sekvensen same skala; rekn dei frå delane, ikkje for hand.
- **Ny del er grå, resten kvitt.** Lesaren ser kva som kjem til utan tekst. Unngå nesten kvite, blanke delar mot kvit bakgrunn; gi dei lys grå fyll og kontur.
- **Rørslepila** er tjukk, kort, har éi retning og endar ved det faktiske grensesnittet.
- **Innføringsaksen** for beslag er ei fin stipla line, skild frå rørslepila.
- **Detaljbobla** er knytt til staden: ein liten heil figur, ein ring rundt festet, éin samanhengande leiar til bobla. Leiaren er open mot bobla, treffer rett skøyt og går klar av tekst. Ei boble som flyt åleine er ein feil. Den automatiske etiketten sit ved kanten av boksen til delen og bommar på lange, skrå delar: set då `label: false` og ein `callout` med punkt på delen.
- **Sluttstillinga** blir vist etter kvar låsing, i same vinkel.
- **Rett og feil** blir vist som eit par med kryss på det feile, ikkje forklart i ord.
- **Glas** er to skrå parallelle strekar.
- Ingen skugge, gradient, farge, golvplan med perspektiv eller dekorative rammer.

### 5. Stilark

Målt i MILSBO, PAX og MOSSJÖN (A4 595,28 × 841,89 pt). Bruk tala i faktisk A4-storleik, ikkje på skjerm.

| Element | Verdi |
| --- | --- |
| Hovudstrek, geometri | 0,75 pt (dominerer: PAX s. 8 har 1079 baner på 0,75 pt) |
| Lette samband, leiarar, aksar | 0,5 pt |
| Framheving, ytterkontur, piler | 1,5 pt |
| Stegnummer | 32 pt, halvfeit, øvst til venstre i figursona |
| Mengd ved handlinga («4x») | 18 pt |
| Del- og beslagnummer | 7 til 7,5 pt |
| Sidetal | 9 pt |
| Produktnamn på framsida | 90 til 140 pt, tilpassa lengda på namnet |
| Fargar | svart strek, kvit botn, éin lys grå fyll for nye delar og ein mørkare grå for markering |

Eigne tidlegare forsøk med 0,32/0,52 pt strek var for tynne; 0,5/0,75 pt var vedtaket som fungerte. Kontroller at tjukkare strek ikkje gjer tette detaljar (kretskort, gjenger) svarte. `bygg.py` teiknar strek som raster, og fast `style.line` gir om lag `line × figurbreidd / 1200` pt (målt: standardverdien 3 gir om lag 1,5 pt). Set difor `style.line_pt` til 0,75, så vel byggjaren strekbreidda per figur og boble; `rapport.json` viser `strek_pt`. Set òg `steg_pt` 32, `mengd_pt` 18, `mengd_fyrst` true, `tittel_pt` 90 eller meir med `tittel_feit` true, `sidetal_pt` 9, `del_pt` 7,5, `lett_pt` 0,5, `ramme` false og `beslagkolonne` false; standardverdiane er frå før målinga. Port, kontroll og bakside er `step` med `n: false`, og glas er figurfeltet `glas`.

### 6. Kontroll før levering

1. Les `rapport.json`: avvik mellom beslag i stega og mengda i dellista, steg utan ny del, tomme figurar, tekst som overlappar. Alle åtvaringar skal vere løyste eller grunngjevne.
2. Sjå kontaktarket, og så kvar side i full storleik.
3. Samanlikn side mot side med referansen frå steg 2, i same skala:

   ```bash
   montage ut/sider/side-07.png /tmp/ref-milsbo-11.png -tile 2x1 -geometry +20+20 /tmp/samanlikn-07.png
   ```

4. Gå gjennom lista: eitt tyngdepunkt per side, stegnummer og mengder lesbare på A4, leiarar treffer rett, kamera stabilt i sekvensen, sluttstilling rett, portane står før monteringa, ingen tekst gjentek det figuren alt seier, ingen IKEA-grafikk kopiert.
5. Skriv i README kva som er digitalt kontrollert og kva som enno manglar fysisk prøving. Ein vakker manual er ikkje prov på at delane passar.

### 7. Lever

Lag `P/rettleiing/` (eller `manual/`) med PDF, `sider/side-NN.png`, kontaktark, spesifikasjonen og `ikea-reference-audit.md`. Spesifikasjonen og delane er kjelda; PDF-en skal kunne byggjast på nytt med éin kommando. Nummerer revisjonar (M01, M02 … eller r05, r06 …) og skriv i README kva som endra seg frå førre utgåve.

## Kjende feil frå tidlegare manualar

- **Katalogrytme**: overskrift, seksjonsnamn, undertittel, biletekst og avsnitt på kvar side. R04 gjekk frå 26 til 17 sider ved å fjerne dette og slå saman like låsesteg.
- **Innhaldsliste og teknisk ingress** på framsida eller side 2. IKEA har ingen av delane.
- **Flytande detaljutsnitt** utan heil figur og leiar.
- **Falsk innføringspil** over ein veg som ikkje er verifisert.
- **For tynn strek** (0,32 pt) og nesten kvite delar som forsvinn mot botnen.
- **Blanding av fargerender og vektor** tilfeldig frå side til side. Materialrender kan brukast på framside og maskinvaresider, men inngrepa skal vere strek.
- **Pynt som ikkje finst i modellen**: skruar, kabelfeste eller alternative delar som ikkje er i BOM.
