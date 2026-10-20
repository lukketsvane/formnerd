# A2 – stereoskopisk kamerahus

Kamerahus for to ESP32-CAM i stilen frå referansane: feite, mjuke tubar rundt ein mørk kjerne, og elektronikken skjult. Bileta og 3D-modellane er laga med Tripo (skripta ligg i `verktoy/`). Meshane er formreferansar for CAD, ikkje produksjonsfiler.

## Printpakke (`print/`) og monteringsrettleiing (`rettleiing/`)

**Status: klar for prøveprint, ikkje 100 % klar for sluttprint og montering.** Sjå «Kva som manglar» under.

Huset er bygd rundt delane som er valde for prosjektet: to ESP32-CAM, kvar sett på eit ESP32-CAM-MB med micro-USB. Det krev inga skrue, inga lodding og ingen flatkabelforlenging.

| Del | Printretning | Mål (mm) | Masse (massiv) | Støtte |
| --- | --- | --- | --- | --- |
| `fremre_skal.stl` | skøytesida ned | 115 × 78 × 43 | ca. 56 g | tre-støtte |
| `bakre_skal.stl` | skøytesida ned | 113 × 77 × 35 | ca. 39 g | tre-støtte |
| `innmatsramme.stl` | plata ned | 110 × 74 × 16 | ca. 23 g | tre-støtte (slicaren legg til litt) |

`A2-hus-alle-delar.3mf` har alle tre på éi 256 mm-plate. `provebitar/` har fire små utdrag av dei same delane, til å prøve skøyten, styrebena, linsehol og USB-tunnel før sluttprint. `renderar/` har samla, eksplodert og snitt.

`bambu/` har ferdig slica filer for Bambu Lab P1S (Bambu Studio 2.8.2, 0,4 mm dyse, 0,20 mm Standard, Bambu PLA Basic, tre-støtte berre frå plata, 3 veggar, 15 % fyll, Textured PEI). Profilane ligg i `bambu/profil/`, og `verktoy/bambu_slice.sh` slicar på nytt.

| Fil | Plate | Innhald | Tid | Filament |
| --- | --- | --- | --- | --- |
| `A2-hus-P1S.gcode.3mf` | 1 | fremre og bakre skal | 6 t 15 min | 117,6 g |
| `A2-hus-P1S.gcode.3mf` | 2 | innmatsramme | 37 min | 18,6 g |
| `A2-provebitar-P1S.gcode.3mf` | 1 | fire prøvebitar | 1 t 32 min | 29,0 g |

Slicaren gav inga åtvaring. Byt skrivar, plate eller filament i Bambu Studio om oppsettet ditt er eit anna.

Konstruksjon (`verktoy/bygg_hus.py`, mål i `print/parametrar.json`):

- **Kropp:** Formen er runde 3, variant 04, skalert til 115 mm breidd, med 2,4 mm vegg.
- **Skøyt:** Fremre og bakre skal møtest i ein halv overlappskøyt med 0,2 mm klaring og seks klikk-knastar.
- **Montering:** Delane under skøyten er trimma mot sveipet av fremre skal, så det kan skyvast rett på utan kollisjon (kontrollert).
- **Innmatsramme:** Ramma blir klemd i skøyten. Ho har styreben og hyller for kvar stabel, med klaring for loddespissar.
- **Stablar:** Kvar stabel (ESP32-CAM på MB) ligg med den lange sida langs breidda. Linsa sit 9,5 mm frå SD-enden (publisert typisk mål) bak eit 9,5 mm hol med fasa kant ut mot ytterflata.
- **USB:** Kvar micro-USB-port når ut gjennom kvar sin endevegg via ein tunnel på 12,5 × 9,5 mm. Den eine kjem ut på grepssida.
- **Linse 2 er flytt:** Linse 1 står i det opphavlege søkket. Linse 2 er flytt frå z = 21 til z = 42,6 mm, og det gamle søkket er fylt. Grunnen er at USB-kontakten sit 31 mm frå linsa på kortet. Med linsa nær høgre enden ville porten peike inn mot den andre stabelen. **Stereobasisen blir difor 30 mm, ikkje 48 mm.** Brei basis krev ein vinkla micro-USB-kabel eller flatkabelforlenging, og ingen av dei er stadfesta.
- **Utløysar:** Ingen fysisk utløysar. Alle 16 stifter på ESP32-CAM sit i MB-headeren, så ein knapp krev lodding. Utløysaren må gå via WiFi. Knappane på toppen er pynt.

Kontrollar som er gjorde (`print/kontroll.json`):

- ingen kollisjonar mellom delar og elektronikk i montert stilling
- minst 0,48 mm frå elektronikken til innerveggen
- monteringssveip utan kollisjon
- plata klemd på om lag 240–300 mm²
- alle delar tette og i eitt stykke, og innanfor P1S-plata

### Kva som manglar før sluttprint og montering

