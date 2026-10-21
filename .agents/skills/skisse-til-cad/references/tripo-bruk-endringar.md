# Endringar i tripo-bruk.md

Endringsnotat for den publiserte Tripo-oppskrifta. Referansar til arbeidsnotat viser kjeldekontrollen i FormNerd-prosjektet, ikkje filer som følgjer denne pakken.

## Forkortingar

**Kontrollar og notat**

- **K1**: adversarial kontroll av «Vel kjede» og «Referansebilete og master».
- **K2**: kontroll av «Deler og lågpoly».
- **K3**: kontroll av CLI, konvertering og køyring.
- **V**: CLI/SDK-lesaren og notatet `notat/verktoy.md`.
- **Dom**: domen i kontrollen: *feil*, *delvis*, *stadfesta (retting)*, *ikkje_i_docs* eller *mangel*.

**Kjeldefiler**

Stiar er relative til `tripo-docs/`.

- `dev/` er `developers/`.
- `v2/` er `web/`.
- `CLI/` er `npm-tripo-cli-0.7.2/x/package/`.
- **PDF-decimate** er `0fadf6e2-mesh-decimate.txt`.

**Praksis**

- **P-A1** er `A4/arkiv/tripo-a1/`.
- **P-Entropi** er `A4/arkiv/entropi-a3/README.md` og `A4/arkiv/entropi-tripo/`, i tillegg til transkripsjonen frå Entropi-økta (`kartlegg/entropi-okt.md`).

## 0. Innleiing

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 1 | Grunnlaget nemner no v2-dokumentasjonen, seks PDF-ar og CLI-pakken, ikkje berre developers.tripo3d.ai | K1 og K3, mangel «Kjeldeoversikta» | `dev/docs_*.md`, `v2/*.txt`, `*.txt` i rota |
| 2 | Ny merking skil dokumentert, praksis (A1/Entropi), *metodeval*, *udokumentert* og *kjeldekonflikt* | Krav i oppgåva | – |

## 1. Vel kjede

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 3 | Ny rad: skisse eller konsept utan vald form går gjennom biletsteget og så H3.1 | Krav i oppgåva | `dev/docs_generation-image-to-model_standard.md` («task_id … text_to_image or image_to_image»), P-Entropi |
| 4 | Rada «Éi vald skisse»: eksplisitt `model`, `model_seed`, `texture=false` og `pbr=false`. Grunngitt med at v3.1 blir tilrådd til 3D-print, og med skisse-showcasen. Rekkjefølgja er merkt *metodeval* | K1 stadfesta, mangel «Modellval for print» | `dev/docs_models-and-versions.md`, `dev/showcase_drawing-to-3d.txt`, `dev/docs_mesh-segment.md` |
| 5 | Rada multiview: berre fire slotar, ingen topp-, botn- eller 3/4-vising, same lys | K1 stadfesta (retting) | `dev/docs_generation-multiview-to-model_standard.md` |
| 6 | Rada `generate_parts`: eksplisitt `texture=false` og `pbr=false`, utan `quad`, 1004 ved utelaten `texture`, +20 kreditt, berre H3.0/H3.1, leveringsforma udokumentert | K1 delvis, K2 | `dev/docs_generation-image-to-model_standard.md`, `dev/models_v3-1.txt` |
| 7 | Rada «Godkjend eksisterande mesh»: `task_id` gjeld berre generation-taskar. Andre meshar går som `file_token`/URL (maks 150 MB). Ingen lovnad om uendra geometri | K1 stadfesta (retting) | `dev/docs_mesh-segment.md` |
| 8 | Rada «Lettare CAD-referanse»: eksplisitt `model`, default `v2.0`, 500–20 000, ingen toleranse. Lokal desimering lagt til som alternativ | K1 stadfesta (retting) | `dev/docs_mesh-decimate.md`, `dev/docs_changelog.md`, P-Entropi |
| 9 | Rada lågpoly: P2 kostar 100. P1/P2 manglar `geometry_quality`, `generate_parts` og `smart_low_poly`, og P1 manglar `quad` | K1 stadfesta (retting) | `dev/models_p2.txt`, `dev/docs_changelog.md` |
| 10 | Rada Smart Segment: «aldri task-ID» | K1 og K2 | `dev/docs_mesh-smartsegment.md`, `CLI/skill/commands/process.md` |
| 11 | Ny praksislinje med dei faktiske kjedene og kostnadene i A1 (160) og Entropi (175) | Praksis | P-A1 `tripo-receipts.json`, P-Entropi README |

