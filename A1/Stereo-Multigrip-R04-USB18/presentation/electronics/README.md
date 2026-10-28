# ESP32-CAM og programmerkortet

Faktiske Blender Cycles-rendringar av ein detaljert 3D-modell, bygd frå komponentgeometri og fotografi. Ingen bilete er laga med imagegen. Den låge, firkanta kamerakroppen følgjer brukaren sitt foto; Prusa-fotografia er brukte for kort, kontaktar, komponentgrupper og merking.

Dei endelege bileta er 2400 × 1800 pikslar, 96 samples med denoising og rein kvit bakgrunn. Det finst ikkje noko golv eller kontaktskugge i scena.

| Fil | Innhald |
|---|---|
| `ESP32_CAM_front.png` | Kamerakortet frå framsida |
| `ESP32_CAM_back.png` | RF-modul, antenne, regulator, minne og reset på baksida |
| `ESP32_MB_actual_hero.png` | Programmerkort med opne headerkontaktar og microUSB |
| `model-provenance.json` | Opphav og avgrensingar for CAM-modellen |
| `mb-model-provenance.json` | Opphav og nominelle mål for eigenmodellert MB-kort |
| `assembly-verification.json` | Uendra R04-geometri og korrekt plassering av begge korta |

Modellane er referansemodellar, ikkje produsentsertifisert mekanisk CAD. Fotobaserte komponentplasseringar og høgder er nominelle. Kamerahuset og linsa er rekonstruerte frå brukaren sitt foto; dei er ikkje målte på ein fysisk modul.

Den eksterne kortgeometrien har 40,0 × 27 mm omriss. Ai-Thinker-databladet oppgir 40,5 × 27 mm. Omrisset og kontaktavstanden er ikkje strekte for å skjule skilnaden. PCB-tjukkleiken er sett til nominelt 1,6 mm, mot 1,0 mm i kjeldegeometrien. Z-tilpassinga er stykkevis: under kjeldeplanet 2,5 mm blir geometrien flytta −2,5 mm; gjennom intervallet 2,5–3,5 mm blir Z skalert 1,6 gongar; over 3,5 mm blir geometrien flytta −1,9 mm. Delar som kryssar PCB-sjiktet blir dermed tilpassa i Z, medan XY og pinneavstand er uendra.

I samanstillinga ligg CAM-botnen på Z = 32,1 mm og MB-botnen på Z = 22 mm. Venstre komplette elektronikkmodell er rotert 180°, ikkje spegla; begge podane har 18° rull. Alle 21 inkluderte printdelar er identiske med den tidlegare verifiserte R04-geometrien. Kabel- og pluggvoluma er framleis nominelle konvoluttar.

Den ekstra dekorative flata på kameraet vart erstatta med materiale på den eksisterande toppflata. Smal geometrikontroll viser 0,129 mm mellom SD-haldaren og kamerakroppen, og den låge linseringen ligg 2,1 mm bak fronten på yoken. Desse kontrollane erstattar ikkje fysisk passformprøving.

## Kjelde og reproduksjon

MicroSD-haldar, FFC-kontakt, headerpinnar, RF-skjerm og antenne er baserte på [ProtoFlow/FastEDA sin ESP32-CAM-modell](https://www.protoflow.ai/library/parts/C277946). Den eksterne inngangsfilen er [VRML-fila](https://www.protoflow.ai/library/parts/C277946/files/COMM-TH_16P-L40.0-W27.0-P2.54_ESP32-CAM.wrl), SHA-256 `119a8442cfec1df5605e515bf899f3431a069327b13bcfda152778c584f7456f`.

Det er ikkje funne ein eksplisitt redistribusjonslisens for den eksterne mesh-fila. Ho og avleidde komplette CAM-mesh/scenefiler er derfor ikkje inkluderte i det offentlege repositoriet. Dei private Blender-scenene har modell, materiale, kamera og lys samla. Den offentlege byggjekoden tek den eksterne fila som eit uttrykkeleg argument.

Fotoreferansane kjem frå [Prusa si AI-Thinker ESP32-CAM-dokumentasjon](https://github.com/prusa3d/Prusa-Firmware-ESP32-Cam/tree/master/doc/AI_Thinker-ESP32-cam). Bileta vart brukte som geometrireferansar, ikkje som bakgrunn eller som erstatning for rendringar.

Frå R04-mappa, med Blender 4.3.2:

```sh
blender --background --python presentation/electronics/source/build_esp32.py -- --source-wrl /path/to/ESP32-CAM.wrl --output presentation/electronics/ESP32_CAM_reconstructed.blend
blender --background --python presentation/electronics/source/build_mb.py -- --output presentation/electronics/ESP32_MB_reconstructed.blend
blender --background --threads 4 --python presentation/electronics/source/render_board.py -- --model presentation/electronics/ESP32_CAM_reconstructed.blend --view front --width 2400 --samples 96 --output presentation/electronics/ESP32_CAM_front.png
python presentation/white_background.py presentation/electronics/ESP32_CAM_front.png
```

Bruk `--view back` for baksida. `render_board.py` kan òg lagre ei innramma scene med kamera og lys ved `--scene-output FILE.blend`; `--skip-render` lagrar berre scena. For dei 18 materialstudiane, sjå [mono-series](../mono-series/README.md).
