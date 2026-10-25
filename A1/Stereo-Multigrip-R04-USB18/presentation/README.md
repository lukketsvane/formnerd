# R04: ekte 3D-rendringar

Dei tre opphavlege bileta er raytraca i Blender Cycles frå dei eksisterande R04-STL-filene. Ingen biletegenerering, nye komponentar eller endringar i printgeometrien er brukte. Dupliserte meshpunkt er sveisa saman for korrekte visingsnormalar. Materialar, lys og kamera er eigne visingsinnstillingar.

Gult viser dei tre nye hovuddelane og dei åtte korte låsekilane. Grått viser linsebøylane og T-pinnane som skal brukast om att. Ramma bak batteriet er ikkje med i desse produktvisingane. Elektronikken er dei forenkla, nominelle CAD-voluma, utan oppdikta komponentdetaljar. Dei svarte USB-voluma og kabelbanane er førebelse geometriske referansar, ikkje målt kabelgeometri.

- `R04_actual_hero.png`: framfrå i trekvart vinkel.
- `R04_actual_front.png`: ortografisk frontvising.
- `R04_actual_rear.png`: bakfrå i trekvart vinkel.
- `R04_actual_studio.blend`: komplett lokal 3D-scene med innebygde mesh og materialar.
- `render_actual.py`: byggjer scena frå dei eksisterande STL-filene.
- `scene_A3.json`: del-ID-ar, fargar og kjeldestiar.
- `render-*.json`: filhashar, trekanttal og renderinnstillingar per vising.

[Den detaljerte ESP32-visingsmodellen](electronics/README.md) blir brukt i serien [svart, grått og tofarga](mono-series/README.md), med seks vinklar per materialval. Dei tre opphavlege bileta ovanfor bruker forenkla elektronikk. Printgeometrien er uendra.

Køyr frå prosjektmappa med Blender 4.3 eller nyare, Python 3 og Pillow:

```bash
blender --background --threads 8 --python presentation/render_actual.py -- --view hero --width 2400 --samples 128
blender --background --threads 8 --python presentation/render_actual.py -- --view front --width 2400 --samples 128
blender --background --threads 8 --python presentation/render_actual.py -- --view rear --width 2400 --samples 128
python presentation/white_background.py presentation/R04_actual_hero.png presentation/R04_actual_front.png presentation/R04_actual_rear.png
```

Cycles skriv først eit bilete med gjennomsiktig bakgrunn. Siste kommando legg det ferdige rendra biletet over heilt kvitt utan å endre sjølve objektet. Det finst ikkje noko golv eller nokon bakkeskugge i scena. Materialfargane er illustrerande og ikkje fysisk fargemålte.
