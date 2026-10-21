# Monteringsrettleiingar frå CAD-delar

`bygg.py` byggjer A4-hefte frå JSON og delane som STL, GLB eller enkle primitiv. Teikningane kjem frå synleg CAD-geometri i 2400 pikslar. Tekst, piler, delenummer og koplingsskjema er vektor i PDF-en.

## Entropi A3 · R03

[Ferdig PDF](eksempel/ut/rettleiing.pdf) · [sideoversikt](eksempel/ut/kontaktark.png) · [rask sidevising](eksempel/ut/bla-gjennom.gif) · [spesifikasjon](eksempel/entropi-a3.json)

Eksempelet bruker geometrien i `A4/Entropi-A3-print` frå `f519652e`: to magnetskall, éin ESP32-CAM med MB-kort, prenta aksel og A17 V4-hjul. Heftet har 20 sider og 15 nummererte operasjonar.

- Faste P01–P06 og H01–H08 med mengder og namn.
- Seks magnetpar, eintydig polaritetsmerking og stativmutter frå undersida.
- Større oversikt, kopla detaljvisingar, målsett akselutstikk og styreliner for dei tre pinnane.
- Skjematiske leidningar, A/B-kontroll av brytaren og konkret opning utan strekk i leidningane.
- Eige koplingsprinsipp og prøving før innbygging.
- Mekanisk montering og funksjon som krev testa firmware er tydeleg skilde.

Dette er monteringsgrunnlag for ein prototype. Meshar og komponentproxyar dokumenterer nominell geometri; fysisk passform, laststyrke og elektronikk er ikkje prova av PDF-bygginga.

## Bygg

Krev Python 3.12, Node.js, Chromium og Poppler (`pdftoppm`).

```bash
python3 -m venv .venv-manual
. .venv-manual/bin/activate
python -m pip install -r verktoy/ikea/requirements.txt
npm ci --prefix verktoy
cd verktoy
npx playwright install chromium --only-shell
cd ..
python verktoy/ikea/bygg.py verktoy/ikea/eksempel/entropi-a3.json
```

Valfri utdatamappe er siste argument. `PLAYWRIGHT_BROWSERS_PATH` kan peike på ein eksisterande nettlesarinstallasjon; `THREE_DIR` kan overstyre three.js. I ChatGPT-miljøet blir `CODEX_PRIMARY_RUNTIME_NODE` brukt når variabelen finst.

Utdata: `rettleiing.pdf`, `kontaktark.png`, `bla-gjennom.gif`, `sider/side-NN.png` og `rapport.json`. PNG-sidene er 1440 pikslar breie; GIF-en er 768 pikslar brei med 650 ms per innside og 1400 ms på første og siste side. Sidevisinga er ei rask oversikt; bruk PDF eller PNG for å lese stega. Alle sidene blir talte og validerte før dei erstattar tidlegare sideutdata. Mellomfiler ligg i `_arbeid/`. Cachen bruker innhaldet i delane, scena og renderarkoden. Endra sidelayout brukar same geometribuffer på nytt.

## Delar og scener

Alle filstiar er relative til JSON-fila. Geometrien bruker mm i ei felles monteringsramme. `offset` på ein del flyttar eit printorientert mesh inn i ramma; `at` og `explode` i scena er vidare forskyvingar.

Ein del har `mesh` (fil eller liste), eller `primitive` (`cylinder` eller `box`). Primitiv kan ha `axis` og `rotation` i grader. Ein sylinder kan ha `sections` og `inner_r`; ein sekskanta mutter får rundt gjennomhol. `name`, `detail`, `qty`, `thumb_view`, `crease` og `min_px` styrer deleoversikta og kantutvalet.

`organic: true` samlar lange konturar varsamt og fjernar doble parallelle strek på mjuke meshflater. Dette er av som standard. Kontroller resultatet mot geometrien.

| Rolle | Visning |
|---|---|
| `context` | Kvit eksisterande del |
| `new` | Lys grå del; `explode` gir innstikksline eller pil |
| `exploded` | Forskyvd del utan automatisk pil |
| `ghost` | Grå gjennomsiktig kontur rundt innmaten |

