# Detaljerte ESP32- og R04-scener

Tre sjølvstendige Blender 4.3.2-filer med geometri, materiale, kamera og lys:

- `ESP32_CAM_studio.blend`: kamerakort, OV2640-kamera og flekskabel.
- `ESP32_MB_studio.blend`: programmerkort med USB-kontakt, headerkontaktar og komponentar.
- `R04_matte_black.blend`: heile R04-samanstillinga med begge detaljerte elektronikkstablane.

Opne ei fil i Blender. Kameraet er innramma og aktivt. F12 rendrar den aktive visinga med Cycles. PNG-utskrift er RGBA; legg resultatet over kvitt etter fargekonvertering for nøyaktig #FFFFFF bakgrunn. Det ferdige biletsettet er allereie levert med kvit bakgrunn.

R04-scena inneheld den matte svarte varianten. Dei same uendra meshane kan også få nøytral grå eller svart/grå tofarge. Materiala heiter `Matte black printed polymer` og `Neutral grey printed polymer`; begge har ruheit 0,62 og ingen klarlakk. Tofarge bruker svart på `02_multigrip_carrier` og grått på dei andre printdelane. Dette er visualiseringsval, ikkje endringar av den fysiske utskrifta.

Den offentlege `presentation/mono-series/render_mono.py` kan byggje variantane med `--palette black`, `--palette grey` eller `--palette duo`. Køyreskriptet `run_batch.py` rendrar heile den dokumenterte bileteplanen. `electronics/README.md` forklarer reproduksjon frå den eksterne mesh-inngangsfilen.

CAM-scena og R04-scena inneheld komponentgeometri frå ProtoFlow/FastEDA. Det er ikkje funne eksplisitt løyve til offentleg redistribusjon av denne mesh-fila; desse komplette modellane er derfor private leveransar. Opphav, URL og hash står i `model-provenance.json`. MB-modellen er eigenmodellert frå fotografi, dokumentert i `mb-model-provenance.json`.

Ingen modell er produsentsertifisert eller fysisk passformverifisert. Komponenthøgder og fotobaserte detaljar er nominelle. CAM-omrisset er 40,0 × 27 mm frå kjelda, medan databladet oppgir 40,5 × 27 mm. XY og kontaktavstand er bevarte. PCB-sjiktet og komponentar som kryssar det er tilpassa i Z til nominell 1,6 mm tjukkleik. Alle printdelar i R04 er uendra.
