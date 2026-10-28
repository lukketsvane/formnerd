# FormNerd Stereo R01

Mekanisk CAD-prøvebygg av den valde kameraskissa, med mjukt grep, to synlege frontlinser og utløysarknapp. Dette er den nye Stereo R01-forma, ikkje spiralmodellen eller det tidlegare rektangulære ESP32-huset.

Fullpakken `FormNerd-Stereo-R01-CAD.zip` inneheld kjelder, referansar og alle eksportar. Den mindre `FormNerd-Stereo-R01-print.zip` inneheld berre printfiler, manual og kontrollrapport for lokal slicing. Byggjekommandoane nedanfor krev fullpakken.

## Innhald

- `cad/assembly.glb`: samanstilt modell i millimeter, med kjøpt maskinvare som nominelle geometriomslag.
- `cad/assembly-manifest.json`: delnummer, mål, samanstillingskoordinatar, materialfargar og maskinvareliste.
- `cad/P*.step`: presise BRep-solidar for mekaniske delar. Dei organiske skala er mesh-basert hybrid-CAD og er ikkje omdøypte til falsk STEP.
- `cad/P*.stl`: kvar produktdel i felles samanstillingskoordinatar. P10 er passningsprøve.
- `print/`: printorienterte eksportar når tilgjengeleg. Ingen fil er ferdig slicad eller sendt til skrivar.
- `print/plates/`: tre 3MF-plater med faste delnamn og plasseringar. Prøveplata har P10, begge kragane og knappen. Dei to andre har frontskalet og bakskalet med beraren/haldelistene.
- `source/build.py`: parameterstyrt oppbygging av geometri og eksportar.
- `manual/`: monterings-PDF, ei PNG per side og kjeldekode for illustrasjonane.
- `verification/`: kontrollrapportar, krav og kjelder.
- `reference/`: vald skisse, uendra Tripo-resultat, transformasjon og dokumentert avleidd form.

## Presisjon og avgrensing

Referansebreidda 140 mm er eit designval, ikkje ei oppmåling. Tripo-forma har vore regularisert for å kunne brukast som lukka geometrisk kropp. Følg `verification/source-audit.json` og byggjerapportane for eksakt behandling.

ESP32-CAM-kortflata 27 × 40,5 mm er eit nominelt produsentmål. Eigne komponentar kan avvike. Full ESP32-CAM-MB-stabel, kontaktar, kameramodul, optisk senter, kabelbøy, brytar og batteri er ikkje målte. Beraren må ikkje tvingast på dei faktiske korta.

Denne modellen stadfestar ikkje USB-C-lading eller dataoverføring, utløysarfunksjon, stereosynkronisering, optisk kalibrering eller funksjonell elektronikk. Ei synleg linsekrage er ikkje sjølve optikken. Prosjektkravet om minst 30 mm faktisk linsediameter er framleis ope.

Digitale kollisjons- og topologikontrollar er avgrensa til dei representerte delane. Dei erstattar ikkje fysisk prøve, slicarkontroll, materialtest eller trygg elektrisk konstruksjon.

Sluttkontrollen omfattar ni STL-gjeninnlesingar og 18 monterings-/tilkomstvegar med 346 prøvde posisjonar. Ingen uventa kollisjon overstig rapportgrensa på 0,01 mm³. Dette er ikkje eit prov for alle kontinuerlege rørsler. Den organiske overflata har framleis synlege mesh-avleidde ujamnskapar og er ikkje godkjend som ferdig industriell overflate.

## Bygg på nytt

Python 3.12 og pakkane i `requirements.txt` er brukte i denne utgåva.

```bash
python source/build.py
python source/verify_independent.py
python source/export_print.py
python source/prepare_plates.py
python manual/make_plan.py
python manual/build_manual.py manual/plan.json
python source/render.py review/hero-scene.json review/hero.png
```

Køyr i ei arbeidskopi. Byggjeskriptet skriv på nytt filene i `cad/` og kontrollrapportane. Sjå også eventuelle separate kontroll- og printeksportskript i `source/`.

Manualfontane ligg i `manual/assets/fonts/` med lisens. Renderkommandoen tolkar relative delbanar frå prosjektrota; `--base` kan overstyre dette.

## Print og montering

Start med P10 og dei to linsekragane. Vel Bambu Lab P1S og den faktisk monterte dysa i Bambu Studio. Ein lokal operatør må velje materiale, støtte og orientering etter lagvis inspeksjon. Importer berre produktdelane frå `print/` eller `cad/P*.stl`, ikkje H- og N-filene for metallskruar og mutrar. All geometri er i mm; ikkje bruk automatisk skalering.

Printfilene er uslicade. Det ligg ikkje G-code, printerpålogging eller automatisert utskrift i denne pakken.

GitHub-mappe: `A1/Stereo-R01/`. Store referansefiler og eksportar kan liggje som tapsfrie bitar i `payloads/`. Køyr `python source/restore_payloads.py` først; skriptet kontrollerer SHA-256 og bevarer eksisterande filer som skil seg frå originalen. På Windows opnar `powershell -File .\Open-Print.ps1 -Plate Prove` prøveplata.
