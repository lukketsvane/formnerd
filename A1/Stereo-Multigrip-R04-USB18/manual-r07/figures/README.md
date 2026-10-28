# R04 USB18: tekniske illustrasjonar

Fjorten illustrasjonar frå den faktiske detaljerte R04-scena. Alle er rendra i Blender 4.3.2 med Cycles og Freestyle, som svarte synlege konturar og kantar på kvit bakgrunn. Ingen biletegenerering, tesselleringsnett, skuggelegging eller golv er brukt.

Trykkdelar og elektronikk har same geometri som i den tidlegare leverte modellen. Materiale, synlegheit, kamera og eksploderingsforskyvingar er visingsval. Venstre elektronikk er framleis rotert 180 gradar, ikkje spegla; podane har 18 gradar rull. Små tekstobjekt er utelatne frå strekteikningane. Faktiske komponentar, kontaktar, pinnar, sensor og bandkabel er bevarte.

| Fil | Innhald |
|---|---|
| `technical_assembled.png` | Ferdig kameraramme med alle 21 trykkdelar og begge elektronikksett. Nominelle USB-pluggar og kabelkonvoluttar er utelatne. |
| `technical_exploded.png` | Dei 21 delane og to elektronikksett skilde for å vise delsamanheng. Dette er ikkje ein verifisert PCB-innføringsveg. |
| `technical_seated.png` | Berar og elektronikk i nominell sluttposisjon. |
| `technical_keepers_rear.png` | Begge bakhaldarane viste 50 mm bak montert posisjon, sett bakfrå. |
| `technical_keepers_locked.png` | Bakhaldarane med fire pinnar og fire korte kilar monterte. Ingen linsebøylar eller kablar. |
| `technical_yokes.png` | Linsebøylane viste 45 mm framfor montert posisjon. Alle fire bakhaldarlåsar er monterte. |
| `technical_rear_usb.png` | Bakside med nominelle plugg- og kabelvolum for rutingsforklaring. |
| `technical_pair_front.png` | Begge korta nesten rett framanfrå, med motsett orientering. |
| `technical_board_stack.png` | Eitt CAM/MB-sett i nominell sluttposisjon. |
| `technical_cam_only.png` | Detaljert ESP32-CAM utan MB eller ramme. |
| `technical_mb_only.png` | Detaljert ESP32-CAM-MB utan CAM eller ramme. |
| `technical_bank_placement.png` | Komplett kameraramme med detaljert elektronikk, medan eksisterande bankramme og nominelt bankvolum er skilde 42 mm bakover. 22 trykkdelar; dette er ikkje ein verifisert innføringsveg. |
| `technical_bank_locked.png` | Alle 30 trykkdelar i sluttposisjon, med detaljert elektronikk og nominelt bankvolum. Ingen plugg- eller kabelvolum. |
| `technical_sensor_contact.png` | Nærbilete av faktisk høgre sensor, bandkabel og linsebøyle. Bøylen er løfta 4 mm for å vise kontaktområdet. Berar og MB er utelatne; biletet er medvite avgrensa til detaljen. |

Bileta er 3000 × 2400 pikslar og RGB. Dei sterke konturane og lettare detaljlinjene følgjer den undersøkte manualstilen, mellom anna KALLAX side 20 i referansesamlinga. Detaljar har same geometriske opphav som dei fotorealistiske modellrendringane.

JSON-fila ved kvart bilete inneheld synlege objekt, kamera, millimeterforskyvingar og `anchors`. UV-origo er nedst til venstre. `shown_center_uv` er vist posisjon; `assembled_center_uv` er den opphavlege monterte posisjonen. Sensorbiletet og bøylefiguren har i tillegg dei fire eksisterande integrerte kontaktpunkta i `existing_integral_contact_points`. Desse er avleidde frå dei faktiske CAD-parametrane, ikkje nye kontaktputer.

## Omfang og avgrensingar

PCB-innføringa bakfrå er framleis ikkje godkjend; `technical_seated.png` viser berre sluttposisjon. Eksploderte bilete stadfestar ikkje rørsleveg. Elektronikken er ein detaljert referansemodell basert på kjeldemesh og foto; komponenthøgder og passform er ikkje fysisk målte. Kabel- og pluggvolum på USB-biletet er nominelle. Bankvolumet på dei to bankfigurane er den eksisterande referansen på 94 × 62 × 15 mm, ikkje eit mål av brukarens bank eller ein modell av kontaktane hans. Kontaktpunkta må prøvast med den faktiske sensoren utan å presse på linse eller bandkabel.

## Reproduksjon

Bruk den private sjølvstendige `R04_matte_black.blend` frå den leverte modellpakken. Den eksternt avleidde CAM-geometrien skal ikkje leggjast i det offentlege repositoriet. Den private kjeldescena har SHA-256 `0058945ddf817272faac08a8e517442deb472f21adc69f56a1dc610d467c2690`.

```sh
python run_technical.py --blender /path/to/blender --blend /path/to/R04_matte_black.blend --r04-source /path/to/Stereo-Multigrip-R04-USB18 --scenes assembled exploded seated keepers_rear keepers_locked yokes rear_usb pair_front board_stack cam_only mb_only sensor_contact bank_placement bank_locked
```

Byggjekjelda vel synlege Freestyle-silhuettar, opne grenser og skarpe kantar, utan skjulte kantar eller trekantnett. Trykkdelane har konturar på 3,2 px og detaljar på 1,6 px. Elektronikken i samanstillingane har 1,6/1,0 px; sjølvstendige elektronikkvisingar har 3,2/1,6 px. Sensorinnfeltet bruker 1,8 gonger desse strekbreiddene for lesbarheit i ein liten sirkel. Dei ekstra bankdelane er importerte direkte frå dei eksisterande STL-filene i montert koordinatsystem, med skala 0,001 frå millimeter til meter; kjeldehashane ligg i JSON-fila. Hovudscena får kvit, sjølvlysande overflate berre for rein teknisk strek, ikkje som eit føreslått materiale.
