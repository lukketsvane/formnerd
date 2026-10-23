# ENTROPI R08, faktisk Tripo-geometri

## Kjelder

- Tripo H3.1: `A4/arkiv/tripo-a1/mesh/01-ultra-original.glb`.
- Smart Segment + Quick Cap: `03-quick-capped.glb`.
- Tripo v3.0 Smart Retopology: `04-smart-retopology-preview.glb`, 11 delar, om lag 20 000 trekantar.
- Blender QuadriFlow på ein kopi av Tripo-hovudforma: 4 019 quads, SubD i `Tripo_Quad_SubD.blend`.
- Tripo-master og segmentering er bevarte. Quad-mesh og mekanikk er etterbehandling, ikkje NURBS.

## Dimensjonering

- Ytre omriss frå Tripo ved vald skala: om lag 117,8 × 87,8 × 61,2 mm, inkludert skulpturelle ribber.
- Linocell 5000 mAh: 94 × 62 × 15 mm. Kjelde: Kjell & Company, artikkel 80205.
- 2 × ESP32-CAM: nominelt 27 × 40,5 × 10,4 mm keepout per kort; produsenten oppgir sjølve kortet til 27 × 40,5 × 4,5 mm. Den ekstra tjukkleiken er ein mekanisk føresetnad, ikkje produsentmål.
- To kamerasenter er lagde 58 mm frå kvarandre. Både kameraoptikk og flekskablar krev fysisk kontroll.

## Verifisert digitalt

- `ENTROPI_Tripo_hybrid_R08.blend`: 14 separate, lukka og manifold STL-delar.
- `qa/collisions.json`: 0 registrerte penetrasjonar i 78 prøvde par mellom Tripo-delar, innvendige haldarar og nominelle komponentvolum.
- Tripo-segmenta hadde 25 innbyrdes overlapp før samanslåing. Dei er ikkje inkluderte i talet på 78.
- `ENTROPI_Tripo_GROUPED_R08.blend`: første grupperingsforsøk vart AVVIST på grunn av fragmenterte og delvis ikkje-manifolde printdelar.
- `ENTROPI_Tripo_HEALED_R08.blend`: etter volumreparasjon er kvitt ribbeskal og svart bakhus kvar eitt lukka, samanhengande volum. Optikkgruppa har framleis to separate lukka volum og må delast eller festast mekanisk.

## Prentbar prøving

- `print_tests/00_FIT_COUPONS_P1S_GEOMETRY_ONLY.3mf` har to små delar: eit faktisk hjørnesnitt frå batterihaldaren og eit faktisk utsnitt av ESP32-festet.
- 3MF: 2 objekt, 934 trekantar, ZIP-integritet utan feil. STL-kupongane har 0 ikkje-manifolde kantar.
- Fila er sendt til Bambu Studio på CYGNUS, men slicing, støtte, materialprofil og fysisk utskrift er ikkje verifiserte.

## Ikkje godkjent for full produksjon

Dette er ei digital form- og fitstudie, ikkje ein endeleg produksjonsrevisjon. Manglar som skal løysast: fastsamanføying av ribbeskal og bakhus, lokk/innføringsveg, optiske sensorfeste, kortstraum, utløysar, målt plassering av USB-C og USB-A på powerbanken, mekanisk og fysisk passform, slicer-kontroll og toleranseprøve. Ikkje skriv ut heile kamerahuset som ferdig produkt på grunnlag av R08.

## Mappene

- `render/`: separate bilete frå faktisk Tripo/CAD.
- `scripts/`: redigerbar Blender-Python, med kjelde- og transformasjonsspor.
- `qa/`: maskinlesbare geometrirapportar.
- `print_candidates/`: individuelle STL før grupperingsprøva.
- `print_tests/`: små prøveutskrifter.