## 2. Biletsteget før 3D (ny seksjon)

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 12 | Flyten konseptvariantar → val → to3d-bilete → godkjenning. Juryen i Entropi, krava til to3d-biletet og at A1 gjekk direkte, er merkte som praksis | Krav i oppgåva | P-Entropi README, `payloads/g_to3d.json`, P-A1 `provenance.json`, `dev/docs_generation-image-to-model_standard.md` («clean background and minimal occlusion») |
| 13 | Åtvaring om at skjulte sider blir oppdikta (spegla USB-C, søkar som vender ut mot sidene) | Praksis | P-Entropi README («Kjende avvik») |
| 14 | Modelltabell med pris, maks referansar, dokumentert eigenskap og praksis | Krav i oppgåva | `dev/pricing.txt`, `dev/docs_generation-image-to-image.md`, `dev/docs_models-and-versions.md`, P-Entropi |
| 15 | Lås `model`. Default per endepunkt. Ingen `seed` for bilete | Dokumentert | `dev/docs_generation-text-to-image.md`, `dev/docs_generation-image-to-image.md` |
| 16 | `quality`, `aspect_ratio`, `size`, 2K som tilrådd storleik (*metodeval*) og `mask` berre i OpenAI-kompatibel modus | Dokumentert | `dev/docs_generation-image-to-image.md`, `dev/docs_openai-compat-images.md`, `dev/pricing.txt` |
| 17 | Prompt: engelsk eller kinesisk, `--no`, maks 600 ord. Grensa på om lag 1 800 teikn med 1004 er merkt som praksis | Dokumentert og praksis | `dev/docs_generation-text-to-image.md`, P-Entropi README, payload-lengder i `entropi-tripo/payloads/` |
| 18 | `3d_enhance` er valfri AI-nytolking. `sketch_to_render` og `print_clay` står berre i v2-API-et og i CLI 0.7.2 (kjeldekonflikt) | K1, mangel «Skisse som input» | `dev/docs_generation-image-to-image.md`, `v2/image-generation_advanced-image-generation.txt` |
| 19 | Referansar som `file_token`: `/v3/files` tek JPEG/PNG opp til 20 MB, WebP går via presign, URL må vere offentleg. Inputgrensene for image-to-image | K1, mangel «Opplastingsgrenser» | `dev/docs_files.md`, `dev/docs_files-presign.md`, `dev/docs_generation-image-to-image.md` |
| 20 | `inputs` 4/10/16 med `image[n]`. Kjeldekonflikt om `input` er påkravd. I Entropi fungerte `inputs` åleine | Dokumentert og praksis | `dev/docs_generation-image-to-image.md`, `entropi-tripo/payloads/d_fusion_refs.json` |
| 21 | Levetid for `file_token`: udokumentert i v3. Ved 2019, last opp på nytt | K3, mangel «Levetid for opplasting» | `CLI/skill/common-errors.md` |
| 22 | Kjeding med `task_id` til image-to-model. Image-to-multiview tek ikkje task-ID | K1, mangel «Kjeding av eksakt input» | `dev/docs_generation-image-to-model_standard.md`, `dev/docs_generation-image-to-multiview.md` |
| 23 | Concurrency 1 for alle biletendepunkta. Saldoen er delt, og kreditt skal sporast per task | K1, mangel «Concurrency». Praksis | `dev/docs_rate-limits.md`, P-Entropi (2000), P-A1 `tripo-receipts.json` (8 andre taskar) |
| 24 | Image-to-multiview og Edit Multiview: 10 og 5 kreditt, ingen modell eller seed, førebuing til multiview-to-model. At AI-visingar ikkje er målte, er merkt *metodeval* | K1 delvis | `dev/docs_generation-image-to-multiview.md`, `dev/docs_generation-edit-multiview.md`, `dev/pricing.txt` |

