#!/bin/bash
# Slicar husdelane og prøvebitane i eit prosjekt med Bambu Studio (Flathub) og dei offisielle P1S-profilane.
set -euo pipefail
HER="$(cd "$(dirname "$0")" && pwd)"
PROSJEKT="${1:?bruk: bambu_slice.sh <prosjektmappe, t.d. A2>}"
P="$(cd "$HER/.." && pwd)/$PROSJEKT/print"
APP="$(flatpak info --user --show-location com.bambulab.BambuStudio)/files"
RTREF="$(flatpak info --user -m com.bambulab.BambuStudio | sed -n 's/^runtime=//p')"
RT="$(flatpak info --user --show-location "$RTREF")/files"
GL="$(ls -d "$(dirname "$(dirname "$RT")")"/../../../org.freedesktop.Platform.GL.default/x86_64/*/active/files 2>/dev/null | tail -1)"
TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT
bambu() {
  (cd "$TMPD" && xvfb-run -a -s "-screen 0 1280x1024x24 +extension GLX" env LD_LIBRARY_PATH="$APP/lib:$RT/lib/x86_64-linux-gnu:$RT/lib:$GL/lib" \
    LIBGL_DRIVERS_PATH="$GL/lib/dri" __EGL_VENDOR_LIBRARY_DIRS="$GL/glvnd/egl_vendor.d" LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe \
    "$RT/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2" "$APP/bin/bambu-studio" "$@")
}
python3 "$HER/bambu_profil.py" "$APP/share/BambuStudio/profiles/BBL" "$P/bambu/profil"
INN=(--orient 0 --arrange 1 --load-settings "$P/bambu/profil/maskin.json;$P/bambu/profil/prosess.json" --load-filaments "$P/bambu/profil/filament.json")
slice() {
  local namn="$1"; shift
  bambu --debug 1 "${INN[@]}" --slice 0 --export-3mf "$P/bambu/$namn.gcode.3mf" "$@"
  python3 - "$P/bambu/$namn.gcode.3mf" "$P/bambu/$namn.json" <<'PY'
import json, re, sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
info = z.read("Metadata/slice_info.config").decode()
ps = json.loads(z.read("Metadata/project_settings.config"))
plater = sorted(n for n in z.namelist() if re.match(r"Metadata/plate_\d+\.gcode$", n))
ut = {"programvare": re.search(r'X-BBL-Client-Version" value="([^"]+)', info).group(1),
      "skrivar": ps["printer_settings_id"], "prosess": ps["print_settings_id"], "filament": ps["filament_settings_id"][0],
      "plate": ps["curr_bed_type"], "stotte": f'{ps["support_type"]}, berre fraa plata={ps["support_on_build_plate_only"]}',
      "veggar": ps["wall_loops"], "fyll": ps["sparse_infill_density"], "lag_mm": ps["layer_height"], "plater": []}
for n in plater:
    g = z.read(n).decode(errors="ignore")[:40000]
    ut["plater"].append({"fil": n, "tid": re.search(r"total estimated time: ([^\n;]+)", g).group(1).strip(),
                         "lag": int(re.search(r"total layer number: (\d+)", g).group(1))})
ut["vekt_g"] = [float(v) for v in re.findall(r'key="weight" value="([\d.]+)', info)]
ut["objekt"] = re.findall(r'<object identify_id="\d+" name="([^"]+)"', info)
ut["åtvaringar"] = re.findall(r'<warning msg="([^"]+)"', info)
json.dump(ut, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
print(json.dumps(ut, indent=1, ensure_ascii=False))
PY
}
slice "$PROSJEKT-hus-P1S" "$P/fremre_skal.stl" "$P/bakre_skal.stl" "$P/innmatsramme.stl"
slice "$PROSJEKT-provebitar-P1S" "$P"/provebitar/prove_*.stl
