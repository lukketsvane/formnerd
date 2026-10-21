# Entropi · A3-print (delt skal)

A3-designet frå `arkiv/entropi-a3` som delt og hol kamerakropp for Bambu Lab P1S. Kroppen er delt vassrett gjennom linseaksen (z = 32) i eit botnskal og eit toppskal som blir haldne saman av seks magnetar og tre pinnar. Innsida er holt ut til ein jamn vegg på 2,6 mm, og elektronikken står i to sporstolpar. Hjulet på toppen er bytt ut med A17-entropihjulet (`../../A17/entropihjul/`) på ein EC11-dreieknapp.

![CMF](bilete/cmf.png)

![Sprengd](bilete/sprengd.png)

![Snitt gjennom linseaksen](bilete/snitt.png)

## Prent i denne rekkjefølgja

| Fil i `print/` | Delar | Tid | PLA |
| --- | --- | --- | --- |
| `A3-Entropi-botn-P1S.gcode.3mf` | Botnskal | 2 t 44 min | 66 g |
| `A3-Entropi-topp-P1S.gcode.3mf` | Toppskal | 4 t 10 min | 101 g |
| `A3-Entropi-smaadelar-P1S.gcode.3mf` | Utløysar, USB-lokk, hjulaksel | 12 min | 2 g |
| `A3-Entropi-hjul-A17-P1S.gcode.3mf` | A17-hjulet V1–V4, vel eitt | 39 min | 10 g |

Alle filene er slica med Bambu Studio 02.08.02.61:
- maskin «Bambu Lab P1S 0.4 nozzle», med P1S-startkoden (AMS-lasting, dysereins, 220 °C) og printar-ID C12
- prosess «0.20mm Standard @BBL X1C», som er standarden for P1S, med 3 Arachne-veggar og 15 % fyll
- filament «Bambu PLA Basic @BBL P1S 0.4 nozzle» på Textured PEI-plata
- trestøtte berre frå plata

`print/bambu/skal.json` har kontrollen for kvar fil.

Slik sender du ei fil: opne `.gcode.3mf` i Bambu Studio, trykk *Print plate*, vel P1S-en, knyt filament 1 til PLA-sporet og trykk *Send*. Du kan òg kopiere fila til microSD-kortet i skrivaren.

- **Botnskalet** står på botnen med delingsflata opp. Støtta står berre utanpå, under den runde botnkanten og linseløpet.
- **Toppskalet** står på delingsflata. Støtta står under det flate taket inne i skalet og kan takast ut gjennom den opne delingsflata. Magnetlommene, EC11-pipa, brytartrakta og USB-tunnelen har tak på 45°, så dei treng inga støtte.

## Innkjøp

ESP32-CAM, ESP32-CAM-MB (micro-USB), microSD, 6 × 6 mm trykknapp, 12 magnetar Ø6 × 3 mm, 2 leidningar 26–30 AWG på om lag 15 cm og CA-lim.

EC11-dreieknapp med 20 mm D-aksel er valfri. Har du han ikkje, limer du hjulakselen (smådelplata) i holet, og hjulet sit på han.

## Montering

1. Pinnane er prenta på botnskalet. Lim seks magnetar i lommene i botnskalet med same pol opp. Legg ein magnet på kvar av dei, og merk oversida. Lim dei merka magnetane i toppskalet med merket ned, slik at dei trekkjer mot kvarandre.
2. Lodd leidningane til GND (pinne 2) og IO13 (pinne 4) på 5V-rekkja på ESP32-CAM. Set kameraet på MB, set i SD-kortet, last opp firmware og test.
3. Senk stabelen rett ned i spora i dei to stolpane i botnskalet. Linsa går ned i halve linsesetet.
4. Før leidningane opp gjennom holet i brytartrakta i toppskalet. Lodd brytaren på to diagonale bein, og lim han i lomma med beina i full lengd.
5. EC11: før dreieknappen opp gjennom pipa i toppskalet til aksen kjem ut av holet på toppen, og lim han. Kort akselen til 5,5 mm over toppflata. Utan EC11 limer du hjulakselen i holet i staden.
6. Set toppskalet på. Pinnane styrer det, og magnetane held det.
7. Lim utløysaren på brytaren og trykk A17-hjulet på akselen.
8. Skyv USB-kabelen inn i tunnelen på hjulsida, eller set i USB-lokket.

Ei ny rettleiing i IKEA-stil for det delte skalet kjem. `montering/` viser framleis den gamle luke-versjonen.

## Kontroll (`print/kontroll.json`)

Måla på elektronikken er nominelle, og fysisk passform er ikkje prøvd.

| Kontroll | Resultat |
| --- | --- |
| Delar | Botnskal 74,4 cm³ og toppskal 134,9 cm³. Alle fem delane er ein lekam kvar (manifold). |
| Innvendig rom | 287 cm³ |
| Kollisjon mellom elektronikk og skal | 0 mm³ for alle proxyar. Klaringa til stabelen er 0,2 mm i begge skala. |
| Monteringsbaner | 0 mm³ for: stabel ned i botnen, toppskal ned over stabelen, USB-plugg inn, EC11 opp i pipa, brytar ned i lomma |
| Veggar mot holrom | Holkjerna minst 1,34 mm, magnetlommer 1,59, pinnehol 1,26, brønnen 1,27, brytarlomma 2,54, USB-tunnelen 2,01, EC11-pipa 3,3 |
| Tynne parti (strålar frå 60 000 overflatepunkt) | Linseringen i skulpturen, knivkanten i USB-opninga og ei finne i den eine kortstolpen |
| Hjulet | Skore av ved z = 80 innanfor r = 11,0 rundt (31,1; 103,9). A17-hjulet er Ø24. |

## Kjende avgrensingar

- **Fysisk passform er ikkje prøvd.** Prøv stabelen i stolpane og skala mot kvarandre før du limer noko.
- **Utløysaren krev kode:** IO13 mot GND, med SD i 1-bit-modus og debounce. Hald blitzen (GPIO4) av. Legg inn OTA-oppdatering, for MB-knappane er innebygde.
- **USB-C-porten på grepet er berre form.**
- Filene har ikkje miniatyrbilete.

## Regenerering

```bash
cd verktoy
npm install
python3 lag_skal.py       # skal, delar, proxyar og kontroll.json
python3 print_skal.py     # prentretning
bash bambu_skal.sh A3-Entropi-botn-P1S ../print/printretning/botn.stl
bash bambu_skal.sh A3-Entropi-topp-P1S ../print/printretning/topp.stl
python3 cmf_overfor.py && python3 vis.py
```

Mål og plasseringar ligg i `verktoy/delar_konfig.json` under `skal`. Luke-versjonen med stabelhaldar ligg i git-historikken (958babc).
