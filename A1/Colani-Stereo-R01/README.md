# Colani Stereo R06 | Tripo-formgrunnlag

Status: Tripo H3.1-master og Tripo Smart Mesh Quad-retopologi er genererte. Berre digitalt formgrunnlag, ikkje produksjonsgodkjent.

## Faktiske genereringsfiler

- `tripo/Colani_Lady_Tripo_H31_Master.glb`: original, teksturert Tripo-master (61,7 MB), lagra lokalt på PC. H3.1 Best Quality, 55 Studio-kredittar, 1 958 283 trekantar.
- `tripo/Colani_Lady_Tripo_Retopo_10k.glb`: Tripo Smart Mesh Quad, mål 10 000; resultat 9 750 quads i Tripo UI. Eksportert GLB viser 18 584 trekantar.
- `tripo/Colani_Lady_Tripo_Retopo_10k_welded.glb`: Blender sveisa arbeidskopi utan materialteksturar.
- `tripo/welded_topology_qa.json`: topologikontroll. Det er att 98 opne kantar etter sveising; fila er førebels ikkje klar for printing.
- `tripo/shape_cross_sections.json`: rissbaserte grensar langs høgda til Tripo-lågpolymodellen.

Tripo-produktet er ikkje automatisk ein NURBS/BRep-solid. Bevar form-masteren; konstruer nøyaktige passflater, batterilomme, optiske hol, korthaldarar, skruar og USB-opningar separat. GLB-en har modellinterne einingar; mål i millimeter må fastsetjast eksplisitt etter komponentpakking.

## Mekanisk pakke som skal få plass

- Linocell 5000 mAh: 94 × 62 × 15 mm.
- To ESP32-CAM med OV2640, nominelt 27 × 40,5 mm PCB kvar, parallelle kameraaksar.
- ESP32-CAM-MB-brikka blir berre brukt til programmering, ikkje permanent montert.
- To optiske opningar og USB-C/USB-A frå sjølve powerbanken må integrerast, med dokumentert klaring.
- Print til Bambu Lab P1S må ha lukka skal, nøyaktige grensesnitt og verifisert slicing.

## Revisjonsportar

**Engineering:** Førebels ikkje bestått, opne mesh-kantar, elektronikk og port/ledning ikkje prøvde.

**Industridesign:** Tripo-masteren fangar hovudformene i originalfotoet, men det er framleis ikkje vist at den tekniske pakka kan plasserast utan å svekkje silhuetten. Overflata skal vurderast uavhengig av teknisk passform.

Arbeidsgrunnlag: foto av Canon Colani-referansen frå brukaren, tidlegare R05-konstruksjon og Tripo Studio-jobben `7fe16741-5e00-44ed-9210-318d7989ab35`.
