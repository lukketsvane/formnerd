#!/bin/bash
# Set saman det frittståande repoet for skisse-til-cad (github.com/lukketsvane/skisse-til-cad) i <utmappe>.
set -euo pipefail
HER="$(cd "$(dirname "$0")" && pwd)"
ROT="$(cd "$HER/../.." && pwd)"
UT="${1:?bruk: bygg.sh <utmappe>}"
mkdir -p "$UT/skills" "$UT/.agents/skills"
rm -rf "${UT:?}/skills/skisse-til-cad"
cp -r "$ROT/.agents/skills/skisse-til-cad" "$UT/skills/"
mkdir -p "$UT/skills/skisse-til-cad/scripts"
cp "$ROT/verktoy/tripo.py" "$ROT/verktoy/kjor.py" "$ROT/verktoy/tripo_docs.sh" "$UT/skills/skisse-til-cad/scripts/"
cp -r "$HER/.claude-plugin" "$HER/README.md" "$HER/LICENSE" "$UT/"
ln -sfn ../../skills/skisse-til-cad "$UT/.agents/skills/skisse-til-cad"
python3 - "$UT/skills/skisse-til-cad" <<'PY'
import sys
d = sys.argv[1]
for fil, gammal, ny in (
    ("SKILL.md", "Stiar merka **Praksis** i referansane (t.d. `A4/arkiv/...`, `verktoy/tripo.py`) viser til det repoet.",
     "Stiar merka **Praksis** i referansane (t.d. `A4/arkiv/...`) viser til det repoet. `scripts/` i denne skillen har ein Tripo v3-klient (`tripo.py`, `kjor.py`) som følgjer krava i [Tripo-oppskrifta](references/tripo-bruk.md), og `tripo_docs.sh`, som hentar heile Tripo-dokumentasjonen på nytt."),
    ("references/tripo-bruk.md", "`verktoy/tripo.py` og `verktoy/kjor.py` følgjer punkta 1–7 og validerer punkt 8 lokalt (utan `/mesh/uv`-grensa) sidan 20.10.2026; `python3 verktoy/tripo.py valider jobbar.json` sjekkar ei jobbliste utan kostnad.",
     "`scripts/tripo.py` og `scripts/kjor.py` i denne skillen (i formnerd: `verktoy/`) følgjer punkta 1–7 og validerer punkt 8 lokalt (utan `/mesh/uv`-grensa) sidan 20.10.2026; `python3 scripts/tripo.py valider jobbar.json` sjekkar ei jobbliste utan kostnad."),
):
    p = f"{d}/{fil}"
    s = open(p).read()
    assert s.count(gammal) == 1, (fil, gammal[:40])
    open(p, "w").write(s.replace(gammal, ny))
PY
mkdir -p "$UT/dist" && cp "$(ls "$ROT"/dist/skisse-til-cad-*.skill | sort -V | tail -1)" "$UT/dist/skisse-til-cad.skill"
claude plugin validate "$UT" | tail -1
