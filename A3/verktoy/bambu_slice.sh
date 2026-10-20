#!/bin/bash
# Slicar A3-delane med Bambu Studio (Flathub-versjonen) og dei offisielle P1S-profilane.
set -euo pipefail
HER="$(cd "$(dirname "$0")" && pwd)"
P="$HER/../05-print"
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
python3 "$HER/bambu_profil.py" "$APP/share/BambuStudio/profiles/BBL" "$P/bambu/profil"
DELAR=("$P/printretning/kropp.stl" "$P/printretning/luke.stl" "$P/printretning/stabelhaldar.stl" "$P/printretning/utloysar.stl" "$P/printretning/usb-lokk.stl")
INN=(--orient 0 --arrange 1 --load-settings "$P/bambu/profil/maskin.json;$P/bambu/profil/prosess.json" --load-filaments "$P/bambu/profil/filament.json")
bambu --debug 1 "${INN[@]}" --export-3mf "$P/A3-Entropi-P1S.3mf" "${DELAR[@]}"
bambu --debug 1 "${INN[@]}" --slice 0 --export-3mf "$P/A3-Entropi-P1S.gcode.3mf" "${DELAR[@]}"
python3 - "$P" <<'PY'
import json, re, sys, zipfile, pathlib
P = pathlib.Path(sys.argv[1])
z = zipfile.ZipFile(P / "A3-Entropi-P1S.gcode.3mf")
g = z.read("Metadata/plate_1.gcode").decode(errors="ignore")[:20000]
info = z.read("Metadata/slice_info.config").decode()
ps = json.loads(z.read("Metadata/project_settings.config"))
out = {
    "programvare": re.search(r'X-BBL-Client-Version" value="([^"]+)', info).group(1),
    "skrivar": ps["printer_settings_id"], "prosess": ps["print_settings_id"], "filament": ps["filament_settings_id"][0],
    "plate": ps["curr_bed_type"], "stotte": f'{ps["support_type"]}, berre fraa plata={ps["support_on_build_plate_only"]}',
    "veggar": ps["wall_loops"], "fyll": ps["sparse_infill_density"], "lag_mm": ps["layer_height"],
    "tid": re.search(r"total estimated time: ([^\n;]+)", g).group(1).strip(),
    "vekt_g": float(re.search(r'key="weight" value="([\d.]+)', info).group(1)),
    "lag": int(re.search(r"total layer number: (\d+)", g).group(1)),
    "miniatyr": any(n.endswith(".png") for n in z.namelist()),
    "objekt": re.findall(r'<object identify_id="\d+" name="([^"]+)"', info),
}
(P / "bambu" / "slicing.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps(out, indent=1, ensure_ascii=False))
PY