## 3. Referansebilete og master

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 25 | WebP er lista på endepunktet, men `/v3/files` tek berre JPEG/PNG. Bruk PNG | K1 delvis | `dev/docs_generation-image-to-model_standard.md`, `dev/docs_files.md`, `dev/docs_files-presign.md`, `v2/model-generation_image-to-model-v3-0-v3-1.txt` |
| 26 | «Gjer formval før generering» er merkt *metodeval* | K1 ikkje_i_docs | – |
| 27 | Multiview: same lys, tre format som punktliste. Task-forma skal vere nøyaktig `[{"task_id":…}]` frå `generate_multiview_image` eller `edit_multiview_image`. `multiview_to_model` fungerer ikkje | K1 delvis | `dev/docs_generation-multiview-to-model_standard.md` |
| 28 | Kva left og right tyder, er udokumentert. CLI-en les filnamn. Maks filstorleik er ikkje oppgitt, så 20 MB blir tilrådd | K1 mangel «Multiview-slotar og filnamn» | `dev/docs_generation-multiview-to-model_standard.md`, `CLI/skill/commands/generate.md` |
| 29 | «Godkjenn kvar vising» er merkt *metodeval* | K1 ikkje_i_docs | `dev/docs_cli.md` (næraste kontrollråd) |
| 30 | v3.1 er tilrådd til print. Lås versjonen i alle kall, også API-kall | K1 stadfesta (retting), mangel «Modellval» | `dev/docs_models-and-versions.md`, `CLI/skill/commands/generate.md` |
| 31 | Ultra kostar +20 og løftar taket frå 1,5 M til 2 M. ComfyUI tilbyr det berre i image-modus | K1 stadfesta (retting) | `dev/docs_generation-image-to-model_standard.md`, `dev/models_v3-1.txt`, `dev/docs_comfyui-nodes.md` |
| 32 | 20 mot 30 kreditt. Ikkje kopier multiview-dømet utan `pbr:false` | K1 stadfesta (retting) | `dev/docs_generation-multiview-to-model_standard.md`, `dev/models_v3-1.txt` |
| 33 | Ikkje send `texture_quality` i geometrikøyringar. At han ikkje gir geometri, er merkt som slutning | K1 delvis | `v2/model-generation_image-to-model-v3-0-v3-1.txt` |
| 34 | `face_limit`: utelat for adaptiv topologi. Grensene 2018, 150 MB og 80 000 (mesh/uv), CLI-ens P1-regel og showcase-taket på 50 000. Filstorleikar frå A1 og Entropi | K1 mangel «face_limit for master». Praksis | `dev/docs_generation-image-to-model_standard.md`, `dev/docs_mesh-segment.md`, `dev/docs_error-handling.md`, `dev/docs_changelog.md`, `dev/docs_cli.md`, `dev/showcase_drawing-to-3d.txt`, P-A1 `manifest.json` og `release-info.json`, P-Entropi README |
| 35 | Aldri `quad` på masteren (FBX, 10 000 flater) | K1 mangel «quad på master» | `dev/docs_generation-image-to-model_standard.md` |
| 36 | Ikkje set `compress`, og sjekk `extensionsRequired`. Både A1 og Entropi las GLB-en med trimesh | K1 mangel «compress». Praksis | `dev/docs_generation-image-to-model_standard.md`, `v2/model-generation_image-to-model-v3-0-v3-1.txt`, P-A1 `tools/prepare_print.py` |
| 37 | Kjeldekonflikt om `export_uv`: API-sida dokumenterer han for H, CLI-dokumentet seier «P series only» | K1 stadfesta (retting) | `dev/docs_generation-image-to-model_standard.md`, `CLI/skill/commands/generate.md`, `tripo-cli-verification.json` |
| 38 | `auto_size`: berre teksturert (v2). Eininga utan han er udokumentert. Ikkje følg CLI-oppskrifta for print. Normalisert eining er praksis (A1 1,0, Entropi 0,98) | K1 stadfesta (retting). Praksis | `v2/model-generation_image-to-model-v3-0-v3-1.txt`, `CLI/skill/examples/print.md`, P-A1 `print/poses.json`, `entropi-tripo/models/m_hero_mesh_qa.json` |
| 39 | Seed: eksplisitt `model_seed` (`--seed` eller `-p model_seed`). Han blir ikkje returnert. `redo` og `-n` gir nye seeds | K1 delvis, mangel «Seed-verktøy» | `dev/docs_generation-image-to-model_standard.md`, `dev/docs_task-query.md`, `CLI/skill/commands/make.md`, `dev/docs_cli.md` |
| 40 | `enable_image_autofix` finst ikkje i v3-multiview. Ikkje send han, sidan han kan gi 2002 | K1 delvis | `dev/docs_generation-multiview-to-model_standard.md`, `v2/model-generation_multiview-to-model-v3-0-v3-1.txt`, `dev/docs_error-handling.md` |
| 41 | Følgja av `orientation`: aksane må fastsetjast i CAD | K1 stadfesta (retting) | `dev/docs_generation-image-to-model_standard.md` |
| 42 | `export_orientation` blir ikkje send ved generering (default `+x`), og sluttorienteringa blir sett i convert eller lokalt. Y-opp og eksplisitt aksematrise er praksis | K1 stadfesta (retting). Praksis | `dev/docs_generation-image-to-model_standard.md`, `dev/docs_models-convert.md`, P-Entropi (rotasjon til Z-opp), P-A1 `print/poses.json` |
| 43 | Output er GLB og førehandsbilete. Ingen lovnad om vasstett mesh. Opne kantar i Entropi er praksis. Lagre SHA-256 for opphavet | K1 mangel «Outputformat og vasstettheit» og «Mellombelse resultat» | `dev/docs_quick-start.md`, `dev/docs_models-convert.md`, `dev/showcase_drawing-to-3d.txt`, `entropi-tripo/models/m_hero_mesh_qa.json` |

