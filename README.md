# formnerd

Formutvikling med AI-genererte bilete og 3D-modellar frå Tripo-API-et.

| Mappe | Innhald |
| --- | --- |
| [`A2/`](A2/) | Stereoskopisk kamerahus for to ESP32-CAM: referansar, tre designrundar, 3D-modellar og innmatsanalyse |
| [`verktoy/`](verktoy/) | Felles skript: Tripo-oppgåver, mesh-QA og innmatsanalyse |

Krev `TRIPO_API_KEY` i miljøet og Python-pakkane `requests`, `trimesh` og `scipy`.

- `verktoy/tripo.py` – opplasting, oppgåver, polling og nedlasting
- `verktoy/kjor.py jobbar.json ut.json [parallelle]` – køyrer ei liste med Tripo-oppgåver og lastar ned resultata. Biletgenerering tillèt berre éi oppgåve om gongen, så bruk `1` der.
- `verktoy/mesh_qa.py fil.glb …` – topologisjekk (rå og sveisa analysekopi)
- `verktoy/innmat.py linser.json [prosessar]` – minste kroppsstorleik som gøymer elektronikken, sjå `A2/README.md`
