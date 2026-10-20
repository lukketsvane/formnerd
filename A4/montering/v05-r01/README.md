# Entropi v05 - mekanisk montering R01

[Opne monteringsrettleiinga](Entropi-v05-Montering-R01.pdf). 19 sider, eitt steg og éi isometrisk CAD-visning per side. [Enkeltbileta ligg her](pages/).

Rettleiinga bruker dei faktiske STL-delane i [CAD v05](../../Entropi-CAD-v05/). Snitta på side 4 og 5 og utsnittet på side 6 er berre illustrasjonsutsnitt. Dei endrar ikkje produksjonsfilene. Nye delar er grå; allereie monterte delar er lyse. Pilene viser nominell rørsleretning, ikkje ein sertifisert kollisjonsfri monteringsbane.

## Finn steget

| Side | Steg |
|---|---|
| [01](pages/step-01.png) | Start med delane |
| [02](pages/step-02.png) | Delnummer og skruar |
| [03](pages/step-03.png) | Prøv passingane først |
| [04](pages/step-04.png) | Før inn returfjøra |
| [05](pages/step-05.png) | Knapp og sikringspinne |
| [06](pages/step-06.png) | Lukk serviceluka |
| [07](pages/step-07.png) | Fest bur til chassis |
| [08](pages/step-08.png) | Bygg kameravugga ute |
| [09](pages/step-09.png) | Legg på kameraklemma |
| [10](pages/step-10.png) | Før inn optikkgruppa |
| [11](pages/step-11.png) | Valfri rein formmodell |
| [12](pages/step-12.png) | Monter det øvre hjulet |
| [13](pages/step-13.png) | Fest den tomme I/O-plata |
| [14](pages/step-14.png) | USB-feste er førebels |
| [15](pages/step-15.png) | Bygg korthaldaren ute |
| [16](pages/step-16.png) | Før inn korthaldaren |
| [17](pages/step-17.png) | Prøv før du lukkar |
| [18](pages/step-18.png) | Baklokket kjem sist |
| [19](pages/step-19.png) | Kva som faktisk er kontrollert |

## Avgrensingar

Dette er ei mekanisk monteringsrekkjefølgje, ikkje eit stadfesta bygg av fungerande kamera. Nominelle mål for kort, kamerahylse, USB-kort og brytar må kontrollerast mot maskinvara. Kjelda `Utstyret me har`, Iver Raknes Finne, 20. oktober 2026, side 1, oppgir ikkje desse måla. Fysisk passform, gjengestyrke, verktøytilkomst, fjørlevetid, optikk og elektrisk funksjon er ikkje verifiserte.

Side 11 er ei alternativ formmodellgrein, utan kamera. Side 14 gjeld eit førebels separat USB-kort, ikkje eit verifisert ESP32-CAM-MB-grensesnitt. Modellens 27 skruar inkluderer formpluggen; kameravarianten utan del 12 og 13 bruker 26, dersom den førebelse USB-klemma også blir brukt. Utan del 19 blir to M2 × 6 tekne ut av den nominelle lista.

## Kjelde og regenerering

[build_manual.py](build_manual.py) bruker `../../Entropi-CAD-v05/parts/*.stl` og v05 sin `render_preview.py`. [manual_manifest.json](manual_manifest.json) inneheld SHA256 for alle 20 kjeldedelane. [figures](figures/) inneheld CAD-bileta før PDF-piler og delnummer.

Frå denne mappa, med Python, NumPy, Pillow, VTK, ReportLab, DejaVu Sans, g++ og Poppler tilgjengeleg:

```bash
python build_manual.py
```

Berre bygg PDF og sidebilete på nytt frå dei lagra figurane:

```bash
python build_manual.py --reuse-figures
```

Oppdater utvalde CAD-figurar:

```bash
python build_manual.py --reuse-figures --refresh-figures 4 5 6
```
