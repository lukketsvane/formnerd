# ENTROPI R10 · ytre hus og integrert innmat

**Status: digital mekanisk prototype. Ikkje produksjonsfrigjeven eller fysisk prøvd.**

Denne revisjonen byggjer vidare på den faktisk genererte Tripo H3.1-forma i `A1/stereo-tripo-R09` og den kompakte H02-innmaten. Originalfotoet ligg i `../reference/TRIPO_R09_SELECTED_REFERENCE.jpg`. Ingen ny generativ form er erstatta med ein annan designvariant.

## Kva som er laga

| Del | Format | Tal |
| --- | --- | --- |
| P01 framhus, glatta og reinskorne klaringar | STL mesh | 1 |
| P02 bakhus | STL mesh | 1 |
| H11 eksisterande dobbelt ESP32-CAM-MB-chassis | STEP og STL i `../harness/` | 1 |
| H12 ny sentrert batteriramme | STEP og STL | 1 |
| P03 linsekrage venstre og høgre | STEP og STL | 2 |
| P04 utløysarhette | STEP og STL | 1 |
| P05 separate M3-avstandshylser | STEP og STL | 8 |
| T11 og T12 frå H02, T13 USB-veggmal | STL/STEP | 3 |

Det er òg laga `R10_hybrid_assembly.glb` med delane i monterte nominelle posisjonar, `R10_analytic_inserts.step` berre med faktiske analytiske CAD-solidar, åtte CAD-rendringar og tre printplater i 3MF.

Ytterskalet er ein **Tripo-avleidd triangulert mesh**, ikkje automatisk presis NURBS. STEP-fila representerer mekaniske innsatsar, ikkje eit falskt konvertert STEP-ytterskal.

## Komponentpakking

Powerbanken er Linocell 5000 mAh, nominelt 94 × 62 × 15 mm. Ny batterisenter X=3,6 mm, flytta 20,5 mm frå H02-plasseringa som gjekk utanfor skalet. To ESP32-CAM-MB-stablar er framleis representerte med antatt totaldjupn 20,5 mm, og optiske senter har nominell baselinje 76,326 mm.

USB-A og USB-C har to separate hol direkte i sideveggen, utan nokon pluggbrønn. Teoretisk avstand frå bankens ytterkant til planlagt vegg er 0,45 mm. **0,52 mm CAD-voxeloppløysing kan ikkje verifisere ein klaring på 0,45 mm**, og USB-portkoordinatar, kabel og pluggkropp er ikkje målte. Prøv T13 før print av skalet.

## Digitale kontrollar

- `qa/R10_geometry_report.json`: originale skal og kameravolum
- `qa/finish_clearance.json`: glatt Taubin-overflate lét att volumoverlapping og vart avvist
- `qa/clearance_restoration.json`: korrigerte, glatta og reinskorne skal gav 0 voxeloverlapping mot elektronikk og haldarar, og er lukka STL-mesh
- `qa/fitting_spacers.json`: P05/T13 er gyldige STEP-solidar og vassfaste STL
- `qa/print_plates.json`: P1S-plater og 3MF-filinventar

Digital passform er prøvd med nominelle volum, ikkje med fysisk målte kretskort, portplasseringar eller kablar. Følgjande manglar framleis produksjonsfrigjeving: optisk akse og fokus, mekanisk kortlåsing, skrueinngrep, straumdeling frå USB-A, USB-C-kabeltilgang og fysisk montasje.

## Bambu P1S

`print/00_R10_fit_tests_P1S.3mf`: tre passformprøver, skal fyrst. 
`print/01_R10_Tripo_shells_P1S.3mf`: fram- og bakskal, er **berre 3MF-geometri**, ikkje maskinslica G-kode.
`print/02_R10_mechanics_P1S.3mf`: mekanikk og innsatsar, **berre 3MF-geometri**, ikkje maskinslica G-kode.

Kontroller fysisk batteri- og kretskortpassform med testdelane, bruk P1S 0,4 mm-dyse med korrekt filamentprofil, vurder støtte, brim og verktøybaner, og mål kontaktposisjonar før du lagar endelege hol. Ingen ny fysisk utskrift eller godkjend slicing av R10 er stadfesta.

## Kjelder og regenerering

`build_r10.py` byggjer skalet frå `../cad/outer_volume_grid.npz`; kjelda er Tripo H3.1-flata. `smooth_shell.py` lagar glattere mesh, men **ikkje bruk desse direkte** fordi dei hadde volumoverlapping. `restore_clearance.py` skjer maskinvarevoluma frå den glatta geometrien. `build_fittings.py` lagar P05 og T13. `render_r10.py` lagar åtte separate bilete frå faktisk geometri. `package_r10.py` byggjer 3MF og hybridmodellar. Rekkefølgja er:
`build_r10.py → smooth_shell.py → restore_clearance.py → build_fittings.py → package_r10.py → render_r10.py` (med `R10_SMOOTH=CLEAR` for siste rendring).

Fysiske mål, låsing og rettleiing må reviderast etter fysisk dry-fit. Fram til det er R10 ei eksplisitt merka prøvebygging.
