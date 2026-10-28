# Utgåve 07: kortare og meir visuell manual

## Faktisk undersøkt

Lesne kjelder: `referansar/ikea-manualar/utval/UTVAL.md` og `rangering.json`. Desse vart brukte som utvalshjelp, ikkje som erstatning for å sjå PDF-ane. Tolv sider frå tre lokale IKEA-PDF-ar vart rasteriserte og vurderte kvar for seg. Sidenummer nedanfor er fysiske PDF-sidenummer, og samsvarer med trykte sidetal der slike står.

| Referanse | Observerte sider | Konkret grep som kan overførast |
|---|---|---|
| MILSBO, AA-2094158-9 | 1 | Eitt stort produktnamn, éin ferdig produktfigur, svært lite anna. Ingen innhaldsoversikt eller teknisk ingress på framsida. |
| MILSBO | 7 | Beslag er identifiserte med form, delnummer og stor mengd. Klare rader og mykje luft. Lite behov for tabelltekst. |
| MILSBO | 11, steg 6 | Eit lite, komplett oversiktsobjekt nedst og to store detaljbobler over. Leiarane peikar på dei faktiske to festepunkta. Rørsle og verktøy er viste inne i detaljen, ikkje forklarte i eit avsnitt. |
| MILSBO | 16, steg 13 | Ei lita vendingsfigur viser ny synsretning før hovudhandlinga. Presise innfelte detaljar og korte piler viser tilgang, støtte og kontakt. Åtvaringane ligg ved risikopunktet. |
| MOSSJÖN, AA-2390862-4 | 6 | Ein komplett beslagsoversikt med nøyaktige variantformer, ID og mengd. Verktøy er viste i same system, utan eigen tekstside. |
| MOSSJÖN | 10, steg 4 og 5 | To påfølgjande handlingar på same side, same kamera og same rammeposisjon. Først delar på plass, så låsing. Store detaljbobler og eit eksplisitt rett/feil beslagpar gjer skilnaden klar. |
| MOSSJÖN | 12, steg 7 og 8 | To festesteg deler ei side. Ramma held orienteringa. Verktøy- og beslagdetaljane står ved bruksstaden; mengd er eit kort 2x. |
| MOSSJÖN | 19, steg 20 og 21 | Innsetjing og etterfølgjande festing står over kvarandre. Éi tjukk rørslepil har éi retning. Smådelane blir forklara i ei enkel forstørring. |
| TARVA, AA-2440493-1 | 3 | Verktøy og relevant arbeidsmåte blir viste kompakt; støtte og rett arbeidsstilling blir forklara visuelt. Ikkje overfør uvedkomande møbel- eller veggfestevarsel til kamerariggen. |
| TARVA | 5 | Dei små delane er grupperte i éi avgrensa sone. Repetisjon blir uttrykt med mengder, ikkje med fire/fem nesten like sider. |
| TARVA | 29, steg 35 og 36 | Parallelle variantar blir viste i kolonnar med same kameravinkel og nummererte handlingar. Ei detaljrute er berre brukt der kontaktflata treng forklaring. |
| TARVA | 30, steg 37 | Det er lov å la mykje av sida vere kvit når éi oversikt og éin detalj gjer handlinga klar. Lite tekst og få grafiske nivå. |

## Kvifor utgåve 06 kjennest lengre enn ho treng

26-siders manualen er korrekt og lettleseleg, men han har katalogrytme: stor overskrift, seksjonsnamn, undertittel, hovudfigur, grå biletekst, handlingsoverskrift, forklaringsavsnitt, ofte ei ekstra påminning og gjenteken topp-/botntekst. Det gir mange ord rundt ei ganske enkel handtering. Mange sider brukar full side til eitt av to nesten identiske låsesteg. Dei store CAM- og MB-produktbileta fungerer som ein presentasjon, men dei lærer ikkje kvar for seg meir montering enn ei felles maskinvare- og orienteringsside ville gjort.

## Kutt og slå saman

