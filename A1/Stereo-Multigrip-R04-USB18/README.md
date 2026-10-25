# R04: meir vinkel og plass til rette USB-pluggar

Vidareføring av den fysisk printa Stereo Multigrip R03. Begge kamerastablane er vridde frå 12° til 18° kring sine eigne linseaksar. Linsesentera står framleis 76,326 mm frå kvarandre på same vassrette linje. Dei optiske aksane er parallelle; dette er ikkje innovervinkling av kameraa.

Kontrollen bruker førebelse rette pluggvolum på 24 × 16 × 10 mm, med 0,8 mm ekstra serviceklaring rundt. Dette er ikkje mål av dei faktiske pluggane på fotoa. Det er 7,586 mm mellom pluggvoluma og minst 2,086 mm frå eit pluggvolum til det motståande MB-kortet. USB-opningane omfattar ein samanhengande 20 mm innføringsveg og ein førebels kabelbane på 6 mm diameter med 12 mm senterlineradius. Faktisk stivleik, minste bøyeradius, toleransar og handplass er ikkje fysisk testa.

Dei fire bakhaldarlåsane er løfta 7 mm over kabelplanet. Alle åtte kamerakilane har kortare spiss; heile inngrepet i T-pinnen, halsen og trekkfliken er bevarte. Kilespissen har 1,15 mm vertikal klaring over servicevolumet. To lause USB-veggrestar og to ikkje-berande ytterendar av ribbene er fjerna og dokumenterte i kontrollrapporten. Bereføter og sensorkontaktar er bevarte. Kanalane i kameraberaren gir plass til å føre dei nye bakhaldarane inn frå baksida før kablar, linsebøylar, pinnar og batteriramme blir monterte.

## Prøv først

Opne `3MF/00_USB_CLEARANCE_TEST_FIRST.3mf` i Bambu Studio. Dette er ei tynn 5,4 mm prøveramme som plasserer dei komplette ESP32-CAM/MB-stablane med den nye vinkelen og har integrerte støtteføter. Hald korta varsamt på plass medan du prøver begge faktiske USB-pluggane og kabelbøyane. Prøveramma erstattar ikkje dei endelege bakhaldarane eller låsane. Ho har same nominelle plassering av korta og USB-serviceopningar, men er for lett prøving, ikkje bruk som kamera.

## Delar som skal printast på nytt

`3MF/01_R04_REPLACEMENT_PARTS.3mf` inneheld berre desse elleve delane:

- Éin ny dobbelkameraberar, `02_multigrip_carrier`.
- To nye bakhaldarar med høgare låseøyre, `03_MB_keeper_left` og `04_MB_keeper_right`.
- Åtte korte kamerakilar: fire til bakhaldarane (`20_keeper_*_wedge`) og fire til linsebøylane (`30_yoke_*_wedge`).

Den eksisterande R03-batteriramma kan brukast om att. Dei åtte kamera-T-pinnane, begge linsebøylane og dei fire ytre hovudlåsane kan òg brukast om att. Bakhaldarane frå R03 skal erstattast, og dei åtte gamle kamerakilane skal erstattast med dei korte kilane på plata. Kontrollen i `checks/reuse-checks.json` samanliknar dei aktuelle gamle STEP-delane med dei nye monteringsposisjonane. Faktisk printpassform må framleis prøvast.

Dei to 3MF-filene er uslica modellplater for ei 256 × 256 mm plate. Dei inneheld ingen skrivarjobbar. Vel faktisk Bambu P1S, dyse, plate og filament i Bambu Studio og sjå gjennom støtte og verktøybaner før printing. Dei heva armane på bakhaldarane kan krevje støtte i den leverte orienteringa; fjern støtta frå innføringsflater og hol før prøvepass. Fullmodellen inneheld òg ein ny nominell batteriramme som referanse; han er ikkje på erstatningsplata og treng ikkje printast.

## Montering

