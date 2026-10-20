# ENTROPI · CAD v05

Detaljert, demonterbar kameramodell etter den valde referansen. Fem breie ribber, synleg samanhengande botnboge mellom ribbeføtene, avrunda frontring, mørk kropp og integrert utløysar. Alle mål er i millimeter.

## Opne desse filene

- `Entropi-assembly-v05.step`: samanstilling med 18 separate, namngjevne CAD-delar.
- `Entropi-assembly-v05.glb`: farga visningsmodell i korrekt meterskala.
- `parts/`: STEP og STL i samanstillingsposisjon, for vidare CAD-arbeid.
- `print/stl/`: dei 20 delane orienterte kvar for seg med botnen på Z = 0. Bruk desse ved individuell utskrift.
- `print/plate_*.3mf`: delar fordelte på plater innanfor 250 × 250 mm, med avstand mellom delane. Opne i Bambu Studio og vel P1S, faktisk dyse og filament.
- `print/print_manifest.json`: orientering, mål, klaringar på platene og støttebehov.
- `preview/`: sju separate visningar av den faktiske CAD-geometrien.
- `cad/`: redigerbar CadQuery-kjelde, parameterfil og faktiske kontrollrapportar.
- `cad/design_review.md`: kritikk og grunngjeving av endringane, knytt til dei fire FormNerd-dokumenta.
- `reference_hardware/`: nominelt PCB og førebels MB-volum som målreferansar.

3MF-filene inneheld geometri og plassering. Støtter, filamentprofil og G-kode blir laga i sliceren.

## Modelldetaljar i v05

Dei grøne markeringane i `reference/detail-markup.png` er grunnlaget for v05. Ribbene er bundne saman av ein synleg, samanhengande botnboge med avrunda endar og fire avrunda rot-overgangar. Dei tre oppovervende stubbeflatene bak ribbeføtene er fjerna. Porten har ei 13,6 × 9 mm tilgangsbrønn med 0,45 mm avrunda leppe. Knappefestet har ei lokal avrunding mot grepet. Overgangane frå ribbefanen og ytterbogen til frontringen er avrunda i sjølve CAD-geometrien.

`cad/form_refinements.py` utfører endringane etter den mekaniske grunnmodellen. Kvart steg blir skrive til STEP og lese inn att. `cad/form_refinement_report.json` registrerer dei faktisk utførte stega og kontrollerer at dei tre stubbeflatene er borte.

Utløysaren har 1 mm slag, nedstopp mot skuldra og oppstopp mot sikringspinnen. Ein utskiftbar, prenta fjørkassett returnerer knappen. Pinnen blir ført inn bakfrå og har splitta låseende og uttrekksflik. Nominell pinne er Ø1,8 mm med 0,3 mm diametral klaring. Ei nominell brytarvugge ligg under fjøra. Ei avtakbar lys grå serviceplate dekkjer tilgangsopninga bak knappen.

Kameraet får ei todelt klemme for nominelt Ø8 mm linsehus, med 2,8 mm aksial justering. I/O-plata har kortvugge, skruklemme og spor for kabelavlasting. Kortvugga er førebels dimensjonert for eit USB-kort på 14 × 16 × 1,6 mm. I/O-plata er utvida til 27,4 mm, og skruefesta har 23 mm avstand slik at dei ligg utanfor pluggbanen. Ei nominell plugghylse på 12 × 7 mm og ein metallende på 8,8 × 3 mm blir prøvde med eit 30 mm kontinuerleg innføringsvolum. Dei faktiske kabel- og kontaktmåla er ikkje målte.

Det øvre høgre festet for korthaldaren er flytta slik at det ikkje stengjer skruen mellom ribbebur og chassis. Dei to festehola i I/O-plata går no heilt gjennom.

## Prent først

Prent `11_fit_coupon` og `16_shutter_calibration` før hovuddelane. Nummer 11 prøver M2-hol og PCB-spor. Nummer 16 prøver pinne-/holpassing og ein 0,8 mm fjørseksjon. Bruk same filament og dyse som i dei endelege delane.

Startpunkt for PLA: 0,4 mm dyse, 0,16 mm lag, fire veggar, fem topp- og botnlag og 15 % gyroid. Kontroller oppskorne baner før utskrift.

- Ribbebur: frontringen ned. Støtte frå byggeplata under ribber og grep; kontroller at støtta kan fjernast gjennom dei opne felta.
- Chassis: fronten ned og bakopninga opp. Kontroller støtter under innvendige skruestolpar og bruer.
- Baklokk: utsida ned og lokaliseringskanten opp.
- Fjør 15: den flate sida som opphavleg har Xmax = −65,4, ligg ned. Lengd og bøying ligg i lagplanet. Denne orienteringa er lagt inn i prentfilene.
- Sikringspinne 08: akslingen ligg i lagplanet. Bruk ei lita, avtakbar brim dersom kontaktflata krev det. Hald spalta fri.
- Dei andre delane: bruk orienteringa i `print/stl/` og sjå støttemerknaden i manifestet.

Det er sett av plass til maksimalt 3,5 mm brim mellom delane på dei ferdige platene. Større brim eller endra støtteoppsett kan krevje ny plassering.

## Montering

