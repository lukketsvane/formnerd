# Colani Stereo R14 | samla 3D-vising

Denne revisjonen samlar den **faktiske Tripo R12-ytterforma** med ei 3D-mekanisk visualisering av R13-komponentane.

- `Colani_R14_Complete_Visible.glb`: samla 3D-modell for inspeksjon, med fram-/bakskal, batterivogge, PCB-haldar, optikk og nominell elektronikk.
- `Colani_R14_Complete_Visible.blend`: redigerbar Blender-scene.
- `renders/`: produktfoto og tekniske framstillingar, eitt bilete per vising.
- `mechanical_interferences.json`: dokumenterte kollisjonar.

Ytterskalet har nominelt 96 × 145 × 46 mm, veggtjukkleik 2,4 mm og 29,5 mm optisk base. Innmaten er geometrisk bygd etter kjelda i R13; batteriet er flytt frå y=2 til y=10 mm i denne visingsmodellen.

## Fysisk og mekanisk status

**Ikkje produksjonsgodkjent.** Statisk volumkontroll avslørte at battery envelope skjærer gjennom Tripo-ytterskalet med 16 723 mm³ og bakre skalveggen med 11 027 mm³. Det same gjeld høgre PCB med 1 218 mm³ utanfor yttervolum og 1 283 mm³ inn i framskalet. Dette er visingsfeil i innpakkinga, ikkje godkjende konstruksjonar.

R14 er ein **ekte kombinert 3D-visingsmodell**, ikkje ferdig mekanisk verifisert CAD. Verken usbportane, avstand til FPC-kabel eller fysisk passform er kontrollert. R12 sine printskalfiler er framleis eigne separate filer; R13 innmat STEP er analoge mekaniske delar, ikkje ein integrert STEP-solid av den organiske Tripo-ytterforma.

Sjå `01_finished_hero_actual_CAD.png`, `05_open_back_with_electronics.png`, `06_exploded_outer_inner.png` og `10d_tuned_product_iso_white.png`.

### Framdrift

R15-undersøking med større skal-djupn 55 mm har redusert, men ikkje eliminert kollisjonar. Ho er difor ikkje utgjeven som sluttgeometri.