1. Prøv vinkelen og begge USB-kablane i den tynne prøveramma.
2. Avklar innføringa av kamerakorta før montering. Kontrollen i `checks/manual-insertion-review.json` viser at ei rett innføring bakfrå kolliderer med den nominelle kameraberaren. Sluttposisjonane har klaring, men det dokumenterer ikkje innføringsvegen. Ikkje press korta gjennom ramma.
3. Monter dei to nye bakhaldarane. Bruk dei fire eksisterande keeper-T-pinnane og dei fire nye korte keeperkilane. Ikkje tving ein kile som bind.
4. Flytt over linsebøylane og T-pinnane deira, og bruk dei fire nye korte linsebøylekilane. Kontroller at kontaktane landar på dei stive sensorskuldrene og ikkje på linsa eller flekskabelen.
5. Kople til begge USB-kablane og prøv at pluggane går heilt inn utan sidepress. La kablane følgje dei opne servicevegane.
6. Monter den eksisterande batteriramma og dei fire ytre hovudlåsane. Kontroller at alle fire koplingane ligg plant og at ingen kabel blir klemd.

Begge bileta får den nye felles rotasjonen. Orientering eller stereokalibrering i programvara må tilpassast ved bruk.

## Kontrollert digitalt

- Éin gyldig solid per printdel, positivt volum og lukka STL-overflater.
- Ingen påviste volumkollisjonar mellom printdelane, dei nominelle elektronikkvoluma og USB-/kabelservicevoluma.
- Kontinuerlege rette USB-innføringsvolum og samanhengande innføringsvolum for bakhaldarane frå baksida. Toleransar og praktisk innføring må framleis prøvast fysisk.
- Bevarte linsesenter og parallelle optiske aksar.
- Positive meshvolum, avstand mellom delane og plassering innanfor begge 3MF-platene.
- STEP-eksportane importerte på nytt og kontrollerte.

Dette er ei digitalt kontrollert prøveutgåve med uavklart innføring av kamerakorta. Ho er ikkje fysisk passformprøvd med dei faktiske kablane dine. Erstatningsplata med tre hovuddelar og åtte korte kilar er importert og slica i Bambu Studio for P1S med 0,4 mm dyse, 0,12 mm lag, tre veggar, 20 % gyroid og seks topp-/botnlag. Ytterveggar og toppflater er sette til 40 mm/s. Jobben vart starta med AMS A3 og gult PLA; estimatet var 5 timar 23 minutt og 60,99 g med støtter. Dette stadfestar slicing og oppstart, ikkje ferdig utskrift eller fysisk montering.

## Faktiske rendringar og fullstendig monteringsmanual

`presentation/` inneheld material- og lysrendringar av dei eksisterande R04-meshane. [Den detaljerte ESP32-visingsmodellen](presentation/electronics/README.md) kombinerer referansegeometri og rekonstruerte komponentdetaljar. Dei nominelle elektronikkvoluma i passformkontrollen er uendra. [Monteringsmanualen utgåve 07](manual-r07/output/ENTROPI_R04_Monteringsmanual.pdf) har 15 sider med faktiske ESP32-rendringar, deleoversikt, tydelege byggjesteg og sluttkontroll. [Alle manualsider](https://chatgpt.com/space/page_f9400752da088191973e1efe3b0adebc) er samla i FormNerd. [Byggjekjelda](manual-r07/README.md) kan regenerere PDF-en og alle sidebileta lokalt. Innføringsvegen for kamerakorta må framleis avklarast fysisk; korta skal ikkje pressast på plass. Den eldre ti-siders utgåva er bevart i `manual-r05/`. Dokumenta endrar ikkje modellgeometrien eller printfila.

Serien [svart, grått og tofarga](presentation/mono-series/README.md) viser same CAD-modell frå seks vinklar per materialval.

## Bygg på nytt

Køyr frå prosjektmappa med CadQuery, NumPy og Pillow tilgjengeleg:

```bash
python source/build_harness.py
python source/prepare_delivery.py
python source/verify_exports.py
```

`source/parameters.json` styrer mål, vinkel og klaringar. `STEP/` har redigerbare solide delar og samanstillingar. `STL/PRINT_*.stl` er individuelle printfiler ved Z=0; andre STL-filer er monteringsreferansar. Renderane viser faktisk CAD og førebelse plugg-/kabelvolum i grått. R03-kjelda er bevart i nabomappa i formnerd-repoet.