1. **Delane er ikkje mottekne og målte.** Utstyrslista seier «to sett avtalt henting», utan stadfesta variant. Alle mål på kort, MB, kamera og USB i `parametrar.json` er publiserte eller anslåtte (`"målt": false`). Kjeldene ligg i `print/delmaal.json`. Mål dette med skyvelære og køyr `bygg_hus.py` på nytt:
   - stabeldjupna frå linsetopp til underside MB
   - kvar linsa sit på kortet
   - kortlengda
   - høgda til USB-kontakten
2. **Prøvebitane er ikkje printa.** Skøyten, klikk-knastane, styrebena og USB-tunnelen er ikkje prøvde fysisk.
3. **Slica, men ikkje printa.** Bambu Studio gav inga åtvaring, men tre-støtta under visiret og første lag må sjåast etter på den første printen.
4. **Krava i prosjektoversikta er ikkje oppfylte:**
   - Linsa er under 30 mm (holet er 9,5 mm).
   - Utløysaren finst berre i programvaren.
   - Det er micro-USB, ikkje USB-C. Biletoverføring skjer via WiFi eller SD-kort.
5. **Delar som ikkje står på utstyrslista:** to micro-USB-kablar, to USB-ladarar (5 V, 1–2 A), tape til å feste kameramodulen på SD-sokkelen, og eventuelt microSD-kort.

Visiret er printa i same farge som skalet. Det mørke visiret på renderen er valfri måling.

## Formrundane

Runde 3, variant 04 (`runde-3/3d/04-brei-basis-eitt-bilete/`) er forma printpakken byggjer på. Variant 01 (tett visir, `runde-3/3d/01-eitt-bilete/`) er alternativet. Innmatsanalysen under er gjort før printpakken og reknar med flatkabelforlenging til kameraa. Det er ein del som ikkje er stadfesta, og grunnen til at printpakken har kortare stereobasis.

## Mapper

| Mappe | Innhald |
| --- | --- |
| `print/` | STL og 3MF i printretning, slica P1S-filer (`bambu/`), prøvebitar, parametrar, publiserte delmål, kontrollrapport og renderar |
| `rettleiing/` | Monteringsrettleiing i IKEA-stil, 13 sider (PNG og PDF) |
| `referansar/` | Stilreferansar. ref-7 er hovudreferansen, og ref-6 er ESP32-CAM-annonsen |
| `runde-1/` | Ti første konsept i rør- og kubestil, forkasta |
| `runde-2/konsept/`, `runde-2/3d/` | Sju konsept etter ref-7 med skjult elektronikk, og tre 3D-modellar |
| `runde-3/konsept/`, `runde-3/3d/` | Tett visir etter kritikken, og to 3D-modellar |
| `analyse/` | Linsesentrum, innmatsanalyse og verifiseringa av kritikken og verktøyet |
| `verktoy/` | Skript for Tripo, mesh-QA, innmatsanalyse, husbygging, slicing, renderar og rettleiing |

Kvar konseptmappe har `promptar.json` og `generering.json` med oppgåve-ID-ar, og kvar 3D-mappe har `model.glb`, Tripo-førehandsvising, `visningar.png` (front, 3/4, topp og bak) og `mesh-qa.json`.

## Innmatsanalyse (`analyse/innmat.json`)

`verktoy/innmat.py` finn den minste kroppsbreidda der dette får plass heilt inne i forma:

- kort med USB-kort (27 × 42 × 20 mm)
- kort (27 × 42 × 7 mm)
- LiPo (34 × 50 × 6 mm)
- ei lomme for kameramodulen (10 × 10 × 8 mm) rett bak kvar linse

Rekna med:

- 2 mm vegg mot utsida og mellom romma
- 0,5 mm klaring per side
- fri retning på kvar boks

Linsesentera er målte på framdjupnekartet (`analyse/linser.json`, kontrollbilete i `analyse/linser.png`).

| Mesh | Kropp med kameralommer (mm) | Nedre grense utan lommer | Stereobasis |
| --- | --- | --- | --- |
| runde-2 01a tvillingløp | 103 × 63 × 76 | 100 | 32 mm |
| runde-2 04 visir | 100 × 66 × 73 | 100 | 30 mm |
| runde-2 02 eitt vindauge | 84 × 70 × 60 | 78 | 16 mm |
| runde-3 01 tett visir | 100 × 67 × 66 | 98 | 26 mm |
| runde-3 04 tett visir, brei basis | 108 × 73 × 71 | 100 | 48 mm |

Målet er breidd × høgd × djupn.

Atterhald:

- Søket prøver eit utval plasseringar på eit dobbelt så grovt nett, så tala er øvre grenser. Ein uavhengig, uttømmande kontroll av runde-3 04 fann 95 mm utan lommer og 97–98 mm med lommer (`analyse/kontroll-innmat.json`).
- Mål på kort med kameramodul flytta til FPC, på USB-kortet (kjeldene seier 27 × 40–48 mm) og på batteriet er overslag.
- ESP32-CAM-kortet er 27 × 40,5 × 4,5 mm etter Ai-Thinker-databladet.
- Analysen sjekkar ikkje FPC-lengd, tilgang til USB-kontakt og SD-spor, festepunkt eller om banda blir massive.

