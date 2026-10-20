---
name: formnerd-hus
description: Pipeline i formnerd-repoet for å gå frå referansebilete til eit ferdig, printbart hus rundt elektronikk (ESP32-CAM + ESP32-CAM-MB) - Tripo-konsept og 3D, innmatsanalyse, SDF-skal med skøyt, ramme, klikk-knastar, linsehol og USB-tunnel, eksakt printkontroll, Bambu P1S-slicing, renderar, IKEA-rettleiing og ein adversarial kontroll-workflow. Bruk han når brukaren vil lage, vidareutvikle, printe, slice, rendre eller kontrollere eit kamerahus, kabinett eller enclosure i formnerd (A2-pipelinen), eller nemner Tripo, printpakke, monteringsrettleiing, prøvebitar, bygg_hus, stereokamera eller ESP32-CAM-hus - sjølv om dei ikkje seier «pipeline».
---

# formnerd-hus: frå konseptbilete til printpakke

Pipelinen vart laga for A2 (stereokamera for to ESP32-CAM, `A2/README.md`) og ligg no som felles verktøy i `verktoy/`. Kvart skript tek prosjektmappa (t.d. `A2`) som argument og skal køyrast frå rota av repoet. A2 er referanseprosjektet: kopier frå det når du startar eit nytt.

| Steg | Verktøy | Ut |
| --- | --- | --- |
| 0 Delar og mål | research, `delmaal.json` | publiserte mål med kjelder |
| 1 Konsept | `tripo.py`, `kjor.py` (image-to-image) | `runde-N/konsept/*/bilete.png` |
| 2 3D | `kjor.py` (image-to-model), `mesh_qa.py`, `visningar.mjs` | `runde-N/3d/*/model.glb`, `visningar.png` |
| 3 Innmat | `innmat.py` | `analyse/innmat.json` |
| 4 Hus | `bygg_hus.py P` | `P/print/*.stl`, `montert/`, `provebitar/`, `kontroll.json` |
| 5 Slicing | `bambu_slice.sh P` | `P/print/bambu/*.gcode.3mf` + `.json` |
| 6 Renderar | `renderar.py P` | `P/print/renderar/*.png` |
| 7 Rettleiing | `rettleiing.py P` | `P/rettleiing/side-*.png` + PDF |
| 8 Kontroll | workflowen `kontroller-hus` | funn med alvor, prov og fiks |

Skriv README og tekstar på nynorsk, slik resten av repoet er.

## Prosjektmappa

```
P/README.md
P/referansar/                     stilreferansar
P/runde-N/konsept/<id>/           bilete.png, promptar.json, generering.json
P/runde-N/3d/<id>/                model.glb, preview.png, visningar.png, mesh-qa.json
P/analyse/                        linser.json, innmat.json
P/print/parametrar.json           alle mål; kropp.kjelde_mesh peikar på formmodellen
P/print/delmaal.json              publiserte delmål med kjelder
P/print/{*.stl, P-hus-alle-delar.3mf, montert/, provebitar/, bambu/, renderar/, kontroll.json}
P/rettleiing/
```

## Steg for steg

### 0. Delar og mål (før alt anna)

Finn datablad og målingar for dei delane brukaren *faktisk har stadfesta*, med kjelder i `delmaal.json`. Kvar verdi i `parametrar.json` har `verdi`, `kjelde` og `målt`. `målt: false` tyder at verdien ikkje er kontrollert på brukaren sine eigne delar, og det skal stå slik heilt til nokon har målt med skyvelære. Det er denne ærlegdomen som gjer at svaret på «er dette klart for print?» kan bli rett.

### 1–2. Konsept og 3D med Tripo

Krev `TRIPO_API_KEY` (skriv han aldri ut). Last opp referansar med `python3 verktoy/tripo.py upload fil.png`, som gir ein `file_token`. Lag ei jobbliste (sjå `jobbar-mal.json` i denne mappa) og køyr:

```bash
python3 verktoy/kjor.py jobbar.json ut.json 1    # biletgenerering tillèt berre éi oppgåve om gongen
python3 verktoy/kjor.py 3d.json 3d-ut.json 4
python3 verktoy/mesh_qa.py P/runde-N/3d/*/model.glb
node verktoy/visningar.mjs model.glb visningar.png
```

