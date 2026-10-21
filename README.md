# formnerd

Formutvikling for FormNerd med AI-genererte bilete og 3D-modellar frå Tripo-API-et. Kvar designmappe er sjølvstendig, med eigen README, referansar, resultat og skript.

| Mappe | Design |
| --- | --- |
| [`A4/`](A4/README.md) | Entropi: oppdatert CAD v05, prentdelar, rendringar, referansar og heile det tidlegare A1/A3-arbeidet |
| [`A2/`](A2/README.md) | Stereoskopisk kamerahus for to ESP32-CAM med skjult elektronikk: tre designrundar, 3D-modellar, innmatsanalyse, printpakke for P1S og monteringsrettleiing. Lagt bort (oktober 2026) |

## Felles verktøy

[`verktoy/`](verktoy/README.md) er pipelinen frå A2, gjord om til eit verktøy for alle prosjektmapper. Han går frå referansebilete til ferdig printpakke: Tripo-konsept og 3D, innmatsanalyse, hus med skøyt, ramme og hol, printkontroll, Bambu P1S-slicing, renderar og monteringsrettleiing i IKEA-stil. Kvart skript tek prosjektmappa som argument, til dømes `python3 verktoy/bygg_hus.py A2`.

- Skillen `formnerd-hus` (`.claude/skills/formnerd-hus/SKILL.md`) skildrar steg, krav og fallgruver, og blir lasta automatisk i Claude Code i dette repoet.
- Den portable skillen [`skisse-til-cad`](.agents/skills/skisse-til-cad/SKILL.md) er publisert i [lukketsvane/skisse-til-cad](https://github.com/lukketsvane/skisse-til-cad) (Apache-2.0; `claude plugin marketplace add lukketsvane/skisse-til-cad` eller `npx skills add lukketsvane/skisse-til-cad`; bygd med `publisering/skisse-til-cad/bygg.sh`). Han bevarer heile kjeda frå skisse via Tripo og mekanisk CAD til IKEA-liknande montering, med offisielle kjelder og 12 offlinekontrollar av CLI 0.7.2.
- [Skisse til CAD som plugin](plugins/skisse-til-cad/README.md) har installasjonsrettleiing, støtte og offentlege nedlastingar av plugin og skill, versjon 0.1.2.
- Workflowen `kontroller-hus` (`.claude/workflows/kontroller-hus.js`) er ein uavhengig, målande kontroll av ei printpakke, med `args: {"prosjekt": "A2"}`.

Tripo-skripta krev `TRIPO_API_KEY` i miljøet.