## Gjennomgang av kritikken (`analyse/kritikk-verifisering.json`)

Etter runde 2 tilrådde ein kritikar 04 framfor 01a. Kvar påstand vart sjekka med eigne målingar.

| Påstand | Dom | Kva som held |
| --- | --- | --- |
| 01a ved 89 mm: berre éi delt plassering | delvis | Plasseringa stemmer, men klaringa er 0 mm, ikkje 1 mm. «114 mm i grepet» avheng av kvar grepet sluttar. Kameramodulane får ikkje plass i den løysinga. |
| 01a: for lite djupn bak glaset | delvis | Hovudpoenget held og er endå trongare: 1,9–4,2 mm. Boringa er 12–14 mm, ikkje 17 mm. |
| Batteri gjev om lag 100 / 100 / 86 mm | delvis | 01a og 04 stemmer. 02 er 84 mm. |
| 04: visiret er 10 mm djupt og 46 mm breitt | delvis | 12 mm fri djupn held. Visiret har ingen rand på 10 mm, og det er 51 mm breitt i linsehøgd. |
| Linseavstand 0,34 / 0,33 / 14 mm | delvis | 02 stemmer. 01a og 04 er 0,31 og 0,30 av breidda. Dei høge tala var lesne av perspektivbilete. |
| 04 er betre enn 01a | avkrefta | Pakkinga er om lag lik, og i delt oppsett var 04 2–3 mm breiare og 5–7 mm høgare. CAD-kvaliteten er lik. I 04-biletet syner linsene gjennom glaset. |

Revisjonane av sjølve analyseverktøyet fann feil i begge versjonane. Alle er retta, og primitivtestar stadfestar rettingane:

- Analysen frå runde 2 såg ikkje kvar linsene var, og minstetala 89–91 mm kravde eit kamera som ser til sida.
- Linsemodusen talde kameramodulen to gonger.
- Det var null klaring på korta og dobbel vegg mellom romma.
- Det mangla vegg mot minimumssidene, fordi nettet ikkje hadde tom kant.
- Veggterskelen tillét veggar ned mot 1,7 mm, og mellomveggen på det grove nettet var éi celle for tjukk.
- For tette linser gav krasj.

## Rundane

**Runde 3** (`runde-3/`): 04 visir frå runde 2 er redigert til eit tett visir med rundare band. Variant 04 flyttar linsene ut til endane av visiret. Varianten med breiare kropp (03) vart ikkje breiare, sidan biletmodellen ignorerte proporsjonsendringa. 3D frå fire genererte vinklar (image-to-multiview) er forkasta: vinklane var motstridande, med spegla visir bak og eit stort enkeltobjektiv på sida.

**Runde 2** (`runde-2/`): Sju konsept etter ref-7 med linser som djupt, mørkt glas, og 3D av 01a, 04 og 02. 01a er ref-7 redigert direkte og ligg nærast referansen.

**Runde 1** (`runde-1/`): Ti konsept etter ref-1 til ref-5. Dei er forkasta fordi sensoren var synleg i linsene og forma låg for langt frå ønskt uttrykk.

## Verktøy (`verktoy/`)

Krev `TRIPO_API_KEY` i miljøet og Python-pakkane `requests`, `trimesh` og `scipy`. Køyr frå rota av repoet.

- `tripo.py` – opplasting, oppgåver, polling og nedlasting
- `kjor.py jobbar.json ut.json [parallelle]` – køyrer ei liste med Tripo-oppgåver og lastar ned resultata. Biletgenerering tillèt berre éi oppgåve om gongen, så bruk `1` der.
- `mesh_qa.py fil.glb …` – topologisjekk (rå og sveisa analysekopi)
- `innmat.py A2/analyse/linser.json [prosessar] > A2/analyse/innmat.json` – innmatsanalysen over
- `bygg_hus.py` – byggjer printdelane, prøvebitane, 3MF og `print/kontroll.json` frå `print/parametrar.json` (krev òg `manifold3d` og `scikit-image`)
- `bambu_slice.sh` – slicar huset og prøvebitane med Bambu Studio (Flathub, under `xvfb-run`) og dei offisielle P1S-profilane, via `bambu_profil.py`
- `renderar.py` og `rettleiing.py` – fargerenderar og IKEA-rettleiinga. Dei krev Node med Playwright og `npm install` i `verktoy/` for three.js.

## Kredittar

| Runde | Bruk | Kredittar |
| --- | --- | --- |
| Runde 1 | Modelltest og ni konsept | 155 |
| Runde 2 | Sju konsept og tre modellar | 160 |
| Runde 3 | Fire konsept, to modellar og forkasta fleirvinkelforsøk | 120 |

Saldo: 485.
