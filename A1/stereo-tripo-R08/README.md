# ENTROPI STEREO R08: Tripo-master

Referanse: `reference/tripo_reference_square.jpg`. Eksakt bilete frå den valde 3/4-skissa, sentrert på kvit 768 x 768 flate, utan endring av kamerasilhuetten.

## Formkrav
Asymmetrisk venstregrep med taktil utløysar øvst, samanhengande og mjuk bølgje frå venstre mot to små linser til høgre, to avtakbare linsetuver, avrunda bakvolum. Ikkje utvid den opphavlege optikken til store DSLR-ringar. Bevar originalforma før mekanikken blir laga.

## Elektronikk
- Linocell 5000 mAh: 94 x 62 x 15 mm (publiserte yttermål).
- To AI Thinker ESP32-CAM-kort: nominelt 27 x 40,5 mm kvar. Utan ESP32-CAM-MB i ferdig eining.
- Powerbanken skal monterast tett ved USB-sida: hol gjennom ytterveggen, ikkje djup USB-brønn.
- USB-A for straum ut og USB-C for lading krev målt kontaktplassering og kabelbane før fysisk sign-off.
- Eksakt USB-pluggtoleranse, straumdeling og sensorplassering er enno ikkje fysisk verifiserte.

## Pipeline
1. `powershell -ExecutionPolicy Bypass -File .\RUN_TRIPO_R08.ps1` etter Tripo CLI-innlogging.
2. `tripo/master/`: H3.1 detaljert mesh. Aldri destruktiv desimering på masteren.
3. `tripo/lowpoly/`: 20 000 trekantar, retopologi v3.0 som separat CAD-referanse.
4. Samanlikn silhouette og 3/4 med referansen, både front og bak. Avvis modell ved formavvik.
5. Lag parametrisk mekanikk/haldarar basert på godkjend master og reelle komponentmål.
6. Kontroller uttaksbaner, printklaringar, vassfast topologi og G-kode før P1S-print.

R08 er førebels ikkje ein produksjonsklar CAD-assembly. Ingen Tripo-jobb er oppretta før autentisert generering faktisk har returnert task-ID.
