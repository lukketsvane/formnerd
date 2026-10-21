# A1 som gjennomført døme

Bruk kjeldene som sporbar metode- og stilreferanse, ikkje som universelle mål eller prov på fysisk passform.

## Kjelder og filer

- Repo: [lukketsvane/formnerd](https://github.com/lukketsvane/formnerd).
- Dokumentert R03-revisjon: `d4047d83d9a537a9a991a38238d35ab3a224c60d` på `claude/stereoskopisk-kamerahus-cjqyqr`.
- Dåverande mappe: `A4/arkiv/tripo-a1/cad-assembly/`. Sjekk gjeldande tre før endring; A1 låg tidlegare i eiga rotmappe.
- [CAD, printfiler og manual på fast revisjon](https://github.com/lukketsvane/formnerd/tree/d4047d83d9a537a9a991a38238d35ab3a224c60d/A4/arkiv/tripo-a1/cad-assembly).

| Fil under arbeidsmappa | Bruk |
| --- | --- |
| `review/A1-Byggjerettleiing-R03.pdf` | Visuell standard og rekkjefølgje |
| `review/pages-r03/` | Kontrollerte sidebilete |
| `review/A1-R03-bilete-og-kjelde.zip` | Portabel PDF-byggjar, figurar og manifest |
| `verification/guide-r03.json` | Sidetitlar, figurgrunnlag og status |
| `cad/` | Mekanikk, parameter og kontrollrutinar |
| `print/` | Individuelle delar og to føreslåtte plater |
| `PRINT-P1S.md` | Lokal handoff med låseprøve først |

Pakk ut kjeldepakken og les `source/build_manual_r03.py` før tilpassing. Fjern A1-spesifikke mål, tekstar og ID-ar ved nytt produkt. Bruk figurar frå den nye geometrien.

## Metode og status

Den valde detaljerte Tripo-forma vart bevart som meshgrunnlag, delt og lukka før mekaniske opningar og grensesnitt vart modellerte. Analytiske delar vart bygde separat; komplett montert 3MF/GLB og analytisk STEP fekk dokumentert omfang. Konstruksjonen fekk 11 produktdelar, pluss låseverktøy og testhylse: 13 objekt totalt.

R03 har 29 A4-sider med 23 byggjesteg, deloversikter, eksplodering, elektronikk/programmering, isometrisk montering og låsedetaljar. Tekniske figurar kjem frå geometri og deterministiske elektronikkteikningar. R03 endra ikkje printgeometrien.

A1 var digitalt og generisk slicer-kontrollert; fysisk passform var uprøvd. Nominell CAM/MB-plass, brytar, fleks og pluggveg måtte prøvast med maskinvara. Første fysiske steg var éin lås, testhylse og verktøy: krev innføring, 90° rotasjon, aksialt hald og opning utan skade før hovudutskrift.

## FormNerd som prosjektkontekst

Ved FormNerd-arbeid: les dei aktuelle oppgåve-PDF-ane før nye designval. Prosjektoversikta side 2 prioriterer uttrykket av eit valt konseptord og krev dokumentert skisse-/modellprosess og fysisk modell. Intro side 7 legg konsept, proporsjonar og enkle modellar før digital modellering og samanføyingar. Semiotikk side 7 og 13-19 gir kjeda konsept → tolking → form → mottakar → tilbakemelding. Formanalyse side 5-9 og 26-32 legg storform, proporsjonar, balanse og negativt rom før detaljar; side 34-48 og 58-67 knyter overflater, skjøtar og komponentar til heilskapen. Tripo og assemblymanual er metodetillegg, ikkje krav frå desse PDF-ane.