`at` er ei liste med posisjonar, éin per eksemplar. `line` kan vere `arrow`, `dashed` eller `none`. For ein kortstabel kan éin del bere pila medan resten bruker `none`. `cut: [nx, ny, nz, offset]` gir eit geometrisk plansnitt.

## Sider og stil

| Type | Innhald |
|---|---|
| `cover` | Tittel, undertittel, hovudfigur og status |
| `inventory` | Prenta delar med mengder og namn |
| `hardware` | Komponentar og verktøytekst |
| `exploded` | Oversikt med delenummer og valfrie `guides` |
| `step` | Nummer, handling, figurar og kontroll |
| `warnings` | Kontrollpunkt, avgrensingar og lenkbare kjelder |

Alle sider kan ha `title` og `intro`. Monteringssider bruker `note`, `warning`, `check` og valfri `alternative`. Uttrykkeleg `hardware` tel forbruket: `[]` betyr ingen ny komponent. `parts_used` styrer den synlege delelinja og kan vise delar som blir brukte om att. `action: "inspect"` markerer kontroll eller klargjering utan ny del.

Figurar har `scene`, `view`, `caption`, `labels`, `callouts`, `annotations`, `arrows` og valfri `detail`. `centre` + positiv `span` med `crop: false` held eit utsnitt fast. `flow: "detail"` bruker to figurar som hovudvising og kopla, rund detaljvising. Andre val er `down` og `right`. `diagram` støttar `shutter_wiring`, `magnet_pair` og `switch_contacts`, teikna som vektorskjematiske framstillingar.

`dimensions` har to punkt `a` og `b` i mm, ein 2D-`offset` i PDF-punkt og valfri etikett. Verdien blir elles rekna frå 3D-avstanden. `guides` er par av 3D-punkt; styrelinene er berre synlege i det opne rommet mellom delane. `schematic_paths` bruker 1 + 3n kontrollpunkt for kubiske kurver og skal merkast som skjematiske i figurteksten. `callouts` kan bruke ein fri `label` for nummererte kontrollpunkt. `label_offsets` flyttar delenummer i den eksploderte oversikta. `arrows_in_frame` plasserer ei rørslepil med normaliserte 2D-punkt i figurplassen, til dømes utanfor ein tett samanstilling.

Fysiske strekbreidder er i PDF-punkt: `line_pt` for silhuett, `seam_pt` for deleskøyt, `feature_pt` for andre synlege kantar og `valley_pt` for eventuell organisk dalstrek. Standardmargen er 45,35 pt (16 mm). Sjå eksempelfila for ei komplett spesifikasjon.

## Kontroll før levering

```bash
python verktoy/ikea/kontur.py
python verktoy/ikea/bygg.py verktoy/ikea/eksempel/entropi-a3.json
```

Dei seks kantkontrollane skil samanhengande flater frå verkelege sprang, held deleskøytar og kryssande kantar, og fjernar parallelle dublettar. Byggerapporten kontrollerer komponentmengder, tomme figurar og tekst-/etikettkollisjonar. Han registrerer PDF-, spesifikasjons-, kode-, font-, avhengnads- og mesh-sjekksummar samt geometriutgåva. PDF-en bruker fast metadata for repeterbare bygg med same kjelder og miljø. Rapporten har relative filstiar, og sideeksporten kontrollerer sidetal, pikselmål og alle GIF-rammer/tider.

Sjå gjennom alle sidebileta i lesestorleik. Ein feilfri maskinrapport stadfestar ikkje at ei pil, eit utsnitt eller ei instruksjon er forståeleg. Bruk merkinga på dei faktiske elektronikkdelane.

## Filer og grenser

- `bygg.py`: geometri, projeksjon, figurar, validering og rapport.
- `strek.mjs`: lokal three.js-rendering av normal-, djupne- og ID-buffer.
- `kontur.py`: separate konturfamiliar og semantiske kontrollar.
- `sider.py`: sidelayout og vektordiagram.
- `vising.py`: validert PNG-, kontaktark- og GIF-eksport utan ny geometriutrekning.
- `eksempel/entropi-a3.json`: gjennomarbeidd monteringseksempel.

ID-bufferen støttar opptil 255 synlege objekt per pass. Dei faktiske monteringsaksane, delane og kjeldene må oppgivast i spesifikasjonen; verktøyet finn ikkje på mekaniske samanføyingar.