- Bilete: `generation/image-to-image` (t.d. `chat_image_2.5_sunburst` 10 kredittar, `banana_pro` 15 kredittar, `seedream_v5`). Inndata må vere `file_token`. Task-ID frå eit tidlegare bilete blir avvist, så last ned og last opp på nytt.
- 3D: `generation/image-to-model` med `"model": "v3.1-20260211", "texture": false, "pbr": false` (20 kredittar for standardgeometri; sjekk gjeldande pris før køyring). Her går task-ID-en til biletet fint som `input`.
- Lagre promptane i `promptar.json` og task-ID-ar og kredittar i `generering.json`, slik at runden kan gjenskapast. Sjekk saldoen med `python3 verktoy/tripo.py balance`.

Sjå den portable [skisse-til-CAD-skillen](../../../.agents/skills/skisse-til-cad/SKILL.md) og den dokumentasjonskontrollerte [Tripo-oppskrifta](../../../.agents/skills/skisse-til-cad/references/tripo-bruk.md) for modellval, segmentering, Smart Low Poly og parametergrenser. CLI-dry-run kan gi `valid=true` for parameter som API-et kombinerer annleis; kontroller også endepunktdokumentasjonen.
- Lat brukaren velje konsept. Meshen er ein formreferanse, ikkje ei produksjonsfil.

### 3. Innmat

`python3 verktoy/innmat.py P/analyse/linser.json [prosessar] > P/analyse/innmat.json` sjekkar om elektronikken får plass i forma. `linser.json` har linsesentera målte på meshen. Linsene skal sitje i det mørke visiret, så posisjonane kjem frå forma, ikkje frå elektronikken.

### 4. Hus

Kopier `A2/print/parametrar.json` til `P/print/`. Set `_tittel`, `kropp.kjelde_mesh`, `kropp.breidd`, `linser.y` og `linser.z`, og `linser.fyll_søkk_z` (søkk i forma som ikkje skal ha linse, blir fylte). Køyr så:

```bash
python3 verktoy/bygg_hus.py P      # ca. 90 s
```

Konstruksjonen i korte trekk (detaljar i `verktoy/bygg_hus.py`):

- **Skal:** Signert avstandsfelt (EDT på voxelfyll med pitch 0,25) av formmodellen. Level-sett gir innerflater (vegg 2,4).
- **Skøyt:** Halv overlapp ved `x_s`, med fremre ytre lepp og bakre indre lepp (0,8 mm tjukkare innover). Skøyten har 45°-fuge og 45°-skulder, så han treng inga støtte. Seks klikk-knastar sit midt på bakre lepp.
- **Innmatsramme:** Plata blir klemd i skøyten med ein 45°-kant mot skuldra. Styreben og hjørnehyller held kvar stabel.
- **Plassering:** Kvar stabel blir flytt bakover med bisection på eksakt `min_gap` til alt utanom linseløpet har `stabel.frigang` til fremre skal. Linsetoppen er avgrensa av `inn_i_hol`.
- **Opningar:** Linsehol med indre fas, fresing innanfrå og synsfeltkjegle. USB-tunnelen har minst `vegg_under` ned til skøyten.
- **Påskyving:** Bakre skal og ramme blir trimma mot sveipet av fremre skal langs −x. Platekanten blir trimma kolonnevis mot den lågaste flata på fremre skal.

Godkjenn ikkje eit bygg før `P/print/kontroll.json` viser alt dette:

- `kollisjonar_mm3` er `{}`.
- Alle verdiar i `påskyving_mm3` er `0.0`.
- Kvar stabel har `klaring_til_fremre_skal_mm` ≥ `frigang`, og `linseløp_til_holkant_mm` er rimeleg (≥ 1,5).
- Kvar del i `delar` har `stl_vasstett: true`, `stl_kantar_med_fleire_enn_2_flater: 0`, `lag1_bitar: 1`, låg `lag1_smalare_enn_2_liner_mm2` og `får_plass_på_P1S: true`.

### 5. Slicing (Bambu Studio, P1S)

```bash
bash verktoy/bambu_slice.sh P
```

Skriptet krev Bambu Studio frå Flathub (`flatpak install --user flathub com.bambulab.BambuStudio`) og `xvfb-run`. Det flatar ut dei offisielle profilane (P1S 0,4, 0,20 mm Standard, Bambu PLA Basic) og legg til tre-støtte berre frå plata, 3 veggar og Textured PEI. Så slicar det huset og prøvebitane, og skriv tid, lag, vekt og åtvaringar til `bambu/P-*.json`. Bambu Studio fordeler delane på plater sjølv, så les tala frå JSON-fila og ikkje frå gamle notat.

