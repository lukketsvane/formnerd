# A1 til Bambu Lab P1S

Repo: `lukketsvane/formnerd`. Grein: `claude/stereoskopisk-kamerahus-cjqyqr`.
Arbeidsmappe: `A4/arkiv/tripo-a1/cad-assembly/`.
Dette er A1-geometri R01 med byggjerettleiing R03. Fysisk passform er ikkje verifisert.

1. Les `README.md`, `review/A1-Byggjerettleiing-R03.pdf` og `bill-of-materials.json`. Behald original skala og form. Printmodellane ligg i `print/`; `review/A1-assembled.3mf` er berre ei montert vising.
2. Opne modellane i Bambu Studio. Vel faktisk P1S, dyse, byggjeplate og filament. Startgrunnlag: PLA, 0,4 mm dyse, 0,20 mm lag, 3 veggar, 15 % gyroid, automatisk støtte. Bruk P1S-profilen sine temperaturar og maskininnstillingar. INI-fila er eit generisk kontrollgrunnlag; lag ny P1S-slicing.
3. Første prøve: `print/test_lock_socket.3mf` + `print/05_lock_1.3mf` + `print/06_lock_tool.3mf`. Kontroller orientering, platekontakt, støttefjerning og alle lag i førehandsvisinga. Lagre Bambu Studio-prosjekt og slica `.gcode.3mf` med profilnamn.
4. Kontroller rett skrivar, ledig/rein plate og filament, og print prøva. Fjern støtte. Låsen skal gå inn, dreiast 90°, halde aksialt og opnast igjen utan stor kraft eller sprekk. Registrer resultatet før resten blir printa.
5. Etter godkjend låseprøve: slice dei attståande delane. `print/A1-plate-01.3mf` og `print/A1-plate-02.3mf` har føreslått plassering på 256 mm plater. Kontroller tal og unngå unødvendige duplikat frå prøva. Produktet har 11 delar: skal, lokk, haldar, frontring, 4 låsar, utløysar, utløysarkassett og kameraklemme. Verktøy og testhylse gir totalt 13 objekt.
6. Kontroller støtte og verktøybaner for alle objekt, lagre prosjekt/slica plater og print. Dokumenter profil, materialbruk, tid og eventuelle feil.
7. Prøvepass faktisk ESP32-CAM + MB, kamerafleks, USB-plugg og brytar. Nominell stakkplass er 28 × 48 × 22 mm og brytarsete 6 × 6 mm. Kontroller knappeslag/retur og kabelklaring før sluttmontering. Følg R03-guiden. Rapporter avvik med mål og bilete før endring av geometrien.
