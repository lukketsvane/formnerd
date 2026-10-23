# ENTROPI · Tripo R08

Dette er den **faktiske Tripo-forma**, ikkje ei nyteikna etterlikning av referansebiletet. Hovudforma er bevart som original mesh. Mekaniske funksjonar er separate delar.

## Kjelde og geometri

- Detaljmaster: Tripo H3.1 image-to-model, task `8b601eb6-f627-4edb-aa2e-b9816c7271a2`.
- Smart Segment og Quick Cap: taskar dokumenterte i `A4/arkiv/tripo-a1/tripo-receipts.json`.
- Smart Retopology v3.0, 20 000 trekantar: task `4b23cc6d-7b12-4bf6-b415-3db38289b36f`, `A4/arkiv/tripo-a1/mesh/04-smart-retopology-preview.glb`.
- 11 separate Tripo-segment, i uendra relativ posisjon.
- Blender QuadriFlow har gitt 4 019 quads på ein kopi av Tripo-hovudforma. Gjennomsnittleg avstand frå input er 0,145 mm, p95 0,422 mm og maks 1,087 mm ved skala 112. Desse tala gjeld quad-meshen før SubD-utjamning.
- R08-huset brukar skala 118, med førebels ytre Tripo-omriss 117,8 × 87,8 × 61,2 mm.

## Opne modellane

- `Tripo_20k_master.blend`: original segmentert lågpoly frå Tripo.
- `Tripo_Quad_SubD.blend`: redigerbar QuadriFlow-/SubD-kopi av faktisk Tripo-hovudform.
- `ENTROPI_Tripo_hybrid_R08_CLOSEFIT.blend`: Tripo-ytterform, separat avrunda teknisk bakkloss og nominelle volum for ein powerbank og to ESP32-CAM.
- `ENTROPI_Tripo_hybrid_R08.blend`: første kassettstudie, AVVIST fordi utgravinga sletta eitt av Tripo-baksegmenta.
- `ENTROPI_Tripo_hybrid_R08_CLEARED.blend`: eksperiment med innvendig utsparing, AVVIST fordi for mykje av synleg Tripo-ribbevolum forsvann.

## Komponentpakking

- Linocell: oppgitt 94 × 62 × 15 mm.
- To ESP32-CAM: nominelle referansevolum 27 × 40,5 × 10,4 mm, ikkje eksakt elektronikkmodell.
- Kamerasenter: førebels 58 mm baselinje.
- Separat avrunda bakkloss: 101,4 × 70,8 × 46,5 mm, open framtil, nominell 2,5 mm minimumsvegg.
- Kollisjonskontroll mot bakklossen: 0 mm³ mellom bakklossen og batteri, PCB-referansar og to kortbrakettar.
- Kollisjonskontroll mellom bakkloss og skulpturell Tripo-form: **ikkje godkjend**. Samanføying, portutsparingar og synlege ribber må vidareutviklast utan å endre Tripo-silhuetten.

## Grense for denne revisjonen

**R08 er ein formrett, digital arbeidsmodell. Han er ikkje produksjonsklar og ikkje ferdig slica.** `print_candidates/` er geometrikandidatar, ikkje godkjende Bambu-plater. Faktiske kontaktmål, fysisk PCB-passform, linse/flekskabel, ladeportane, optisk synsfelt, skruar, samanføying og mekanisk styrke må prøvast.

Hald `Tripo_Quad_SubD.blend` som visuell master. Endre mekanikken separat. Ikkje erstatt Tripo-ytterforma med R07-kopien.

## Prosessbilete

- `render/01_three_quarter.png`: original Tripo-lowpoly.
- `render/09_Tripo_Quad_SubD.png`: nøyaktig quad-retopologisert hovuddel.
- `render/14_R08_Tripo_actual_with_close_cube.png`: original skulptur med kompakt bakdel.
- `render/17_battery_two_esp32_visible.png`: dei to kortvoluma og powerbank.
- `render/19_exploded_tripo_compact_assembly.png`: gruppevising i samanstilling.

Arbeidsskript og rapportar finst under `scripts/` og `qa/`.
