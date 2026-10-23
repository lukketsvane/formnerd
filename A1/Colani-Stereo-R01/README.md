# FormNerd · Colani Stereo · Tripo R01

**Status:** Faktisk Tripo-baserte formmodellar er ferdige og eksporterte. Ikkje mekanisk produksjonsklar. Dette er ein ny Tripo-grein, ikkje same geometri som den tidlegare parametriske R05.

## Kjelda og modellkøyring

Referanse: foto av Canon Colani-kameraet, originalbilete brukt i Tripo Studio, med kjelde `https://images.navigart.fr/1000/4N/43/4N43150.jpg`. Fotografi og opphavleg design er tredjepartsmateriale, ikkje eit nytt originaldesign.

Tripo Studio, 23. oktober 2026:

| Trinn | Utført og verifisert |
| --- | --- |
| H3.1 Best Quality image-to-3D | 55 kredittar, detaljert teksturert GLB, 1 958 283 trekantar, 61 702 316 byte |
| Smart Mesh P1.0 retopologi | 40 kredittar, quad-topologi med 10 000 target |
| Native FBX-mesh frå Tripo | 9 750 flater: 8 834 quads + 916 trekantar, 9 312 hjørne |
| Nedlasta GLB | 18 584 triangulerte flater og 5 220 924 byte |
| Sum | **95 Studio-kredittar** |

Tripo Workspace: https://studio.tripo3d.ai/workspace/retopology/7fe16741-5e00-44ed-9210-318d7989ab35

## Filer

- [H3.1 master](tripo/Colani_Lady_Tripo_H31_Master.glb) – original 3D-form, teksturert og uendra
- [Tripo Smart Mesh, GLB](tripo/Colani_Lady_Tripo_SmartMesh_10k_Quad.glb) – avleidd lett mesh med triangulert quad-topologi
- [Tripo Smart Mesh, original FBX med teksturar](tripo/Colani_Lady_Tripo_SmartMesh_Quad_FBX_and_textures.zip) – **brukt når ekte quad-topologi trengst**
- [Redigerbar Blender-scene](tripo/Colani_Lady_Quad_Cage_Edit.blend) – quad-grunnlag for manuell SubD-/overflateretning, ikkje native NURBS eller mekanisk BRep
- [Tripo 3/4-view](preview/01_Tripo_3quarter_frontA.png), [frontriss](preview/03_Tripo_frontA.png), [profil](preview/05_Tripo_side.png)
- [Faktisk meshkontroll](tripo/lowpoly_mesh_qa.json) og [FBX-topologikontroll](tripo/fbx/qa_fbx_quads.json).

## Engineering-kontroll

**FAIL / prototypestadium.** Den originale quad-FBX har 98 opne kantar og 3 ekstra ikkje-manifolde kantar (101 totalt). GLB-en har UV-duplikat som kan sveises; etter sveising står dei same 98+3 feilane att. Ho er difor ikkje vasstett. Avleidd reparasjonsarbeid må vurderast for topologiske og visuelle endringar før det kan brukast i konstruksjonen. Sjølv lukka mesh ville ikkje åleine stadfeste monterbarheit, materialtjukkleik, toleransar eller funksjon.

Den genererte forma har **ikkje dokumentert mm-skala**. Berekna ytre mål, kollisjonar eller radier frå Tripo aleine må ikkje presenterast som målte fysiske delar.

Teknisk må vidare konstruksjon romme Linocell-powerbank 94 × 62 × 15 mm, to ESP32-CAM-modular og to optiske opningar med stereobase som kan målast. ESP32-CAM-MB-programmeringsmodulane bør ikkje stå permanent i det tronge kamerahuset. USB-A og USB-C må få separate reelle opningar i sideveggen, og powerbanken må vere uttakbar. Lengd på reelle pluggkontaktar, leidning, brytar og optisk modul må målast fysisk.

## Industridesign-kontroll

**PASS som formreferanse, IKKJE som ferdig produkt.** Ekte Tripo-overflate tek vare på bølgjene, den ujamne visuelle vekta og den asymmetriske Colani-silhuetten som var borte i tidlegare R05. Genereringa har samstundes teke med tilfeldig tekstrelieff, optiske artefaktar, merkeelement, knapperelieff og AI-generert skjult geometri. Desse må formgivast om til eigne produksjonsflater. Den ikkje-symmetriske originalforma må tilpassast ei ny ekte stereokamera-konstruksjon og konseptet entropi.

### Rett vidare flyt

1. Bevar master og quad-FBX uendra som designkjelde.
2. Rydd topologi i **eigen avleidd kopi**, kontroller avvik mot master.
3. Rekonstruer velde framflater som G2-kontinuerlege CAD-/NURBS-flater eller bruk dokumentert SubD-meshhybrid. Quad-mesh er ikkje automatisk NURBS/STEP.
4. Bygg ei målsett mekanisk indre ramme og elektronikkmodell rundt dei faktiske komponentane.
5. Modellér front-/bakskal, begge linsehol, sideportar, låsing og knappen, kontroller veggar/kollisjonar/monteringsrekkje.
6. Først då: printprøve for powerbank og kamera, P1S slicing og IKEA-liknande rettleiing frå faktisk geometrisk samanstilling.

Ingen output i denne mappa er stadfesta som komplett montert stereokamera eller produksjonsgodkjend P1S-del.
