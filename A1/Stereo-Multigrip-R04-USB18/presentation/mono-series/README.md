# R04: 18 matte materialstudium

Atten separate 3D-rendringar av R04 med detaljert ESP32-CAM og programmerkort, laga i Blender Cycles. Dei eksisterande STL-filene for printdelane er uendra. Kvar vising har éin modell på heilt kvit bakgrunn utan golv eller bakkeskugge. Ingen biletegenerering eller endring av printgeometrien er brukt.

| Serie | Farge på printdelane | Bilete |
| --- | --- | --- |
| 01 til 06 | Matt svart | Hero, front, bak, høg skråvinkel, låg sidevinkel, låsedetalj |
| 07 til 12 | Nøytral matt grå | Same seks kameravinklar |
| 13 til 18 | Svart kameraberar med grå lause delar | Same seks kameravinklar |

Den matte overflata har ruheit 0,62 og ingen klarlakk. Lys og kameravinklar er valde for å vise konturar, djupn og låsar også på dei svarte delane. Dei to elektronikkstablane bruker den [detaljerte fotobaserte modellen](../electronics/README.md). Plugg- og kabelvoluma er framleis nominelle referansar. Fargestudiet endrar ikkje filamentval eller innstillingar for den fysiske utskrifta.

`shot-plan.json` er den ordna bileteplanen med filnamn, materiale, kameraretningar og merking av nærbilete. Nærbileta viser eksisterande låsar i montert stilling og er ikkje ei innføringsrettleiing.

Alle sluttbileta er 2400 × 1800 pikslar, 96 samples med adaptiv sampling og støyfjerning. Kvart bilete har ein tilhøyrande `render-NN.json` med kjeldefiler og SHA-256-hashar. `batch-progress.json` inneheld mål, biletkantar og faktisk renderingsstid.

Bygg først CAM- og MB-modellane etter oppskrifta i electronics/README.md. Bygg deretter heile serien frå prosjektmappa med Blender 4.3.2 og Python med NumPy og Pillow:

```bash
python presentation/mono-series/run_batch.py --blender /path/to/blender --workers 2 --threads 4
```

For eit utval kan du leggje til `--ids 01,07,13`. Skriptet rendrar dei uendra printmeshane og dei detaljerte elektronikkmodellane med vald overflate og legg det ferdige RGBA-biletet over heilt kvitt etter fargekonverteringa. Den private modellpakken inneheld éi komplett R04-studioscene i matt svart og separate CAM- og MB-studioscener, alle med kamera og lys. Dei grå og tofarga variantane kan byggjast med `--palette grey` og `--palette duo`; dei er ikkje dupliserte som ekstra filer i modellpakken. CAM- og R04-scenene inneheld ekstern CAM-komponentgeometri og blir leverte privat. Det offentlege repositoriet har byggjekode, kjelde-URL, hash og sluttrendringar. Alle gamle førebelse bilete med forenkla elektronikk er erstatta i denne serien.