## 4. Deler og lågpoly

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 44 | `generate_parts`: krev `model ≥ v3.0-20250812`, gir 1004 og skal sendast utan `quad`. `smart_low_poly` fjernar delane utan feilmelding, men jobben blir betalt. +20 kreditt. Leveringsforma er udokumentert, og completion krev segment-task | K2 stadfesta (retting), K1 mangel «generate_parts-output» | `dev/docs_generation-image-to-model_standard.md`, `CLI/skill/common-errors.md`, `dev/models_v3-1.txt`, `dev/docs_mesh-complete.md` |
| 45 | Segment: inputtypar spesifiserte. v2 reknar segmentering til stega som «rebuild or modify». Samanlikn med masteren. Defaultverdiane i v2 er nemnde og låste (*metodeval*) | K2 delvis og stadfesta (retting) | `dev/docs_mesh-segment.md`, `v2/animation_rig-v2-5-20260210.txt` |
| 46 | `ref_image`: offisielt namn, `file_token`/URL, blir ignorert. Maska er berre nemnd i biletteksten, og formatet er udokumentert. Kjeldekonflikt om v1 (1004 eller ignorert). Bruk PNG. `mask_url` som utgangspunkt | K2 delvis, mangel «ref_image på v1» | `dev/docs_mesh-segment.md`, `CLI/skill/commands/process.md`, `dev/docs_comfyui-nodes.md`, `dev/docs_files.md`, `dev/docs_mesh-smartsegment.md` |
| 47 | Delnamn: kvar dei står, er udokumentert, så dei blir lesne frå GLB-nodane. A1 hadde `tripo_part_N`. Etikettar er overflateområde | K2 delvis, mangel «Delnamn». Praksis | `dev/docs_mesh-segment.md`, `dev/docs_models-convert.md`, P-A1 `parts-map.json` |
| 48 | Smart Segment: aldri task-ID. Pris 85/55 (CLI-default `model`). Kva transformasjonen tyder, er udokumentert, og CLI-en fyller inn identitet. Om modus `model` genererer eller importerer, er udokumentert. `granularity`, `hint`, `seg_model_url`, `prompt`, `mask_url`, `seg_task_id` og `model_task_id`. I A1 gav `fine` 11 delar | K2 delvis, mangel «Smart Segment-parametrar og -output». Praksis | `dev/docs_mesh-smartsegment.md`, `CLI/skill/commands/process.md`, `dev/pricing.txt`, `tripo-cli-verification.json`, P-A1 `segmentation-result.json` og `tripo-receipts.json` |
| 49 | Completion: tek ikkje `file_token` eller URL. Delar frå `generate_parts` og Smart Segment er udokumenterte som input. Pris 50/30, og `completion_mode` finst berre i v3. Risikoen ved cap er merkt *metodeval*. Kjeldekonflikt om samanslåing og praksis frå A1 (node 5 kopla saman). CLI-oppskrifta for print brukar `ai_completion` | K2 stadfesta (retting), ikkje_i_docs, mangel «Completion kan slå saman» og «CLI sin print-oppskrift». Praksis | `dev/docs_mesh-complete.md`, `dev/pricing.txt`, `v2/mesh-editing_mesh-completion-v1-0-20250506.txt`, `v2/animation_rig-v2-5-20260210.txt`, `v2/get-started_overview.txt`, `CLI/skill/examples/print.md`, P-A1 `parts-map.json` og `tripo-receipts.json` |
| 50 | H Smart Low Poly: +10, krev ≥ v3.0-20250812, kan feile, feila taskar blir ikkje fakturerte, nedre grense 1 000 i v2, `quad` gir FBX | K2 stadfesta (retting), mangel «quad tvingar FBX» og «Feil ved for kompleks modell» | `dev/docs_generation-image-to-model_standard.md`, `dev/models_v3-1.txt`, `dev/docs_billing.md`, `v2/model-generation_image-to-model-v3-0-v3-1.txt` |
| 51 | P-serien: `model` er påkravd, og API-et byter aldri sjølv. P1 manglar òg `smart_low_poly`, `generate_parts` og `geometry_quality`, og gir 400 ved `quad`. Grensene for P1 og P2. Preview. 100 kreditt. CLI-en vel P1 ved «low-poly request» og fjernar parametrar med ei åtvaring | K2 delvis og stadfesta (retting) | `dev/docs_generation-image-to-model_p.md`, `dev/docs_changelog.md`, `dev/models_p2.txt`, `dev/docs_cli.md`, `CLI/skill/commands/make.md` |
| 52 | «Smart Low Poly» har tre tydingar. ComfyUI har begge, og v2 brukar `highpoly_to_lowpoly`. Task-typen i A1 og CLI-en | K2 stadfesta (retting), mangel «Namnekonflikt». Praksis | `dev/docs_comfyui-nodes.md`, `v2/mesh-editing_smart-low-poly-p-v2-0-20251225.txt`, `dev/docs_migration-v2-to-v3.md`, P-A1 `tripo-receipts.json`, `tripo-cli-verification.json` |
| 53 | Decimate: punktliste. v1 krev `face_limit` og støttar verken `bake` eller `part_names`; tala står berre i PDF-en. Grensene og prisane for v2/v3. Reduksjonsfaktor om lag 100. `smart_uv` gir 400/1004. `bake=false`. Segment-task-ID er ikkje gyldig dokumentert input, så kjeda er merkt som delvis udokumentert | K2 delvis og stadfesta (retting), mangel «Decimate bake og v1-krav» | PDF-decimate, `dev/docs_mesh-decimate.md`, `dev/docs_changelog.md`, `dev/pricing.txt`, `CLI/skill/commands/process.md`, `tripo-cli-verification.json` |
| 54 | Praksis: retopologien i A1 vart berre førehandsvising (0,35 MB). Lokal desimering i Entropi gav maks 0,115 mm avvik | Praksis | P-A1 `manifest.json` og `README.md`, P-Entropi README |