1. Ta vekk den eigne innhaldsoversikta på side 2. Ein 16-18-siders visuell manual med store stegnummer treng ikkje seks siderangar før start. Flytt berre venstre/høgre-definisjonen og totaldelstala til deleoversikta.
2. Slå saman CAM- og MB-identifikasjon, no side 5 og 6, og orienteringa på side 9 i éi maskinvareside. Vis dei to verkelege modulstablane med rett 180-graders forhold; eit lite MB-utsnitt ved sida forklarer USB-basen. Bevar hovudregelen om parallelle linseaksar og 18-graders rull, men ikkje gi alle komponentane ei eiga tabellrad.
3. Bevar to oversiktlege deleoversikter: nye R04-delar og delar frå R03. Store 1x/2x/4x/8x og korte ID-ar ved faktiske delrendringar erstattar mykje forklaring. R04 inneheld tre nye hovuddelar pluss åtte kilar; dette må ikkje komprimerast til eit uriktig tre-dels produkt.
4. Slå saman kvar pinne-/kileparet: side 12+13, 15+16 og 20+21. Bruk to tydeleg nummererte underhandlingar på same side. Pinnen inn først, kilen inn etterpå. Det er tre kompakte låsesider, ikkje seks.
5. Slå saman USB og open kameratest, side 17+18. Stor baksidefigur, éin kontaktaksepil ved kvar plugg, tre korte kontrollar: begge bilete stabile, ingen kabelpress, rett orientering. Dette er framleis eit kontrollpunkt før den valfrie bakramma.
6. Slå saman service og feilsøking, side 23+24. Vis kile ut før pinne ut; legg fire korte avvikspunkt i ei smal nedre sone. Bevar støtte av elektronikken og stans dersom eit kort ikkje kan takast fritt ut.
7. Ta bort heilsideoversikta over førre printjobb på side 25. Gul PLA, AMS-val og tidlegare jobbhistorikk forklarer ikkje montering. Bevar dette i README/printdokumentasjonen, og lenk dit frå ei kort kjeldenote.
8. Flytt teknisk proveniens og komplette nominelle mål frå side 26 til kjeldepakken/README. I PDF-en er det nok med revisjon, kjeldelenkje og ei kort setning om at modellen er nominell. Ikkje gjenta "ekte Blender", "ikkje biletegenerering" og "komponenthøgder er nominelle" på fleire sider.
9. Bevar den konkrete PCB-innføringsporten. Han kan ikkje fjernast som overflødig tekst, og han skal ikkje skjulast i sluttvedlegget. Éi roleg side med sluttposisjon, tydeleg stopptekst og ingen falsk innføringspil er nødvendig.

## Tilrådd 17-siders følgje

1. **ENTROPI R04**. Eitt stort, realistisk produktbilete i matt svart/grått. Lita linje: "Montering / USB18". Kort merknad viser til passformkontrollen.
2. **Nye delar**. 02, 03, 04 og 8 korte kilar. Form, ID, mengd. 11 nye delar.
3. **Bruk om att**. 05/06, åtte kamera-T-pinnar og valfri 01+fire ramme-T-pinnar+fire lange kilar. Marker den valfrie gruppa samla. Total21/30.
4. **Maskinvare og retning**. To riktige ESP32-stablar, same låste frontkamera; relevant MB-/USB-detalj, 180° forskjell, same18° rull. Ingen unødvendig komponentkatalog.
5. **Klargjer**. Kort/lang kile i same målestokk og riktig mengd. Fjern støtter, kople frå og prøv lås utan kraft.
6. **Oversikt**. Explodert, avgrensa separasjon med tre direkte ID-grupper. Merk at avstandane forklarer delsamanheng, ikkje PCB-innføringsveg.
7. **Passform før montering**. Bevar faktisk stoppunkt og korrekt sluttposisjon. Ikkje teikn eit ubrukt alternativt innføringsløp.
8. **1 / Bakhaldarar**. Begge inn frå baksida, med elektronikken synleg nok til at støttepunktet kan forståast. Resten av delane ute av vegen.
9. **2 / Lås bakhaldarane**. Éi oversikt + to store lokale detaljar: pinne, så kort kile. 4x.
10. **3 / Linsebøylar**. Begge ned mot faktiske stopparar. Detalj av sensorens stive skulder, fri linse og fleks.
11. **4 / Lås linsebøylane**. Same visuelle språk som side9: pinne, så kort kile. 4x.
12. **5 / USB og test**. Faktisk bakside, rette pluggaksar, kabelfrigang, kort open funksjonsprøve.
13. **6 / Valfri batteriramme**. Banken korrekt i ramma, portopning og frie kablar. Ikkje utelat akkurat banken når handlinga handlar om å plassere han.
14. **7 / Lås batteriramma**. Pinne, så lang16mm-kile. 4x. Lokal detalj viser det faktiske tverrsporet.
15. **Kontroller**. Eitt stort ferdigbilete og ei svært kort fysisk sjekkliste. Kamera-only8+8; med ramme12+12. Bevar tomt felt for dato/avvik.
16. **Opne / feil**. Kile ut først, pinne etterpå, støtt delane. Korte konkrete stopp-/feilpunkt.
17. **Bakside**. Ferdig produkt frå ei nyttig, anna faktisk vinkel. Revisjon, to kjeldelenkjer, ei linje om gjenståande fysisk passform. Ingen ny teknisk rapport.