1. Prøv kupongane, avgrad hol og fjern støtter. Prøv skruar i plast før samanstilling. Ikkje lim delane.
2. Monter den faktiske brytaren i vugga dersom måla passar. Før fjørkassett 15 inn bakfrå til foten låser i sporet. Før knappen ned og sikringspinnen inn bakfrå. Kontroller retur og begge endestoppa før vidare montering. Monter serviceplate 20 med M2 × 6 etter prøving; ta henne av ved tilgang til pinne, brytar eller fjør.
3. Skru ribbeburet til chassis frå innsida. Dette blir gjort før korthaldaren blir montert.
4. Monter kameravugge 17 og klemme 18 på frontblende 06 utanfor huset. Legg linsehuset i klemma, juster aksialt og stram jamt. Før gruppa inn gjennom fronten og fest bakfrå i dei to øyra i kragen. Før flekskabelen fritt bakover.
5. For rein formmodell kan den store mørke senterpluggen 12 brukast. Før han inn frå framsida og fest skive 13 bak blenda med M2 × 4. Fjern 12 og 13 ved bruk av faktisk kamera.
6. Før det øvre hjulet ned frå utsida. Fest låseskive 14 på akslingen med M2 × 6 frå innsida. Hjulet er ein mekanisk formdetalj.
7. Før I/O-plate 10 inn gjennom bakopninga og skru henne til sidefesta før USB-kort og klemme 19 blir lagde på. Legg deretter kortet i vugga og monter klemme 19. Før kabelen gjennom avlastingsspora og fest utan å klemme leiarane. Prøv den faktiske USB-pluggen gjennom portbrønnen før vidare montering.
8. Før ESP32-kortet inn i spora i haldar 04 og monter toppklemme 05. Kople kamera/flekskabel til att dersom dei vart kopla frå. Kontroller at ingen komponent ligg mot klemme eller skruetupp.
9. Skru haldaren på dei fire stolpane. ESP32-CAM-MB skal kunne koplast frå og takast ut gjennom bakopninga.
10. Kontroller kabelslakk, knappeslag og tilgang til kontakt. Monter baklokket sist.

## Skruar

| Grensesnitt | Tal | Førebels skrue |
|---|---:|---|
| Ribbebur til chassis | 4 | M2 × 10 |
| Baklokk | 4 | M2 × 8 |
| Korthaldar til chassis | 4 | M2 × 10 |
| Kortklemme | 2 | M2 × 6 |
| Frontblende | 2 | M2 × 8 |
| I/O-plate | 2 | M2 × 6 |
| Øvre hjul | 1 | M2 × 6 |
| Valfri senterplugg | 1 | M2 × 4 |
| Kameravugge til blende | 2 | M2 × 6 |
| Delt kameraklemme | 2 | M2 × 8 |
| USB-kortklemme | 2 | M2 × 6 |
| Serviceplate bak knapp | 1 | M2 × 6 |

Pilothola er laga for utprøving av M2-skruar direkte i plast. Det er ikkje modellert metriske gjenger eller metallinnsatsar. Skruetype, hovudmål og faktisk inngrep må samsvare med det som er brukt i kontrollrapporten og prøvast i kupongen.

## Kontroll og målgrunnlag

`cad/export_verification.json` kontrollerer STEP-samanstilling, lukka GLB-nett og korrekt visningsskala. GLB-eksporten fjernar berre trekantar som får to nøyaktig like hjørne etter konvertering til 32-bits koordinatar. Native STEP og STL blir ikkje endra av dette.

`cad/verification_report.json` dekkjer native solid, STL-topologi, innbyrdes kollisjon og prøvd uttaksbane. `cad/shutter_verification.json` prøver fem slagposisjonar med bøygd fjørgeometri og begge mekaniske endestoppa. `cad/fastener_verification.json` kontrollerer dei modellerte skrueskafta og skruehovuda. `cad/usb_access_verification.json` prøver den nominelle pluggen mot alle prentdelane langs heile den rette innføringsbanen. `print/print_manifest.json` kontrollerer prentorientering, Z = 0 og plassering på platene. Les resultata i rapportane; ei kontrolliste er ikkje i seg sjølv eit pass.

ESP32-PCB på 27 × 40,5 mm, MB-volum, kamerahylse, brytar og USB-kort er nominelle eller førebelse mål. Den faktiske elektronikken er ikkje målt. Den berekna overflatetøyinga i fjøra ved 1 mm slag er om lag 0,65 %; dette er ei dimensjoneringsutrekning, ikkje ein utmattingstest. Den mørke Ø39,2 mm formpluggen er ikkje optikk. Batterilading, USB-biletoverføring, batterifeste, firmware og endeleg optikk er ikkje verifiserte av CAD-modellen.

## Endring og regenerering

Krev Python, CadQuery 2.7.0, NumPy, Pillow og VTK. Visningsskriptet krev ein C++-kompilator. CMF-materiala er definerte i `cad/cmf_materials.json` og skrivne inn som ikkje-metalliske PBR-materiale i GLB. Dette endrar ikkje STL-geometrien.

Køyr `python cad/build_assembly.py`, `python cad/verify_assembly.py --motion-step 2`, `python cad/verify_shutter.py`, `python cad/verify_fasteners.py`, `python cad/verify_usb_access.py`, `python cad/prepare_print.py`, `python cad/check_export_files.py` og `python cad/render_preview.py` frå denne mappa. Bygginga kan ta fleire minutt. Parameterverdiane ligg i `cad/parameters.json`; formkurvene ligg i byggjekjelda. Endringar krev ny kontroll og nye prentfiler.