## 5. Konkrete CLI-oppskrifter

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 55 | Verifikasjonssetninga er presisert: builder-kalla er ikkje CLI-flaggparsing, og flagga for generate/mesh er berre lesne i dokumentasjonen | K3 delvis | `tripo-cli-verification.json` (`scope`, `cli_plans`, `request_builder_checks`) |
| 56 | **Fjerna** `export TRIPO_CLIENT_APP=codex TRIPO_DISTRIBUTION_CHANNEL=codex_plugin`. Lagt inn `TRIPO_ANALYTICS_ENABLED=0 TRIPO_NO_UPDATE_CHECK=1` | K3 feil | `CLI/README.md`, `dev/docs_cli.md` (miljøvariabeltabell) |
| 57 | Lås CLI-en til 0.7.2 og Node 20 eller nyare. `install`, `npx` og `update` hentar siste versjon | K3 mangel «Låsing av CLI-versjon» | `dev/docs_cli.md`, `CLI/README.md`, `CLI/skill/SKILL.md` |
| 58 | make-linja: `to3d.png`, `--seed 12345`, same argument som planen `master_h31`. Defaultverdiane er forklarte | K3 stadfesta (retting) | `tripo-cli-verification.json`, `CLI/skill/commands/make.md` |
| 59 | generate-linja: `-p model_seed=12345`, kommentar om at ho kostar 40 og går straks | K3 delvis | `CLI/skill/commands/generate.md`, `CLI/dist/commands/generate.js` (K3), `dev/models_v3-1.txt` |
| 60 | segment-linja: kommentar om 40 kreditt og Beta, defaultverdiane låste | K3 stadfesta (retting) | `CLI/skill/commands/process.md`, `dev/pricing.txt` |
| 61 | complete-linja: `housing`/`cover` bytte ut med `DEL_A`/`DEL_B`, delnamn frå GLB-nodane, 30 kreditt | K3 stadfesta (retting), K2 mangel «Delnamn» | `dev/docs_mesh-segment.md`, `dev/pricing.txt` |
| 62 | decimate v1: kommentar om 10 kreditt og påkravd `face_limit` | K3 stadfesta (retting) | PDF-decimate, `dev/pricing.txt` |
| 63 | decimate v3: kommentar om 35 kreditt og at `--no-bake` ikkje verkar utan tekstur | K3 stadfesta (retting) | `dev/pricing.txt`, `CLI/skill/commands/process.md` |
| 64 | Ny linje: `tripo task watch TASK_ID --download` | K3 stadfesta (retting) | `dev/docs_cli.md` |
| 65 | Berre `make` har dry-run. generate og mesh går straks, headless `--yes` og `@last`. Krev task-ID og kostnadsgrense (*metodeval*) | K3 stadfesta, mangel «Betalt jobb utan stadfesting» | `CLI/skill/commands/make.md`, `CLI/skill/commands/process.md` |
| 66 | Utdatamappa er `tripo-out/<namn>-<id8>/`. Kontekstfil og `TRIPO_HOME` | K3 delvis og stadfesta (retting) | `CLI/skill/commands/make.md`, `CLI/dist/core/download.js`, `CLI/skill/commands/account.md` |
| 67 | Modellval i generate med og utan `--model` | K3 stadfesta (retting) | K3 (`chooseModel`) |
| 68 | `--for print`: v3.1, `texture=false`, `pbr=false`, convert til Advanced 10, 30 totalt. «Watertight» er ein merkelapp. Konflikt om «3MF (colored)» | K3 stadfesta (retting), V | `CLI/dist/knowledge/scenarios.js`, `CLI/skill/examples/print.md`, `dev/pricing.txt`, `dev/docs_models-convert.md`, `dev/docs_cli.md` |
| 69 | Tidsavbrot: exit-kode 6 har to tydingar, minst 15 minutt, default 1800 s | K3 mangel «Timeout og exit-kodar» | `dev/docs_cli.md`, `CLI/skill/SKILL.md`, `CLI/skill/commands/make.md` |

