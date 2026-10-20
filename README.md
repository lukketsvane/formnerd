# Stereoskopisk kamerahus

Formutvikling for eit stereokamera med to ESP32-CAM-modular. Bileta og 3D-modellane er laga med Tripo-API-et (sjå `verktoy/`). Alle meshar er formreferansar for CAD, ikkje ferdige produksjonsfiler.

## Runde 2 – stilen frå ref-7, elektronikken skjult

Hovudreferanse: `referansar/ref-7-hovudreferanse.png`. Sju konsept ligg i `konsept-r2/` (kontaktark: `konsept-r2/kontaktark.jpg`). Linsene er teikna som djupt, mørkt glas utan synleg sensor eller kretskort.

| Konsept | Idé |
| --- | --- |
| 01a tvillingløp | ref-7 redigert til to linseløp i éin stadionforma tubeløkke (chat_image_2.5_sunburst) |
| 01b tvillingløp | same idé, friare tolka (banana_pro) |
| 02 eitt vindauge | begge linsene bak eitt ovalt røykglas |
| 03 røyrende | linsene sit inne i dei opne endane av to tubar |
| 04 visir | begge linsene bak eit mørkt glasvisir under det diagonale bandet |
| 05 brille | kvar linse i eiga tubespole, spolane går over i toppbandet |
| 06 kube | kompakt kubeform; fjernast frå referansen |

### 3D-modellar (`3d-r2/`)

Tripo v3.1 image-to-model, utan tekstur, om lag 97 000 triangel. Kvar mappe har `model.glb`, Tripo-førehandsvising og `visningar.png` (front, 3/4, topp, bak). Oversikt: `3d-r2/oversikt.jpg`.

| Modell | Sveisa analysekopi | Skjult innmat, minste breidd (mm) |
| --- | --- | --- |
| 01a tvillingløp | vasstett, éin komponent | 113 side om side · 89 delt |
| 04 visir | vasstett, éin komponent | 97 side om side · 91 delt |
| 02 eitt vindauge | 4 opne og 4 fleirdelte kantar | 75 side om side · 77 delt |

Rånettet frå Tripo har opne kantar langs saumane i alle tre; det må sveisast (merge by distance) før boolske operasjonar. Detaljar og SHA256 ligg i `3d-r2/mesh-qa.json`.

### Innmatsanalyse (`3d-r2/innmat.json`)

`verktoy/innmat.py` fyller meshen med voksel (1/200 av breidda) og finn minste kroppsbreidd der elektronikken får plass heilt inne i forma med 2 mm vegg:

- **side om side**: to kort ved sida av kvarandre, 58 × 42 × 12 mm (`to_cam`), eller 58 × 42 × 25 mm med USB-kortet bak (`to_cam_pluss_mb`)
- **delt**: eitt kort med USB-kort (27 × 42 × 25 mm) og eitt kort (27 × 42 × 12 mm) i kvart sitt rom, i alle retningar (`delt_i_to_rom`)

Føresetnader: ESP32-CAM er 27 × 40,5 × 4,5 mm etter Ai-Thinker-databladet. Djupna med kameramodul (12 mm) og storleiken på ESP32-CAM-MB (kjeldene seier 27 × 40–48 mm) er estimat og må målast. Analysen ser ikkje på kvar linsene sit, FPC-føring, batteri eller om tubane blir massive. Han seier berre om forma har volum nok.

### Tilråding

Bruk **04 visir** som grunnlag for CAD. Visiret gøymer linser, kort og LED-ar bak mørkt glas, og forma held seg nær ref-7. 01a ligg nærast ref-7, men dei opne, runde linseløpa viser meir, og forma treng mest plass (113 mm side om side).

- Hent det ribba grepet og det feite, runde diagonalbandet frå 01a. Tripo har flata bandet i 04 ut til ein stropp.
- Lag visiret som eit eige mørkt eller opakt innlegg med fals og berre to linsehol. Elles syner kort og LED-ar gjennom.
- Plasser kameramodulane på FPC-forlenging fram til visiret. Ein linseavstand på 30–35 mm får plass innanfor visiret.
- Rekn med om lag 100 mm breidd når batteri, FPC og toleransar kjem med. 89–91 mm er minimum utan margin. Batteritalet er eit overslag og må køyrast på nytt i `innmat.py` med eit målt batteri.
- Den glatte baksida er staden for servicelok.
- 02 er reserve dersom storleik vinn over stereobasis. Forma er minst, men linseavstanden i konseptet er berre om lag 14 mm.

Tilrådinga vart prøvd av ein eigen kritikar som skulle prøve å avkrefte 01a. Han fann at 04 er like god eller betre på pakking, CAD-kvalitet og skjuling.

## Runde 1 – forkasta

Ti konsept i rør- og kubestil etter ref-1 til ref-5 ligg i `konsept/`. Dei vart forkasta: sensoren var synleg i linsene, og formene låg for langt frå det ønskte uttrykket.

## Verktøy

Krev `TRIPO_API_KEY` i miljøet og Python-pakkane `requests`, `trimesh` og `scipy`.

- `verktoy/tripo.py` – opplasting, oppgåver, polling og nedlasting
- `verktoy/kjor.py jobbar.json ut.json [parallelle]` – køyrer ei liste med Tripo-oppgåver og lastar ned resultata. Biletgenerering tillèt berre éi oppgåve om gongen, så bruk `1` der.
- `verktoy/mesh_qa.py` – topologisjekk (rå og sveisa analysekopi)
- `verktoy/innmat.py` – plass til skjult elektronikk

Oppgåve-ID-ar, promptar og referansar ligg i `konsept/generering.json` og `konsept-r2/generering.json`.

## Kredittar

Runde 1: 155 (modelltest 20, ni konsept 135). Runde 2: 160 (sju konsept 100, tre modellar 60). Saldo etter runde 2: 605.
