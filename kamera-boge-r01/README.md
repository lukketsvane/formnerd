# Kamera med boge

Mekanisk prøvebygg med CAD R01 og monteringsrettleiing M03. Førebels breidd er 145 mm. Ytterforma er mesh; STEP dekkjer P03, P04, P05 og T01. Faktisk elektronikk og maskinvare er ikkje målte.

## Start på Windows

Last ned eller synk heile denne mappa. Opne PowerShell i mappa og køyr:

```powershell
powershell -File .\Open-Print.ps1
```

To store 3MF-filer er delte i tapsfrie binære delar under `payloads/`, slik at kvar opplasting er innan transportgrensa. `large-files.json` har rekkjefølgje, storleik og SHA256 for delane og dei heile filene.

Skriptet kontrollerer filhashane, set saman dei to manglande 3MF-filene atomisk og opnar testplata i eksisterande Bambu Studio, eller i programmet som er knytt til 3MF. Det startar inga utskrift og installerer ingenting. Ei eksisterande heil fil med annan hash blir ikkje overskriven. For berre å setje saman og kontrollere filene kan du køyre `powershell -File .\Open-Print.ps1 -VerifyOnly`. Du kan òg opne testplata direkte i Bambu Studio.

1. Vel faktisk P1S, dyse, plate og PLA i sliceren. Førebels startgrunnlag er 0,4 mm dyse, 0,20 mm lag, tre veggar og 15 % gyroid.
2. `Plate-00-test.3mf` inneheld berre T01. Print passningsprøva først.
3. Opne knappen med `powershell -File .\Open-Print.ps1 -Plate Knapp`. Print P04 og prøv stammen i T01 sitt Ø16,4-hol. Prøv faktisk M3-mutter i AF5,9 og dei faktiske skruane i pilotane.
4. Når passningane fungerer, opne `-Plate Front` og deretter `-Plate Rest`. Kontroller alle lag, brim, støtte og korleis støtte kan fjernast frå bakopninga før utskrift.

Platefilene inneheld geometri, ikkje G-kode eller ein validert P1S-profil. Dei er ikkje slica eller fysisk prøvde. Fjørretur og slitestyrke må prøvast i den faktiske utskrifta.

## Filer

| Mappe eller fil | Innhald |
|---|---|
| `manual/Kamera-boge-M03.pdf` | 15 A4-sider med tekniske vektorfigurar frå uendra CAD |
| `manual/pages/` | Dei 15 sidene som separate PNG-bilete |
| `manual/Kamera-boge-M03-kjelder.zip` | Kjeldekode, SVG, kameraposar, skrifter og kontrollrapportar for manualen |
| `print/Plate-00-test.3mf` | T01-passningsprøve |
| `print/Plate-01-framhus.3mf` | P01, oppreist på ei 256 × 256 mm plate |
| `print/Plate-02-deksel-og-smadelar.3mf` | P02, P03, P04 og P05 |
| `print/*.stl` | Separate T01-, P03-, P04- og P05-filer i printorientering |
| `cad/assembled.3mf` | Full geometri for dei fem namngjevne delane P01 til P05 i CAD-koordinatar |
| `cad/*.step` | Analytisk mekanikk og passningsprøve |
| `cad/hardware/` | Nominelle illustrasjonsmodellar av skruar og mutrar, skal ikkje printast |
| `verification/` | Digitale geometri-, rørsle-, eksport- og dokumentkontrollar |
| `reference/sketch.png` | Opphavleg skisse |

Dei store STL-duplikata og rå Tripo-resultata er utelatne. Full P01- og P02-geometri er bevart i dei tapsfrie delane til `cad/assembled.3mf` og i dei respektive printplatene. Dei to genererte heile 3MF-filene er ignorerte av git og blir laga lokalt ved første opning. Assembly har millimeter som eining, direkte meshobjekt P01 til P05 og identitetstransformar.

Den første R01-verifikasjonen finn lukka mesh og prøvde, diskrete monteringsstillingar utan målbar kollisjon. Dette erstattar ikkje fysisk prøvebygg. Maskinvara er nominelt seks M3 × 12, fire M3-mutrar og tre M2,5 × 8. Stram varsamt i printa pilotar.

For å byggje manualen på nytt, pakk ut kjeldearkivet og følg README-en i arkivet. Ein fersk utpakking gav identisk tekst og identiske sidebilete på alle 15 sider utan CAD-program. For å kontrollere lagra filer og eventuelle samansette filer med Python kan du køyre `python source/verify_package.py`. Denne kontrollen endrar ingen filer.
