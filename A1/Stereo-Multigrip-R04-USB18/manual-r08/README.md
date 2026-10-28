# ENTROPI R04 USB18 monteringsmanual

Utgåve 08 er ein 17-siders monteringsmanual med modellavleidde strekteikningar, store detaljutsnitt og korte nynorske instruksjonar. Arbeidsgangen går frå reingjering etter Tree Hybrid-print og prøving av låsane til montering, kameratest og demontering.

Side 5 viser kva delar av beraren som skal stå att når den mellombelse printstøtta blir fjerna. Side 6 skil korte og lange kilar og viser ein prøvelås utan elektronikk. Kortinnføringa er eit stoppunkt på side 7: rett innføring bakfrå kolliderer i nominell CAD, og ein annan innføringsveg og fysisk passform er ikkje verifiserte. Illustrasjonane endrar ikkje R04-geometrien.

## Filer

- `output/ENTROPI_R04_Monteringsmanual.pdf`: manualen i A4 med 17 sider.
- `pages/`: éin PNG per side.
- `source/build_manual.py`: portabel PDF-byggjar.
- `source/fonts/`: skrifter og lisens.
- `figures/`, `vector/` og `vectors/`: faktisk brukt figurgrunnlag og scenedata.
- `used-assets.json`: eksakte avhengigheiter for PDF-byggjaren.
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

Den mekaniske kjelda er `lukketsvane/formnerd`, revisjon `88cc8f327fba72e6517ea30dcadc4e978419da37`, mappe `A1/Stereo-Multigrip-R04-USB18`. Utgåve 08 byggjer vidare på manualen frå revisjon `eb0481b9862fcf8a39269bbb6d9ebf01326f39e1` og endrar berre dokumentasjon og illustrasjonar. Printstøtta kjem frå sliceren og er ikkje ein del av CAD-geometrien som er vist.

[Les monteringsmanualen](https://chatgpt.com/space/page_f9400752da088191973e1efe3b0adebc)

[Fotorealistiske produkt- og ESP32-rendringar](https://chatgpt.com/space/page_35e5106e33c48191a225c9edb196e0ee)
