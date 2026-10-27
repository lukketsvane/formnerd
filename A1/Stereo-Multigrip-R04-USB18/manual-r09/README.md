# ENTROPI R04 USB18 monteringsmanual

Utgåve 09 er ein 17-siders monteringsmanual med modellavleidde strekteikningar, store detaljutsnitt og korte nynorske instruksjonar. Arbeidsgangen går frå reingjering etter Tree Hybrid-print og prøving av låsane til montering, kameratest og demontering. Direkte samanlikning med dei tre leverte IKEA-manualane har gitt tydelegare strekar, mengder ved handlingane, samanhengande detaljhalar og eigne bilete av ferdige låsar.

Side 5 viser kva delar av beraren som skal stå att når den mellombelse printstøtta blir fjerna. Side 6 skil korte og lange kilar og viser ein prøvelås utan elektronikk. Kortinnføringa er eit stoppunkt på side 7: rett innføring bakfrå kolliderer i nominell CAD, og ein annan innføringsveg og fysisk passform er ikkje verifiserte. Illustrasjonane endrar ikkje R04-geometrien.

## Filer

- `output/ENTROPI_R04_Monteringsmanual.pdf`: manualen i A4 med 17 sider.
- `pages/`: éin PNG per side.
- `source/build_manual.py`: portabel PDF-byggjar.
- `source/fonts/`: skrifter og lisens.
- `figures/`, `vector/` og `vectors/`: faktisk brukt figurgrunnlag og scenedata.
- `used-assets.json`: eksakte avhengigheiter for PDF-byggjaren.
- `ikea-comparison.md` og `.json`: konkret samanlikning med dei tre leverte referansane.
- `qa.json`, `layout-checks.json` og `source-manifest.json`: kontroll og filidentitet.

## Bygg på nytt

Køyr frå den utpakka manualmappa:

```bash
python3 -m pip install -r source/requirements.txt
python3 source/build_manual.py
```

PDF-byggjaren bruker lokale figurar og skrifter. Han treng ikkje nettverk, Blender eller CadQuery. Dei same figurane kan brukast til å gjenskape manualen og alle sidebileta.

## Figurgrunnlag

Mekaniske strekteikningar kjem frå R04 STEP. Dei detaljerte ESP32-illustrasjonane er rendra i Blender 4.3.2 med Cycles og Freestyle frå den tidlegare leverte faktiske scena. Elektronikken har nominelle og fotobaserte mål. `figures/README.md` dokumenterer kamera, visingar og reproduksjon.

Den private CAM- og samanstillingsscena og rå kjeldemesh er ikkje distribuerte i denne pakken. Ferdige illustrasjonar og fontfiler er nok til å byggje PDF-en. Generatorskript for nye geometriillustrasjonar krev den eksisterande R04-kjelda og dei dokumenterte ekstra avhengigheitene.

Detaljane på side 15 bruker den faktiske øvre batterirammeskjøten `10_frame_2`. Dei kan lagast på nytt med CadQuery og dei andre generatoravhengigheitene installerte:

```bash
python3 vector/build_frame2_joint_figures.py /sti/til/Stereo-Multigrip-R04-USB18 --alternate
```

`frame_pin_stage.json`, `lock_frame_wedge_stage.json` og `frame_lock_seated.json` er med som generatorinngangar for visingsretning, utsnitt og låseposisjonar. Dei blir ikkje viste i utgåve 09. `build_seated_joint_figures.py` kan lage den siste inngangen frå CAD-kjelda. Berre dei tre endelege `frame2_*_clear.json`-figurane blir brukte på side 15; `frame2-contact-crop-check.json` og `frame2-joint-clear-manifest.json` dokumenterer kontrollen.

Den mekaniske kjelda er `lukketsvane/formnerd`, revisjon `88cc8f327fba72e6517ea30dcadc4e978419da37`, mappe `A1/Stereo-Multigrip-R04-USB18`. Utgåve 09 byggjer vidare på manualen frå revisjon `4edd7a6d080fa1cf1630d8333e097dfc4e302d10` og endrar berre dokumentasjon og illustrasjonar. Printstøtta kjem frå sliceren og er ikkje ein del av CAD-geometrien som er vist. IKEA-referansane er samanlikningsgrunnlag; originalfigurane og skrifter derfrå er ikkje kopierte inn i manualen.

[Les monteringsmanualen](https://chatgpt.com/space/page_f9400752da088191973e1efe3b0adebc)

[Fotorealistiske produkt- og ESP32-rendringar](https://chatgpt.com/space/page_35e5106e33c48191a225c9edb196e0ee)
