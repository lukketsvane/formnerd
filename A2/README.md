# A2 – stereoskopisk kamerahus

Kamerahus for to ESP32-CAM i stilen frå referansane: feite, mjuke tubar rundt ein mørk kjerne, og elektronikken skjult. Bileta og 3D-modellane er laga med Tripo (skripta ligg i `verktoy/`). Meshane er formreferansar for CAD, ikkje produksjonsfiler.

## Tilråding

Ta **runde 3, variant 04 – tett visir med brei basis** (`runde-3/3d/04-brei-basis-eitt-bilete/`) vidare til CAD.

- Elektronikken er heilt skjult. Visiret er eit tett, mørkt panel med berre to små linsehol, og kort, sensor og lysdiodar syner ikkje.
- Stereobasisen er om lag 0,44 av breidda, det vil seie 43–48 mm. Dei andre variantane har 26–32 mm, og 02 berre 16 mm.
- Kroppen må vere om lag 97–108 mm brei for å gøyme begge korta, USB-kortet, batteriet og kameramodulane med 2 mm vegg. 97–98 mm er frå eit uttømmande søk på denne meshen. 108 mm er den konservative øvre grensa frå `innmat.py`.
- Alternativet er variant 01 (tett visir, `runde-3/3d/01-eitt-bilete/`). Han er om lag 100 mm brei, men har berre om lag 26 mm stereobasis.

Neste steg i CAD:

- Teikn opp att forma med eigne kroppar for grep, band og visir. Meshen er eitt samansmelta skal.
- Lag visiret som eit eige, tett og mørkt innlegg med fals og berre to linsehol.
- Plasser kameramodulane bak hola, og før dei med FPC-forlenging til korta. Mål kort, USB-kort og batteri, og køyr `innmat.py` på nytt med dei målte verdiane.
- Bruk den flate baksida som servicelok.

## Mapper

| Mappe | Innhald |
| --- | --- |
| `referansar/` | Stilreferansar. ref-7 er hovudreferansen, og ref-6 er ESP32-CAM-annonsen |
| `runde-1/` | Ti første konsept i rør- og kubestil, forkasta |
| `runde-2/konsept/`, `runde-2/3d/` | Sju konsept etter ref-7 med skjult elektronikk, og tre 3D-modellar |
| `runde-3/konsept/`, `runde-3/3d/` | Tett visir etter kritikken, og to 3D-modellar |
| `analyse/` | Linsesentrum, innmatsanalyse og verifiseringa av kritikken og verktøyet |

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

## Kredittar

| Runde | Bruk | Kredittar |
| --- | --- | --- |
| Runde 1 | Modelltest og ni konsept | 155 |
| Runde 2 | Sju konsept og tre modellar | 160 |
| Runde 3 | Fire konsept, to modellar og forkasta fleirvinkelforsøk | 120 |

Saldo: 485.