## 6. Konvertering og CAD

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 70 | Kina-host `openapi.tripo3d.com`. Tasken er bunden til nøkkel og region | K3 stadfesta (retting), mangel «Taskar er bundne» | `dev/docs_introduction.md`, `CLI/skill/commands/account.md`, `v2/task-query_get-your-task-result.txt`, `dev/docs_task-batch-query.md` |
| 71 | Formatlister konkretiserte. 3MF og USDZ kan berre lastast opp via presign. Kjeldekonflikt om `.gltf` | K3 stadfesta (retting) | `dev/docs_files.md`, `dev/docs_files-presign.md`, `dev/docs_models-convert.md`, `CLI/skill/commands/task.md` |
| 72 | Convert kan ikkje lage GLB, så ta vare på originalane | K3 delvis | `dev/docs_models-convert.md`, `dev/docs_mesh-smartsegment.md` |
| 73 | Ingen einingsparameter. `scale_factor` gir Advanced-pris. Skaler til mm lokalt | K3 stadfesta (retting), mangel «Einingar» | `dev/docs_models-convert.md`, `dev/pricing.txt`, `dev/docs_generation-image-to-model_standard.md` |
| 74 | «quad kan» er endra til «quad tvingar». Konflikt med CLI-en. `force_symmetry` berre med quad. Advanced 10 mot 5, og CLI-en har fleire utløysarar | K3 stadfesta (retting), mangel «Når convert vert Advanced-pris» | `dev/docs_models-convert.md`, `dev/pricing.txt`, `CLI/skill/commands/process.md`, `CLI/dist/knowledge/params.js` |
| 75 | `bake_scale` blir avvist av CLI 0.7.2 | K3 stadfesta (retting) | `CLI/dist/knowledge/models.js`, `CLI/dist/knowledge/params.js` |
| 76 | STL mistar teksturar, 3MF er einfarga, vertex-fargar gjeld berre OBJ/GLTF | K3 mangel «Formatavgrensingar ved print» | `dev/docs_models-convert.md`, `v2/export_conversion.txt` |
| 77 | Alle val i eitt convert-kall | K3 mangel «Konvertering i fleire steg» | `v2/export_conversion.txt` |
| 78 | `part_names` på convert. Om convert tek ein segment-task, er udokumentert | K2 mangel «Eksport av enkeltdelar», K3 mangel «Convert av segment-/retopologi-output» | `dev/docs_models-convert.md`, `CLI/skill/commands/process.md`, `v2/export_conversion.txt` |
| 79 | Ingen Tripo-convert for print i repoet (*metodeval*). Reint formatbyte kostar 5 | V tilråding, K3 stadfesta (retting) | `notat/verktoy.md` §8, `dev/pricing.txt` |

