# Entropi · A3-print

Prentklar versjon av A3-designet: Tripo-forma frå `arkiv/entropi-a3`, skoren opp til fem delar for Bambu Lab P1S, med ESP32-CAM og ESP32-CAM-MB inni. Delane blir haldne saman med lim og magnetar. Ingen skruar.

![CMF](bilete/cmf.png)

![Snitt gjennom linseaksen](bilete/snitt.png)

## Kort sagt

1. Set kameraet på MB-kortet og mål **D** (steg 1 i rettleiinga). Ligg D mellom 15,7 og 16,2 mm, kan du prente plata som ho er. Elles byter du stabelhaldaren med den næraste fila i `print/printretning/haldar-variantar/`.
2. Opne `print/A3-Entropi-P1S.gcode.3mf` i Bambu Studio og send til P1S-en. Plata tek om lag 5 t 44 min og brukar 193 g PLA.
3. Følg `montering/Entropi-A3-montering.pdf`, 13 steg i IKEA-stil.

## Filer

| Fil | Bruk |
| --- | --- |
| `print/A3-Entropi-P1S.gcode.3mf` | Ferdig slica plate for P1S. Kan sendast rett til skrivaren. |
| `print/A3-Entropi-P1S.3mf` | Same plate som Bambu Studio-prosjekt, for å endre innstillingar eller byte haldar |
| `print/A3-Entropi-alle-delar.3mf` | Alle delane plasserte på éi 256 mm-plate, utan slicarinnstillingar |
| `print/printretning/` | Delane i prentretning. `haldar-variantar/` har stabelhaldaren for D = 14,0–18,0 mm i steg på 0,5 mm. |
| `print/stl/` | Delane i samanstillingsposisjon |
| `print/proxy/` | Elektronikken som volum (kort, tappar, knappar, SD-kort, brytar, USB-plugg), brukt i kontrollen |
| `print/kontroll.json` | Veggar, kollisjonar, monteringsbaner og haldarvariantar |
| `print/bambu/` | Profilane som vart brukte, og `slicing.json` med tid, vekt og innstillingar |
| `montering/` | Rettleiinga som PDF og éi PNG per side |
| `bilete/` | CMF-render og snitt gjennom linseaksen |
| `verktoy/` | Skripta som lagar alt over |

## Delar og prent

| Del | Retning på plata | Merknad |
| --- | --- | --- |
| kropp | Ståande, luka ned | Tre-støtte frå plata, gjennom luka og inn i holrommet. Ho kan takast ut gjennom luka. |
| luke | Innsida ned, så utsida blir rein | Fire magnetlommer |
| stabelhaldar | Som montert | Vel variant etter D |
| utløysar | Som montert, toppen opp | Limast på brytaren |
| usb-lokk | På sida | Tettar USB-tunnelen på hjulsida |

Innstillingar: Bambu PLA Basic, 0,4 mm dyse, 0,20 mm Standard, Textured PEI-plate, 3 veggar, 15 % fyll, tre-støtte berre frå plata. Slica med Bambu Studio 02.08.02.61 og dei offisielle P1S-profilane.

## Innkjøp

ESP32-CAM, ESP32-CAM-MB (micro-USB), microSD, 6 × 6 mm trykknapp, 8 magnetar Ø6 × 3 mm, 2 leidningar 26–30 AWG på om lag 15 cm, CA-lim, loddebolt, skyvelære og micro-USB-kabel.

## Monteringsrekkjefølgje

Rekkjefølgja er fast. Pila som går i ring viser når kroppen skal snuast.

1. Mål D og vel haldar. 2. Prent. 3. Lim fire magnetar i kroppen med same side ut. 4. Set kvar luke-magnet på motparten sin, lim og press luka på. La limet herde før luka blir opna. 5. Lodd leidningane til GND (pinne 2) og IO13 (pinne 4) på 5V-rekkja. 6. Set kameraet på MB, set i SD-kortet, last opp firmware og test. 7. Træ leidningane gjennom tunnelen og ut i knappebrønnen. 8. Lodd brytaren og lim han i lomma. 9. Senk stabelen inn gjennom luka og skyv han 17 mm fram til linsa. 10. Haldaren. 11. Luka. 12. Utløysaren. 13. USB-kabel og USB-lokk.

## Kontroll

Kontrollen køyrer med nominelle mål for elektronikken. Dei er henta frå databladet og målingar andre har publisert, ikkje frå dine kort.

| Kontroll | Resultat |
| --- | --- |
| Alle fem delane | Manifold, éin lekam kvar |
| Tynnaste vegg | 2,37 mm (USB-tunnel). Brytarlomma 2,52, rom A 2,93, SD-spor 4,88 |
| Luka | Minst 2,63 mm tjukk |
| Kollisjonar mellom delar og elektronikk | 0 mm³ |
| Monteringsbaner: stabel opp gjennom luka, 17,55 mm fram, haldar opp bak | 0 mm³ kollisjon, med SD-kortet i |
| Klaring stabel mot kropp og haldar | 0,10 og 0,25 mm |
| Haldarvariantar D14,0–D18,0 | 0 mm³ mot kroppen |

Endringar frå den arkiverte A3-versjonen:
- Luka har 0,2 mm klaring og eit neglehakk.
- MB-knappane har spor.
- Haldaren har klaring mot kroppen.
- Kamerahøgda og linsekonusen følgjer målingane.
- USB-tunnelen og pluggen var snudde 90°. Det er retta.
- Brytarlomma er flytta slik at veggen er over 2 mm.
- Det er lagt til eit spor for SD-kortet, som stikk ut frå kortet.

## Kjende avgrensingar

- **Fysisk passform er ikkje prøvd.** Mål D før prent. Prøv stabelen i kroppen før du limer noko.
- **Utløysaren krev kode.** Kameraet tek bilete når IO13 blir kopla til GND. SD-kortet må då køyre i 1-bit-modus (`SD_MMC.begin("/sdcard", true)`). Ikkje hald knappen inne medan kortet startar. Firmware følgjer ikkje med. Bruk CameraWebServer-eksempelet til å teste kameraet.
- **SD-kortet kan ikkje takast ut** etter montering. Bilete blir henta via USB eller wifi.
- **USB-C-porten på grepet er berre form.** Straum og data går gjennom micro-USB-porten på MB, via tunnelen på hjulsida.
- `gcode.3mf` har ikkje miniatyrbilete, fordi slicinga køyrde utan skjermkort. Det påverkar ikkje prentinga.

## Regenerering

```bash
cd verktoy
npm install
python3 lag_delar.py      # delar, proxyar, haldarvariantar, kontroll.json
python3 print_plate.py    # prentretning og 3MF
bash bambu_slice.sh       # Bambu Studio CLI (Flathub), P1S-prosjekt og gcode.3mf
python3 cmf_overfor.py    # fargar frå PBR-teksturen til delane (print/cmf, ikkje i git)
python3 vis.py            # bilete/
python3 ikea.py           # montering/
```

Mål og plasseringar ligg i `verktoy/delar_konfig.json`. Kjelda er `arkiv/entropi-a3/03-3d/a3-entropi-print-120mm.stl`.
