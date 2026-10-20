#!/bin/bash
# Slicar A3-delane med Bambu Studio (Flathub-versjonen) og dei offisielle P1S-profilane.
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
python3 "$HER/bambu_profil.py" "$APP/share/BambuStudio/profiles/BBL" "$P/bambu/profil"
R="$P/printretning"
DELAR=("$R/kropp.stl" "$R/luke.stl" "$R/stabelhaldar.stl" "$R/utloysar.stl" "$R/usb-lokk.stl")
INN=(--orient 0 --arrange 1 --load-settings "$P/bambu/profil/maskin.json;$P/bambu/profil/prosess.json" --load-filaments "$P/bambu/profil/filament.json")
bambu --debug 1 "${INN[@]}" --export-3mf "$P/A3-Entropi-P1S.3mf" "${DELAR[@]}"
bambu --debug 1 "${INN[@]}" --slice 0 --export-3mf "$P/A3-Entropi-P1S.gcode.3mf" "${DELAR[@]}"
bambu --debug 1 "${INN[@]}" --slice 0 --export-3mf "$P/A3-Entropi-P1S-utan-haldar.gcode.3mf" "$R/kropp.stl" "$R/luke.stl" "$R/utloysar.stl" "$R/usb-lokk.stl"
mkdir -p "$P/haldar-p1s"
for f in "$R"/haldar-variantar/*.stl; do
  bambu --debug 1 "${INN[@]}" --slice 0 --export-3mf "$P/haldar-p1s/$(basename "${f%.stl}").gcode.3mf" "$f"
done
python3 "$HER/bambu_etter.py" "$P" "$APP/share/BambuStudio/profiles/BBL"