## 7. Køyring, kostnad og kjeldekonfliktar

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 80 | Ny liste med åtte krav til klienten (*metodeval* bygd på dokumentasjonen) | V, K3 manglar | `dev/docs_task-lifecycle.md`, `dev/docs_task-query.md`, `v2/task-query_get-your-task-result.txt`, `dev/docs_cli.md`, `CLI/skill/commands/task.md`, `dev/docs_mesh-smartsegment.md`, `dev/docs_mesh-uv.md`, `dev/docs_rate-limits.md`, `dev/docs_changelog.md` |
| 81 | Praksis: A1 brukte CLI-en, Entropi sin eigen klient. `verktoy/tripo.py` manglar fleire av punkta | V. Praksis | `notat/verktoy.md` §7 |
| 82 | Innsending: retry berre ved 429, spørjingar 3×, konflikt med error-handling. Sjekk `frozen`. Henting frå same task i både Entropi og A1 | K3 stadfesta (retting), mangel «Retry-reglar». Praksis | `dev/docs_cli.md`, `CLI/skill/common-errors.md`, `dev/docs_error-handling.md`, `dev/docs_account.md`, `entropi-tripo/images/d_fusion_refs.json`, P-A1 `LES-MEG.txt` |
| 83 | Samtidigheit og rate limit per pool og nøkkel | K3 mangel «Samtidigheit og rate limits», K2 mangel «Samtidigheitsgrense» | `dev/docs_rate-limits.md` |
| 84 | Utgått URL og utgått task er skilde. `missed`. Levetid 60 s, 5 min eller ikkje oppgitt. Lagringstid «XXX». Webhooks og batch på 100 | K3 delvis og stadfesta (retting), manglar «Task-statusar», «Batch-query og webhooks» og «Lagringstid» | `dev/docs_sdk.md`, `dev/docs_task-lifecycle.md`, `CLI/skill/common-errors.md`, `dev/docs_task-batch-query.md`, `v2/other_support-faq.txt`, `v2/task-query_get-your-task-result.txt`, `CLI/skill/commands/task.md`, `dev/docs_webhooks.md` |
| 85 | Kostnad: frosen kreditt, feila taskar blir ikkje fakturerte, desimaltal, 403/2010, separate kredittar, går ikkje ut. Peikar til tabellen | K3 stadfesta, mangel «Rekneskap og avvisingar» | `dev/docs_billing.md`, `dev/docs_task-query.md`, `dev/docs_changelog.md`, `dev/docs_error-handling.md`, `v2/other_support-faq.txt` |
| 86 | **Retta** SDK-påstanden: fem låste SDK-ar, og berre Python står på 0.4.2 | K3 feil | `dev/docs_sdk.md` |
| 87 | **Fjerna** «SDK-master 1.0.0/API v3 og V2-slutt 31. oktober 2026». Berre at `tripo3d` 1.x finst, er dokumentert (via ComfyUI). Ingen V2-sluttdato | K3 ikkje_i_docs | `dev/docs_migration-v2-to-v3.md`, `dev/docs_comfyui-nodes.md` |
| 88 | **Fjerna** lenkjene til SDK README og CHANGELOG frå kjeldelista, fordi dei verken har hash eller lagra kopi | K3 ikkje_i_docs, mangel «Kjeldeoversikta» | `tripo-dokumentasjon.json` (`additional_sources`) |
| 89 | Refine og Stylize presiserte: fjerna i ComfyUI, `refine` finst i CLI-en og begge i Java-SDK-en, men ingen v3-side. Irrelevante for kjeda | K3 delvis | `dev/docs_comfyui-nodes.md`, `dev/docs_sdk.md`, `CLI/skill/commands/process.md` |
| 90 | CLI 0.7.2 avviser texture v3.5 og `bake_scale`. Etterslep i rig-check og rig-default | K3 stadfesta (retting), V fallgruver | `tripo-cli-verification.json`, `CLI/skill/commands/process.md`, `dev/docs_changelog.md`, `dev/docs_animations-rig.md` |
| 91 | Telemetri er på som default, og `TRIPO_ANALYTICS_ENABLED=0` slår han av | K3 mangel «Telemetri» | `dev/docs_cli.md`, `CLI/README.md` |
| 92 | Kommandonamna i GPT-6/Astra-cookbooken avvik frå CLI-sida | V fallgruver | `dev/cookbook_gpt-6-astra-3d-game-scene-workflow.txt`, `dev/docs_cli.md` |
| 93 | Kjeldeoversikta dekkjer ikkje v2, PDF-ane eller showcase-sidene | K1 og K3 mangel «Kjeldeoversikta» | `tripo-dokumentasjon.json` |

