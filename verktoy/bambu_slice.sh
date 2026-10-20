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
BBL="$APP/share/BambuStudio/profiles/BBL"
python3 "$HER/bambu_profil.py" "$BBL" "$P/bambu/profil"
INN=(--orient 0 --arrange 1 --load-settings "$P/bambu/profil/maskin.json;$P/bambu/profil/prosess.json" --load-filaments "$P/bambu/profil/filament.json")
slice() {
  local namn="$1"; shift
  bambu --debug 1 "${INN[@]}" --slice 0 --export-3mf "$P/bambu/$namn.gcode.3mf" "$@"
  python3 "$HER/bambu_etter.py" "$BBL" "$P/bambu/profil/maskin.json" "$P/bambu/$namn.gcode.3mf" "$P/bambu/$namn.json"
}
slice "$PROSJEKT-hus-P1S" "$P/fremre_skal.stl" "$P/bakre_skal.stl" "$P/innmatsramme.stl"
slice "$PROSJEKT-provebitar-P1S" "$P"/provebitar/prove_*.stl
