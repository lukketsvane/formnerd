# Lærdom frå Stereo R01

1. Finn eksisterande Tripo-oppgåver før nye betalte kall. Denne vidareføringa brukte dei to lagra oppgåvene, ikkje ei ny generering.
2. Lås ein referansesnapshot med hash av bilete, mesh, transformasjon og volumfelt. Ei anna aktiv økt kan endre filer i same prosjektgrunnlag.
3. Eit filnamn som «repaired» er ikkje ein topologitest. Kontroller lukking, konsekvent winding og samanhengande volum før skalbygging.
4. Glatt avleidd volumfelt kontrollert før både ytre og indre isoflate. Dokumenter endringa; ikkje skjul henne gjennom berre pene normalar i renderen.
5. Skil visuell Tripo-segmentering frå mekaniske produktdelar. Berar, festepunkt, toleransar og maskinvare krev eigne kontrollerte konstruksjonar.
6. Kutt hol og mutterlommer etter endeleg union av bossar og skal. Elles kan skalveggen fylle att opninga.
7. Kontroller fysisk monteringsveg, ikkje berre sluttposisjon. Prøv heile kassetten med haldelister og maskinvare, og prøv bakskalet si innskyving.
8. Last elektronikk i kassetten før ho går inn i huset dersom tilkomsten elles blir stengd. Oppdater monteringsrettleiinga når rekkjefølgja endrar seg.
9. Bruk den faktiske, eksporterte geometrien til sluttbilete og monteringsmanual. Eit stilutkast kan styre layout, men er ikkje geometrisk dokumentasjon.
10. Skil digital geometritest, slicartest og fysisk passformprøve i leveransen. Ingen av dei tre er ei erstatning for dei andre.
11. Last inn kvar eksportert STL på nytt. Gyldig GLB eller manifold interngeometri garanterer ikkje gyldig STL etter flyttalsavrunding. Loggfør eventuell minimal opprydding og volumendring.
12. Lås modellhashane før manualen blir rendera. Kontroller at printfiler, PDF og uavhengig audit viser til same revisjon før pakking.
13. Bruk prosjektlokal `.gitattributes` med `* -text` når hashkontroll og tapsfrie filbitar skal fungere på Windows. Automatisk CRLF-konvertering kan endre både kjelder og PDF-bitar utan å endre Git-objektet. Prøv gjenoppbygging etter faktisk Windows-checkout.
