# verktoy – frå konseptbilete til printpakke

Felles verktøy for formnerd-prosjekt. Køyr alt frå rota av repoet med prosjektmappa som argument (`P` = t.d. `A2`). Heile arbeidsgangen, krava til `kontroll.json` og fallgruvene står i skillen [`formnerd-hus`](../.claude/skills/formnerd-hus/SKILL.md). A2 er referanseprosjektet.

| Skript | Bruk | Gjer |
| --- | --- | --- |
| `tripo.py` | `upload fil` · `balance` · `task <id>` | Tripo v3-klient: opplasting, oppgåver, polling og nedlasting (krev `TRIPO_API_KEY`) |
| `kjor.py` | `jobbar.json ut.json [parallelle]` | køyrer Tripo-jobbar og lastar ned bilete og GLB (biletgenerering: `1`) |
| `mesh_qa.py` | `model.glb …` | topologisjekk av meshar |
| `visningar.mjs` | `node verktoy/visningar.mjs model.glb visningar.png` | fire visningar (front, 3/4, topp og bak) av ein GLB |
| `innmat.py` | `P/analyse/linser.json [prosessar]` | om elektronikken får plass i forma, og minste breidd |
| `bygg_hus.py` | `P` | skal, skøyt, ramme, hol, kontrollar, STL, 3MF, prøvebitar og `kontroll.json` frå `P/print/parametrar.json` |
| `bambu_slice.sh` | `P` | slicar huset og prøvebitane for Bambu P1S (Bambu Studio frå Flathub, `xvfb-run`; profilar via `bambu_profil.py`) |
| `renderar.py` | `P` | fargerenderar: samla, bak, eksplodert og snitt |
| `rettleiing.py` | `P` | monteringsrettleiing i IKEA-stil (PNG og PDF) |
| `hus.py`, `strek.py`, `strek.mjs` | – | felles geometri (voxelfyll, avstandsfelt, level-sett) og line art-rendering |

Krav: Python med `numpy`, `scipy`, `trimesh`, `manifold3d`, `scikit-image`, `Pillow` og `requests`, og Node med Playwright/Chromium. Køyr `npm install --prefix verktoy` for three.js.
