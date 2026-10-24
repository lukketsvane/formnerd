# ENTROPI · stereokamera · R08-MECH-01

Dette er mekanisk innmat til den valde kameraskissa, ikkje ei ferdig attgjeving av ytterskalet. Den eksterne forma i originalbiletet er låst som formkrav. Tidlegare R02–R07-frihandsmodellar er **ikkje** godkjende formmasterar.

## Innhald og status

| Leveranse | Status |
| --- | --- |
| Originalskisse og 768 × 768 Tripo-input | Klar, uendra motiv |
| Tripo H3.1 Ultra og seinare 20 000-trekantars kopi | Skript og dry-run klar, **ikkje køyrt**: kontoen manglar CLI-innlogging |
| 10 nominelle interne printdelar + 2 prøvebitar | Native, redigerbar CadQuery; STEP og STL eksportert |
| Innvendig STEP-assembly og STEP med elektronikkvolum | Eksportert |
| Kollisjonssjekk og STL-topologi | Bestått innanfor dei **nominelle voluma** |
| Bambu P1S | Tre 3MF-geometriplater, ikkje slicer-G-kode |
| Monteringsrettleiing | 13 A4-sider PDF + einskildsider og kjelde |
| Produksjonsskal, faktisk optikk, USB og fysisk passform | **Ikkje godkjende** |

## Komponentpakkingen

Koordinatar: X = tverrbreidd; Y = djupn, framside er negativ; Z = opp. Millimeter.

- Linocell 5000 mAh er representert som **94 × 62 × 15 mm**, orientert som X×Z×Y = 94×62×15. Bankens nominelle midtpunkt er `(−17.95, 14, 0)`.
- Portflata er ved `X = −64.95`. Den framtidige skalveggen har ei førebels innsida ved `X = −65.40`. Nominell avstand blir **0,45 mm**. T01 er ein isolert prøvebit med **berre hol gjennom 2,6 mm vegg**, ingen portbrønn.
- To AI-Thinker ESP32-CAM-kort, nominelt **27 × 40,5 mm**, er plasserte ved `X = 0` og `X = 43`, `Y = −8.2`, `Z = −5.4`. Lengder, kontaktar og faktisk USB-programmeringskort må kontrollerast. **ESP32-CAM-MB er ikkje i sluttkonstruksjonen**.
- Linsemidtpunkta ved `X = 10` og `X = 53` krev at OV2640-modulen blir flytta 10 mm sidevegs på flekskabelen. Sensorfleks og lengd er ikkje målt, og denne justeringa er ikkje godkjend.
- Powerbanken ligg bak elektronikken i staden for å auke breidda. USB-A og USB-C blir vende mot venstre sidevegg. Nominell 3D-ramme er **136 × 78 × 48 mm**; dette er berre ein komponentkonvolutt, **ikkje den endelege organisk forma**.

## Sentrale filer

- `reference/original_reference.jpg` er valt skisse; `reference/tripo_input_square.jpg` er same motiv sentrert på kvitt for Tripo.
- `RUN_TRIPO_R08.ps1` startar **ei** H3.1-køyring etter CLI-innlogging, deretter separat lågpoly-retopologi. Han blir ikkje køyrd før autentisering.
- `source/build_mechanics.py`, `source/parameters.json`: redigerbar mekanikk og mål.
- `R08_inner_assembly.step`, `R08_nominal_hardware.step`: delbar CAD og reference-envelopes.
- `step/`, `stl/`: individuelt namngjevne delar i montert koordinatsystem.
- `print/`: tre 3MF-plater innanfor 250 × 250 mm, ingen G-kode. Importer i Bambu Studio og vel korrekt P1S-, dyse- og filamentprofil.
- `review/`: 3D-bilete av faktisk innmat; delvis eksploderte visingar.
- `manual/ENTROPI_R08_innmat_monteringsrettleiing.pdf`: 13 sider svartstrekteikningar og prøveinstruksar; `manual/pages` inneheld kvar side som PNG.
- `verification/`: faktiske eksport- og kollisjonsrapportar.

## Test og grense for godkjenning

1. Skriv ut T01 og T02 før andre delar. Kontroller powerbankens faktiske kantprofil, begge USB-portposisjonar, PCB-tykkleik, breidd og linsekrage.
2. Opne det slica innhaldet i Bambu Studio; kontroller støtte, brobygging og verktøybaner. Verktøybanekontroll er **ikkje** utført for R08.
3. Monter korta utan MB-programmeringskort og prøv 5 V-forsyning til begge. Powerbanken må ha ein trygg elektrisk fordelar som ikkje konfliktar med USB-veggen. USB-A ut og USB-C inn er ikkje internt tilkopla i denne CAD-en.
4. Godkjenn Tripo-master geometrisk mot originalskissa før han blir brukt som utvendig kropp. H3.1-mesh er ikkje automatisk NURBS eller presis CAD.
5. Bygg den endelege Tripo-tilpassa skalgeometrien med veggar, optiske seter, kopling mellom P01/P02 og bakdeksel. Kontroller alle uttaksbaner, fysiske trykk- og låsetestar.

**Konklusjon:** Dette er ein digitalt kontrollert *mekanisk delpakke*, ikkje ein produksjonsfrigjeven, fullt fungerande kamerakonstruksjon.