#!/bin/bash
# Hentar heile Tripo-API-dokumentasjonen (v3, engelsk) som markdown frå llms.txt og sitemap til ei mappe.
set -euo pipefail
UT="${1:?bruk: tripo_docs.sh <utmappe>}"
mkdir -p "$UT"
curl -sL --max-time 30 https://developers.tripo3d.ai/llms.txt -o "$UT/_llms.txt"
curl -sL --max-time 30 https://developers.tripo3d.ai/sitemap.xml \
  | grep -o '<loc>[^<]*/en/docs[^<]*</loc>' | sed 's#</\?loc>##g' \
  | while read -r u; do
      namn="$(echo "${u#*/en/}" | tr '/' '_')"
      curl -sL --max-time 40 "$u.md" -o "$UT/$namn.md" || echo "feil: $u" >&2
    done
ls "$UT" | wc -l