## 8. Kostnad og grenser per steg (ny seksjon)

| # | Endring | Dom | Kjelde |
| --- | --- | --- | --- |
| 94 | Tabell over 12 steg med endepunkt, dokumentert pris, grenser, pool og praksis | Krav i oppgåva. K1, K2 og K3 mangel «Kostnad per steg» | `dev/pricing.txt`, `dev/models_v3-1.txt`, `dev/models_p2.txt`, `dev/docs_rate-limits.md`, `dev/docs_files.md`, `dev/docs_files-presign.md`, `dev/docs_generation-image-to-image.md`, `dev/docs_mesh-*.md`, `dev/docs_changelog.md`, `v2/get-started_pricing.txt` |
| 95 | Døme: dokumentert kjede 145 kreditt, A1 faktisk 160, Entropi faktisk 175 med fordeling | Dokumentert og praksis | `dev/pricing.txt`, P-A1 `tripo-receipts.json`, P-Entropi README og `entropi-tripo/*/` |

## 9. Vurdert, men ikkje teke med

Desse tema er utelatne fordi dei er irrelevante for kjeda skisse → print:

- splat
- rig og animasjon
- detaljar om `/models/texture`
- `tripo batch run`
- `tripo mcp`
- Codex-pluginen

Feltet `[image 1]` i CLI-dokumentet og `image[1]` i API-et er òg utelate, sidan `image[1]` fungerte i praksis.

## 10. Følgjeendringar tilrådde i andre filer (ikkje gjorde)

**`tripo-og-cad.md`**

| Line | Endring | Grunnlag |
| --- | --- | --- |
| l. 9 og l. 20 | `task_id` gjeld berre generation-taskar | K2 |
| l. 11 | «Auto-modellert» bør bli «mogleg endra». CLI-dokumentet tyder på import | K2 |
| l. 12 | Legg til `generate_parts` (+20) som alternativ til Smart Segment image (85) | K2 |
| l. 13 | Namngi H3.0/H3.1 | K2 |
| l. 15 | Completion kan slå saman delar | K2 og P-A1 |
| l. 18 | Det automatiske modellvalet gjeld berre CLI-en | K2 |
| l. 24 | Seed gjeld berre generering | K2 |

**`SKILL.md`**

| Line | Endring | Grunnlag |
| --- | --- | --- |
| l. 31 | Transformasjonen for Smart Segment er udokumentert | K2 |
| l. 33 | Legg til 1004 og kravet `model ≥ v3.0-20250812` | K2 |
| l. 35 | v1 krev `face_limit` | K2 |
| Steg 1 | Vis til biletsteget i `tripo-bruk.md` | K1 |

**`tripo-dokumentasjon.json`**

- Legg til v2-sidene, PDF-ane og showcase-sidene med hash (K1, K3).
- Fjern `additional_sources` eller legg ved hasha kopiar (K3).

**`tripo-cli-verification.json`**

Legg til ein test av flaggparsinga for `generate` og `mesh`. Til no er berre request-builderen prøvd (K3).

**`verktoy/tripo.py` og `kjor.py`**

Desse manglane er funne av V:

- terminalstatusane `banned` og `expired` manglar
- timeout er 900 s, men bør vere minst 1800 s
- tasken blir ikkje spurd på nytt før nedlasting
- filendinga blir ikkje sett etter URL eller Content-Type
- `seg_model_url`, `mask_url` og `uv_render_url` blir ikkje henta
- `Retry-After` blir ignorert
- parallelliteten er ikkje avgrensa per pool
- `task.json` og SHA-256 manglar
- nøkkelen blir lesen ved import
- lokal validering manglar
