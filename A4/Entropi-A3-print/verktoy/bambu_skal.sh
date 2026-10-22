#!/bin/bash
# Slicar delte skal-delar for P1S: bambu_skal.sh <namn> <stl> [stl ...] -> print/<namn>.gcode.3mf
set -euo pipefail
HER="$(cd "$(dirname "$0")" && pwd)"
P="$HER/../print"
APP="$(flatpak info --user --show-location com.bambulab.BambuStudio)/files"
RT="$(flatpak info --user --show-location org.gnome.Platform//50)/files"
GL="$(ls -d "$(dirname "$(dirname "$RT")")"/../../../org.freedesktop.Platform.GL.default/x86_64/25.08/active/files 2>/dev/null | head -1)"
TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT
bambu() {
  (cd "$TMPD" && xvfb-run -a -s "-screen 0 1280x1024x24 +extension GLX" env LD_LIBRARY_PATH="$APP/lib:$RT/lib/x86_64-linux-gnu:$RT/lib:$GL/lib" \
    LIBGL_DRIVERS_PATH="$GL/lib/dri" __EGL_VENDOR_LIBRARY_DIRS="$GL/glvnd/egl_vendor.d" LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe \
    "$RT/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2" "$APP/bin/bambu-studio" "$@")
}
NAMN="$1"; shift
STL=(); for f in "$@"; do STL+=("$(realpath "$f")"); done
python3 "$HER/bambu_profil.py" "$APP/share/BambuStudio/profiles/BBL" "$P/bambu/profil" > /dev/null
INN=(--orient 0 --arrange 1 --load-settings "$P/bambu/profil/maskin.json;$P/bambu/profil/prosess.json" --load-filaments "$P/bambu/profil/filament.json")
bambu --debug 1 "${INN[@]}" --export-3mf "$P/$NAMN.3mf" "${STL[@]}"
bambu --debug 1 "${INN[@]}" --slice 0 --export-3mf "$P/$NAMN.gcode.3mf" "${STL[@]}"
python3 - "$P" "$APP/share/BambuStudio/profiles/BBL" "$P/$NAMN.gcode.3mf" <<'PY'
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).parent / "verktoy"))
from bambu_etter import modell_id, rett_og_les
P, BBL, f = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
r = rett_og_les(f, modell_id(P, BBL))[0]
s = P / "bambu" / "skal.json"
d = json.loads(s.read_text()) if s.exists() else {}
d[f.name] = r
s.write_text(json.dumps(d, indent=2, ensure_ascii=False))
print(json.dumps({f.name: (r["tid"], r["vekt_g"], r["objekt"], r["kontroll"])}, ensure_ascii=False))
PY