Alternativt kan side17 vere ei kort, visuell referanseside med 9,5/16mm og 76,326mm om desse ikkje er tydelege tidlegare. Ikkje fyll ei side berre for å nå eit bestemt tal.

## Presise visuelle endringar

- **Eitt tyngdepunkt:** eit stort stegnummer er nok. Reduser seksjonsnamn, lange titlar og gjentekne undertitlar. MOSSJÖN10/12 og MILSBO11 viser dette direkte.
- **Lås kamera og skala:** bruk same grunnkamera for keepers/keeperlocks og same for yokes/yokelocks. Ved baksidevising, legg inn ei lita vendingsmarkering eller skriv berre "Bakside"; MILSBO16 gjer vendinga eksplisitt.
- **Knytt detalj til stad:** ikkje la eit avkutta låseutsnitt flyte åleine. Set ei lita heilrigg ved sida av eller under, ring inn det relevante festet, og trekk éin leiar til detaljen. MILSBO11 er best referanse. Utsnitt må vise den rette kontakten og sporet; ikkje velje kameravinkel berre fordi han er dekorativ.
- **Handling før estetikk:** rørslepila skal ende ved det faktiske grensesnittet. Bruk tjukk, kort pil med éi retning. Følg MOSSJÖN19. Ingen pil over PCB som impliserer eit kontrollert innføringsløp.
- **Éi montasjeflate, få detaljar:** detaljert PCB er nyttig for orientering, men heile elektronikken treng ikkje vere synleg i alle låsebileta. Skjul berre det som faktisk skuggar for kontakten; merk dette kort éin gong.
- **Meir realistisk gjennom faktisk form:** bevar modellerte metallkontaktar, orange fleks, svart PCB, komponenthøgder og korrekt venstre/høgre. Bevar alle printdelar og deira faktiske kontaktgeometri. Bruk matte nøytrale husmateriale og lite blanke plastflater. Ikkje pynt med nye skruar, kabelfeste eller alternative linsehus.
- **IKEA og realisme kan kombinerast:** produktframside og maskinvare er materialrendringar; presise inngrep kan vere modellavleidd kontur/lys grå flate med svart kant. Same geometri, kamera og del-ID held språkforma saman. Ikke bland rein fargerender og tynn vektor tilfeldig side for side.
- **Lesbare materialar:** dei nesten kvite, blanke delane i utgåve06 si eksplodering er for nær kvit bakgrunn til å vere sterke tekniske figurar. Litt mørkare matt grått med konturlinje vil skilje armane betre. Hald rein kvit bakgrunn og ingen golvskugge.
- **Riktig kontrastprioritet:** svart pil/nummer, mørk hovudkontur, lettare detaljkant. Ingen dekorativ skugge, tabellstrekar eller kortboksar når ingenting treng avgrensing.
- **Repetisjon med mengder:** to haldarar, fire låsar eller åtte kilar blir uttrykt med 2x/4x/8x ved handlinga. TARVA29 viser repetisjon utan fire forklaringsavsnitt. Venstre/høgre må likevel vere visuelt rette, ikkje falskt spegla.

## Grenser som framleis gjeld

Endre ikkje CAD for å få ei penare teikning. Lang og kort kile må vere dei faktiske delane. Dei integrerte padane rører sensorskuldrene, men skal ikkje tvinge linsa/fleksen ned. Begge keepers må inn før yokes, pins, wedges, cables eller bank. Innføringsvegen for PCB er framleis uavklart. Ingen fysisk passform eller fullført utskrift kan påståast fordi manualen er kortare eller realistisk rendra.

Dette er stil- og strukturreferanse. Ikkje kopier IKEA-logo, figurar, verktøyteikningar eller sidegrafikk inn i ENTROPI-manualen.