### 6–7. Renderar og rettleiing

```bash
npm install --prefix verktoy        # three 0.169.0; Playwright/Chromium er førehandsinstallert i miljøet
python3 verktoy/renderar.py P       # samla, samla_bak, eksplodert, snitt
python3 verktoy/rettleiing.py P     # IKEA-stil: line art frå normal-, djupn- og id-buffer
```

`strek.mjs` rendrar ortografisk i headless Chromium (swiftshader). `strek.py` hentar ut kantane til strekteikning. Sidene i `rettleiing.py` er skrivne for ESP32-CAM + MB (program, kamera på SD-sokkel, CAM på MB, stablar i ramma, ramma i bakre skal, fremre skal på og klikk, straum, opne). Har prosjektet anna elektronikk, må du endre `stabel_modell()` i `bygg_hus.py` og sidene i `rettleiing.py`. **Sjå alltid på bileta før du leverer.** Tekst kan krasje med teikningar, og ein render kan bli svart.

### 8. Kontroll

Køyr workflowen `kontroller-hus` med `args: {"prosjekt": "P"}`. Han har fire uavhengige målande kontrollørar (print, toleransevariantar, optikk og USB, montering) og ein kritikar til slutt. Ingen av dei endrar repoet. Rett funna i `parametrar.json` eller `bygg_hus.py`, byggjer på nytt og køyr kontrollen igjen til det ikkje kjem nye blokkerande eller høge funn. Ver kritisk til funna: kvart funn skal ha eit tal frå eit skript, og du skal kunne spore det.

## Å svare på «er det 100 % klart?»

Svar ærleg og konkret, i tre lister:

1. **Kontrollert:** kva `kontroll.json` og slicaren viser.
2. **Ikkje kontrollert:** mål med `målt: false`, prøvebitar som ikkje er printa, og variantar som ikkje er køyrde.
3. **Utanfor designet:** krav i briefen som ikkje er oppfylte, og delar som ikkje står på utstyrslista (kablar, ladarar, tape, microSD).

Rekkjefølgja er alltid: print prøvebitane først, mål dei verkelege delane, oppdater `parametrar.json`, byggjer på nytt og print så heile huset.

## Fallgruver (lærde i A2)

- **Ikkje bruk trimesh-voxelisering på store meshar** (minnet tek slutt). Bruk paritetsfyllet `hus.fyll`, og sveis UV-saumar med `merge_vertices(merge_tex=True, merge_norm=True)` før fyll.
- **Coincidente flater gir ikkje-mangfaldige STL-kantar.** Det skjer når to level-sett eller boksar møtest i same plan. Forskyv nivåa 0,05 mm (sjå fasane), legg ein liten jitter på voxelmeshar (sjå `sveip_fram`), og la boksar overlappe i staden for å møtast kant mot kant. Kontroller alltid den *eksporterte* STL-fila (`stl_sjekk`), ikkje berre manifold-objektet.
- **Avstandsfelt-kontrollar overvurderer klaring** med opptil 0,3 mm. Bruk eksakt `Manifold.min_gap` til plassering og rapport, og ein kollisjonsterskel på 0,01 mm³, ikkje 0,5.
- **Ein skøyt er sjeldan på det breiaste snittet.** Alt som blir lagt til etter sveiptrimminga (som platekanten), må trimmast mot fremre skal òg. Ellers kolliderer det under påskyvinga. `påskyving_mm3` fangar dette.
- **Knastar og fasar må plasserast mot den faktiske leppa,** ikkje mot nominelle mål. Ein knast som blir kutta i sengplanet, blir ei halvkule med flat side mot påskyvinga.
- **Elektronikken bestemmer mykje:** USB-kontakten sit ved enden av kortet, så kvar linsa kan stå avgjer om porten når ut. Rekn ut tilgjengeleg port før du lovar ein stereobasis.
- **Render:** Kall `computeVertexNormals` når GLB-en manglar normalar (elles blir renderen svart). Skriv buffera i lineær fargerom, kod djupna i to kanalar (elles får du band), og kall `updateMatrixWorld` før du projiserer ankerpunkt.
- **Tripo:** Biletgenerering har samtidigheit 1, og `submit` prøver på nytt ved kode 2000/1007. CDN-nedlastingar kan bli avbrotne, og `download` prøver då på nytt.
- **Vent ikkje i forgrunnen** på lange jobbar som bygg, slicing og rendering. Køyr dei i bakgrunnen og gjer anna arbeid medan dei går.
