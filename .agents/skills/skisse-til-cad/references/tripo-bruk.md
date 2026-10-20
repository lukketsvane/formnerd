# Tripo bruk frå skisse til CAD

Metodegrunnlaget er kontrollert 20. oktober 2026 mot heile den engelske v3-dokumentasjonen på developers.tripo3d.ai. Det er òg kontrollert mot den eldre v2-dokumentasjonen på docs.tripo3d.ai, PDF-utgåvene av seks v3-sider, modell- og prissidene og dokumenta i `tripo-cli@0.7.2`. Sjå `tripo-dokumentasjon.json` og `tripo-cli-verification.json`. Oppskrifta er ei ingeniørfagleg tilråding. Ho påstår ikkje at Tripo lagar målsett CAD.

**Merking.** Tekst utan merke er dokumentert i kjeldene under avsnittet. **Praksis A1** og **Praksis Entropi** er observert i eitt tidlegare prosjekt i dette repoet og er ikkje lova av Tripo. *(metodeval)* er vår eiga tilråding. *(udokumentert)* tyder at kjeldene ikkje seier noko. *(kjeldekonflikt)* tyder at kjeldene er usamde.

## Vel kjede etter kva som alt er godkjent

| Utgangspunkt | Føretrekt kjede | Kvifor |
| --- | --- | --- |
| Skisse eller konsept utan vald form | Biletsteget nedanfor → eitt godkjent to3d-bilete → H3.1 image-to-model | Formval i bilete kostar 5–20 kreditt per forsøk (opptil 50 med chat_image `quality=max`), ein 3D-master 20–60. Rekkjefølgja er *(metodeval)* |
| Éi vald skisse eller eitt vald bilete | H3.1 image-to-model med eksplisitt `model`, `model_seed`, `texture=false` og `pbr=false` → vurder master → ordinær segmentering ved behov | Tripo tilrår v3.1 til 3D-print, og handteikna skisser er eit dokumentert brukstilfelle. Segment tek image_to_model-tasken direkte. Rekkjefølgja er *(metodeval)* |
| Fleire konsistente faktiske visingar | H3.1 multiview-to-model med slotane `front`, `left`, `back` og `right` → vurder master | Fleire vinklar gir betre geometri. Det finst berre fire slotar, så topp, botn og 3/4 kan ikkje brukast. Same objekt, same lys |
| Ny generering der delar er ønskte frå starten | H3.0/H3.1 med `generate_parts=true`, `texture=false` og `pbr=false`, utan `quad` og `smart_low_poly`. Kostar +20 kreditt | Utelaten `texture` gir 1004, og `quad` blir ignorert. `smart_low_poly` fjernar delane utan feilmelding. Leveringsforma for delane er *(udokumentert)* |
| Godkjend eksisterande mesh | Er det ein generation-task, send task-ID-en til ordinær segmentering. Ein lokalt redigert, importert eller konvertert mesh går som `file_token` eller URL (maks 150 MB) | `task_id` er berre dokumentert for text-, image- og multiview_to_model. Ingen side lovar uendra geometri |
| Behov for lettare CAD-referanse | Lag ein `/mesh/decimate` frå masteren med eksplisitt `model` (`v1.0` basic eller `v3.0` retopologi), eller desimer lokalt | Default er `v2.0`. v2/v3 tek 500–20 000 trekantar. Ingen avvikstoleranse er dokumentert |
| Enkel form der lågpoly er sjølve målet | H3.x `smart_low_poly` (+10), eller eksplisitt P1 (40 i v2-prislista, ikkje lista i v3) eller P2 Preview (100 kreditt) | P1/P2 manglar `geometry_quality`, `generate_parts` og `smart_low_poly`. P1 manglar òg `quad` |
| Behov for auto-modellert deling | Smart Segment i eiga grein, med `file_token`/URL og aldri task-ID | Rekn resultatet som ei ny eller geometrisk endra utgåve |

**Praksis A1:** vald bilete → v3.1 Ultra utan tekstur (40) → Smart Segment `model`/`fine` (55) → `quick_cap` (30) → v3.0-retopologi med 20 000 flater som eiga førehandsvising (35), til saman 160 kreditt. **Praksis Entropi:** konseptvariantar → to3d-bilete → v3.1 Ultra med HD-tekstur (60) → lokal desimering og reparasjon, til saman 175 kreditt.

Kjelder: [H image](https://developers.tripo3d.ai/en/docs/generation-image-to-model/standard), [H multiview](https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/standard), [modellar](https://developers.tripo3d.ai/en/docs/models-and-versions), [segmentering](https://developers.tripo3d.ai/en/docs/mesh-segment), [Smart Segment](https://developers.tripo3d.ai/en/docs/mesh-smartsegment), [retopologi](https://developers.tripo3d.ai/en/docs/mesh-decimate), [P image](https://developers.tripo3d.ai/en/docs/generation-image-to-model/p), [P2](https://developers.tripo3d.ai/en/models/p2), [changelog](https://developers.tripo3d.ai/en/docs/changelog), [skisse-showcase](https://developers.tripo3d.ai/en/showcase/drawing-to-3d), [prisar](https://developers.tripo3d.ai/en/pricing). Praksis: `A4/arkiv/tripo-a1/tripo-receipts.json` og `A4/arkiv/entropi-a3/README.md`.

## Biletsteget før 3D

Tripo lagar og redigerer bilete i same API. Gjer formvala her, der eit forsøk er billeg, og send berre eitt godkjent bilete vidare til 3D *(metodeval)*.

1. **Konseptvariantar.** Bruk `image-to-image` med skissa som referanse. `text-to-image` tek ikkje referansebilete. Lag éin variant per idé med eitt kall kvar *(metodeval)*. **Praksis Entropi:** først ei kalibreringskøyring, så seks konseptvinklar med eitt kall kvar. Tre uavhengige domarar rangerte dei etter konsept/semiotikk, industridesign/gjennomføring og om dei eigna seg for 3D.
2. **Val.** Brukaren eller juryen vel éin variant. Lagre biletet, task-ID-en og SHA-256.
3. **Eige to3d-bilete.** Rediger den valde varianten (`input` = varianten) til eit reint rekonstruksjonsbilete. Dokumentasjonen tilrår berre «clean background and minimal occlusion» og minst 256 × 256 px. **Praksis Entropi:** to3d-biletet var 1:1 med eitt objekt sentrert og om lag 10 % marg, kvit bakgrunn og jamt, nøytralt og mjukt lys. Det hadde mjuk kontaktskugge, skarp silhuett, matte materiale og 3/4-vising framfrå, litt ovanfrå (25–30°). Det hadde ingen glød, LED, transparens, krom, sterke refleksar, tekst, logo eller hender. **Praksis A1:** det valde biletet gjekk rett til 3D utan eige to3d-steg.
4. **Godkjenn før 3D** *(metodeval)*. Eitt bilete definerer ikkje skjulte sider. **Praksis Entropi:** den skjulte sida vart ei spegling av grepsida med ein ekstra USB-C, og søkaren vende ut mot sidene. Planlegg skjulte sider med multiview eller i CAD.

| Modell | Kreditt ≤1K / 2K / 4K | Maks ref. | Dokumentert | Praksis |
| --- | --- | --- | --- | --- |
| `seedream_v5` | 5 / 5 / 5 | 4 | Default for image-to-image, «strongest editing, style transfer, and multi-image fusion». Tek ikkje `aspect_ratio` | Entropi: avvist, først for lang prompt og så grensa for samtidige jobbar (2000). Gav ikkje noko bilete |
| `banana_pro` | 15 / 15 / 20 | 10 | «higher quality editing», `aspect_ratio` er støtta | Entropi: kalibrering, fire av seks variantar og to3d. Gav dei to beste variantane |
| `chat_image_2.5_sunburst` | 10 / 10 / 15 | 16 | «keeps untouched parts of the image closest to the original» | Ikkje prøvd. Kandidat til målretta to3d-redigering |
| `chat_image_2.5_flare` | 10 / 10 / 15 | 16 | Rask, kvalitet på nivå med `chat_image_2` | Entropi: éin variant med `quality=medium` (10) |
| `chat_image_1` / `chat_image_1.5` | – | – | Blir pensjonerte 23.10.2026 og 1.12.2026 | Ikkje bruk |

- **Lås og lagre.** Set `model` i kvart kall. Defaulten er `seedream_v4` for text-to-image og `seedream_v5` for image-to-image. Biletendepunkta har ingen `seed`, så same prompt gir eit nytt bilete. Last ned med ein gong.
- **Parametrar.** `quality` gjeld berre `chat_image_2` og 2.5-modellane, og andre modellar gir feil. `high`, `xhigh` og `max` kostar 2–5 gonger meir. `aspect_ratio` gjeld berre banana-serien. seedream og chat_image brukar `size`, som har default `2048x2048`. Hald deg på 2K: 4K kostar meir på banana-serien og chat_image, og ein 4K-PNG kan passere 20 MB-grensa ved ny opplasting *(metodeval)*. OpenAI-kompatibel `/v3/openai/images/edits` er einaste stad med `mask` for inpainting, med same pris og samtidigheit.
- **Prompt.** Skriv på engelsk eller kinesisk, med det viktigaste først og negative ord etter `--no`. Text-to-image tilrår maks 600 engelske ord. **Praksis Entropi:** seedream_v5 avviste ein for lang prompt med 1004, og grensa vart observert ved om lag 1 800 teikn. banana_pro tok 1 587–1 779 teikn og chat_image_2.5_flare 1 628. CLI-dokumentet oppgir ≤ 1024 teikn *(kjeldekonflikt)*. Hald prompten kort og test grensa per modell.
- **Hjelpemal.** `template=3d_enhance` på image-to-image («enhance for 3D generation») er valfri og gir AI-nytolking. v2-vala `sketch_to_render` og `print_clay` står ikkje på v3-API-sidene, men CLI 0.7.2 (`skill/commands/generate.md`) listar dei for text-to-image og image-to-image *(kjeldekonflikt)*. Ikkje bygg kjeda på dei.
- **Referansar som `file_token`.** Last opp lokale filer med `POST /v3/files`. Han tek bilete i JPEG og PNG opp til 20 MB. WebP, BMP og TIFF krev `POST /v3/files/presign` (PUT innan 30 minutt), og ein URL må vere offentleg. Bruk PNG *(metodeval)*. Inputgrensene på image-to-image er 20 MB, 36 MP, sideforhold 1/3–3 og minst 14 px. `webp` blir avvist på somme ruter.
- **Fleire referansar.** `inputs` tek inntil 4 (seedream), 10 (banana) eller 16 (chat_image) bilete, som prompten viser til som `image[1]`, `image[2]` og så vidare. Sida merkar `input` som påkravd, men dømet med fleire bilete sender berre `inputs` *(kjeldekonflikt)*. **Praksis Entropi:** `inputs` med skisse og to referanserenderingar, utan `input`, gjekk gjennom på banana_pro.
- **Levetid.** Kor lenge ein `file_token` varer, står ikkje i v3. CLI-dokumentet kallar dei kortlivde: ved feil 2019, last opp på nytt.
- **Kjeding.** `image-to-model` tek `task_id` frå `text_to_image` og `image_to_image` direkte, så det godkjende biletet blir brukt utan ny nedlasting og opplasting. Er tasken gammal eller utgått, last opp den lagra PNG-en *(metodeval)*. `image-to-multiview` tek berre `file_token` eller URL.
- **Samtidigheit og saldo.** Alle fire biletendepunkta deler éin plass per konto (concurrency 1), så køyr dei etter kvarandre. **Praksis Entropi:** seks parallelle kall gav 2000. Saldoen gjeld heile kontoen. I Entropi brukte noko anna same API-nøkkel samstundes, og i A1 køyrde 8 andre taskar på same konto i same tidsrom. Spor derfor kreditt per task og ikkje som differanse i saldoen.
- **Multiview-bilete.** `image-to-multiview` (10 kreditt) lagar fire visingar frå eitt bilete og har verken modell-, prompt- eller seed-parameter. `edit-multiview` (5 kreditt per redigert bilete) rettar enkeltvisingar. Dokumentasjonen omtalar dei som førebuing til multiview-to-model. AI-visingar er ikkje målte sider av produktet *(metodeval)*.

Kjelder: [text-to-image](https://developers.tripo3d.ai/en/docs/generation-text-to-image), [image-to-image](https://developers.tripo3d.ai/en/docs/generation-image-to-image), [multiview-bilete](https://developers.tripo3d.ai/en/docs/generation-image-to-multiview), [rediger visingar](https://developers.tripo3d.ai/en/docs/generation-edit-multiview), [OpenAI-kompatibel](https://developers.tripo3d.ai/en/docs/openai-compat-images), [filer](https://developers.tripo3d.ai/en/docs/files), [presign](https://developers.tripo3d.ai/en/docs/files-presign), [modellar](https://developers.tripo3d.ai/en/docs/models-and-versions), [prisar](https://developers.tripo3d.ai/en/pricing), [rate limits](https://developers.tripo3d.ai/en/docs/rate-limits), [v2 biletgenerering](https://docs.tripo3d.ai/image-generation/advanced-image-generation.html), `tripo-cli@0.7.2` `skill/common-errors.md`. Praksis: `A4/arkiv/entropi-a3/README.md`, `A4/arkiv/entropi-tripo/payloads/`, `A4/arkiv/tripo-a1/provenance.json` og transkripsjonen frå Entropi-økta 20.10.2026.

## Referansebilete og master

Bruk eit tydeleg motiv, lite okklusjon, rein bakgrunn og minst 256 × 256 px. Endepunktet listar PNG, JPEG og WebP opp til 20 MB, men `POST /v3/files` tek berre JPEG og PNG. WebP krev presign eller URL, og v2-sidene nemner berre JPEG og PNG. Bruk derfor PNG for lokale skisser. Image-to-model har ikkje noko promptfelt for mekanikk: systemet tolkar geometrien frå biletet. Gjer formvala før generering og teikn presis mekanikk i CAD etterpå *(metodeval)*.

Multiview krev ei frontvising og minst éi vising til av same objekt i same lys. Berre slotane `front`, `left`, `back` og `right` finst. Bruk éi av tre former, og bland dei ikkje:

- view-key-array (tilrådd)
- nøyaktig fire posisjonar `[front, left, back, right]`, med `""` for ei manglande vising
- nøyaktig `[{"task_id":"<uuid>"}]` frå ein vellukka Image to Multiview- eller Edit Multiview-task (type `generate_multiview_image` eller `edit_multiview_image`). Ein `multiview_to_model`-task fungerer ikkje her.

Om `left` og `right` er sett frå objektet eller frå kameraet, er *(udokumentert)*. CLI-en les filnamn (`front|back|left|right`) før rekkjefølgja, så namngi filene eksplisitt. Multiview-sida oppgir ingen maks filstorleik, så hald deg til 20 MB. Godkjenn kvar vising før 3D *(metodeval)*.

**Modell og geometri.** Tripo tilrår `v3.1-20260211` til 3D-print og ber om at versjonen blir låst i produksjon. Send `model` eksplisitt i alle API-kall (CLI-alias `tripo-v3.1`), sidan defaulten kan bli endra. `geometry_quality=detailed` er Ultra. Han kostar +20 kreditt og løftar taket for `face_limit` frå 1,5 M til 2 M flater. ComfyUI-noden tilbyr han berre i image-modus. Til print og CAD sender du både `texture=false` og `pbr=false`. `pbr` har default `true` og slår tekstur på att. Rein geometri kostar 20 kreditt, og standard tekstur gjer det til 30. Ikkje kopier H-multiview-dømet, som sender `texture:false` utan `pbr:false`. Send heller ikkje `texture_quality` i geometrikøyringar. v2 forbyr `standard` saman med `texture=false` og `pbr=false`, sjølv om `standard` er default; A1 køyrde utan feltet utan feil. At teksturkvalitet ikkje gir fysisk geometri, er ei slutning.

**Storleik, format og komprimering.** Utelat `face_limit` på masteren. Då blir topologien adaptiv med eit tak på 1,5 M flater, eller 2 M med Ultra. Ein så stor master kan gi 2018 («Model too complex») i seinare steg. Han må vere under 150 MB for mesh-operasjonar og må reduserast til maks 80 000 ekvivalente trekantar før `/mesh/uv`. Utan `--model` vel CLI-en P1 når face-budsjettet er 20 000 eller lågare. Skisse-showcasen brukte eit tak på 50 000 flater. **Praksis:** Ultra-masteren i A1 utan tekstur var ein GLB på 54,6 MB, og etter lukking hadde modellen 2,49 M trekantar. Entropi sin med 4K-tekstur var 62 MB med om lag 2 M trekantar.

Bruk aldri `quad` på masteren: han tvingar FBX og 10 000 flater når `face_limit` manglar. Set heller ikkje `compress`. `geometry` gir meshopt, og v2 seier at meshopt er default. Sjekk `extensionsRequired` i GLB-en før CadQuery eller manifold3d *(metodeval)*. **Praksis:** A1 og Entropi las masteren direkte med `trimesh.load`. Ingen av dei to master-GLB-ane hadde `extensionsUsed` eller `extensionsRequired`, så det var ingen meshopt trass i v2-påstanden.

`export_uv=false` gir raskare generering og mindre fil. API-sida dokumenterer parameteren for H, men CLI 0.7.2 kallar han «P series only» *(kjeldekonflikt)*. Dry-run sende han vidare utan åtvaring, men korleis serveren handsamar han, er ikkje prøvd.

**Skala.** Hald `auto_size=false` og set mål i CAD. Med `auto_size` blir eininga meter utan oppgitt toleranse, og v2 seier at parameteren berre verkar på teksturerte modellar. Ikkje følg CLI-oppskrifta for print, som føreslår `auto_size=true`. Eining og skala utan `auto_size` er *(udokumentert)*. **Praksis:** i A1 var lengste akse nøyaktig 1,0 eining (frå −0,5 til 0,5), i Entropi 0,98. Skaler alltid mot kjende mål.

**Seed.** Set `model_seed` eksplisitt, med `make --seed N` eller `generate -p model_seed=N` i CLI-en. Utan han blir seeden tilfeldig, og task-query dokumenterer ikkje at seeden blir returnert. Same seed og same input gir identisk mesh. `tripo redo` brukar ein ny seed, og `-n/--candidates` lagar inntil fire betalte kandidatar med ulike seeds. Ta vare på dei eksakte inputfilene og den låste modellversjonen.

**Autofix.** `enable_image_autofix` har default `false` på image-to-model (H og P). La han vere av. Multiview-to-model i v3 har ikkje parameteren, så ikkje send han dit: ukjende felt kan gi 2002.

**Orientering.** `orientation=align_image` verkar berre med tekstur, så ein geometrimaster får automatisk orientering. Fastset aksane i CAD. Send ikkje `export_orientation` ved generering, der defaulten er `+x`. Er han sett, kan etterbehandling gi feil orientering sjølv om tasken melder `status: success`. Set ei eventuell sluttorientering i den siste `/v3/models/convert`, eller lokalt. **Praksis:** GLB-en var Y-opp i Entropi og måtte roterast 90° om X til Z-opp. A1 lagra ei eksplisitt akse- og skalamatrise frå kjelde til printer. Kontroller transformasjonane ved innlesing.

**Resultat og opphav.** Generering leverer ein GLB (`output.model_url`) og eit førehandsbilete (`rendered_image_url`). STL og 3MF kjem berre via convert. Ingen API-side lovar vasstett eller manifold mesh. CLI-sida kallar `--for print` «watertight», men presetet har inga reparasjon. **Praksis Entropi:** den rå masteren hadde 63 254 opne kantar langs UV-saumane. Etter sveising på posisjon var det 8 opne og 5 ikkje-manifolde kantar att. Last ned med ein gong. Lagre task-ID, kostnad og SHA-256 for kvar fil, slik skisse-showcasen gjer, og i tillegg request-body *(metodeval)*.

Kjelder: [H image](https://developers.tripo3d.ai/en/docs/generation-image-to-model/standard), [H multiview](https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/standard), [H3.1](https://developers.tripo3d.ai/en/models/v3-1), [modellar](https://developers.tripo3d.ai/en/docs/models-and-versions), [filer](https://developers.tripo3d.ai/en/docs/files), [feil](https://developers.tripo3d.ai/en/docs/error-handling), [changelog](https://developers.tripo3d.ai/en/docs/changelog), [ComfyUI-nodar](https://developers.tripo3d.ai/en/docs/comfyui-nodes), [skisse-showcase](https://developers.tripo3d.ai/en/showcase/drawing-to-3d), [v2 H3 image](https://docs.tripo3d.ai/model-generation/image-to-model-v3-0-v3-1.html), [v2 H3 multiview](https://docs.tripo3d.ai/model-generation/multiview-to-model-v3-0-v3-1.html), `tripo-cli@0.7.2` `skill/commands/{make,generate}.md` og `skill/examples/print.md`. Praksis: `A4/arkiv/tripo-a1/print/poses.json`, `A4/arkiv/tripo-a1/release-info.json` og `A4/arkiv/entropi-tripo/models/m_hero_mesh_qa.json`.

## Deler og lågpoly er ulike val

**Delar ved generering.** H `generate_parts=true` gjeld berre `model ≥ v3.0-20250812`, altså ikkje v2.5, P1 eller P2. Han krev `texture=false` og `pbr=false`, og eit brot gir 1004, også når `texture` er utelaten. Send verken `quad`, som blir ignorert slik at delane kjem som trekantar, eller `smart_low_poly`. `smart_low_poly` vinn utan feilmelding og fjernar delane. Jobben blir truleg fakturert likevel, men om tillegget for parts blir trekt, er *(udokumentert)*. Tillegget er +20 kreditt. Korleis delane blir leverte (nodar og namn i GLB-en), og om dei kan gå vidare til completion eller `part_names`, er *(udokumentert)*. `/mesh/complete` krev ein `mesh/segment`-task. Ta vare på masteren frå den valde genereringa.

**Ordinær segmentering** (40 kreditt) arbeider på ein eksisterande modell. Input er anten task-ID frå text-, image- eller multiview_to_model, eller `file_token`/URL (GLB, GLTF, FBX, OBJ eller STL, maks 150 MB) for alt anna. v3 lovar ikkje uendra geometri, og v2-dokumentasjonen reknar segmentering til stega som «rebuild or modify mesh geometry». Samanlikn den segmenterte GLB-en med masteren før CAD. Defaulten `v1.0-20250506` er geometrisk. `v2.0-20260430` er semantisk og i Beta, med `segmentation_granularity` (`simple`, `balanced` eller `detailed`, default `balanced`) og `split_by_connectivity` (default `true`). Lås begge eksplisitt *(metodeval)*.

**Referansebilete.** `ref_image` finst berre i v2 og heiter offisielt «reference image for semantic analysis». Det tek `file_token` eller ein offentleg URL. Når det er sett, blir granularity og connectivity ignorerte. Berre biletteksten viser at det er ei segmenteringsmaske. Format, fargekoding, synsvinkel og oppløysing er *(udokumentert)*. Send `ref_image` berre med v2.0: CLI-dokumentet seier at v1 gir 1004. ComfyUI-noden sender feltet berre med v2.0, så «v1 ignores them» gjeld noden og er ikkje prov på at serveren godtek det. Lag maska som PNG. `mask_url` frå Smart Segment kan vere eit utgangspunkt *(metodeval)*. Bruk ei maske berre når dei tilsikta delgrensene faktisk er viste.

**Delnamn.** Ingen segmentside fortel kvar etikettane eller delnamna blir leverte. Resultatet har berre `model_url` (GLB) og `rendered_image_url` (webp). Les `part_names` frå nodenamna i GLB-en før completion, decimate eller convert *(udokumentert)*. **Praksis A1:** GLB-en frå Smart Segment hadde nodane `tripo_part_0` til `tripo_part_10`, og `prompt` gav ei skildrande delliste. Semantiske etikettar er overflateområde, ikkje mekaniske skøytar.

**Smart Segment** tek berre `file_token` eller offentleg URL og aldri task-ID, så last ned master-GLB-en og last han opp att. `seg_type=image` (85 kreditt) genererer ein ny modell og segmenterer han. `seg_type=model` (55 kreditt, CLI-default) krev GLB og ein kolonnemajor 4 × 4-`transform` med 16 tal. Sida seier ikkje kva koordinatrammer matrisa koplar saman, og CLI-en fyller inn identitetsmatrisa med ei åtvaring. Om model-modus genererer geometrien på nytt eller berre importerer han, er *(udokumentert)*. CLI-dokumentet nemner ein indre «image_to_model / import task». Rekn geometrien som mogleg endra og samanlikn. Vala er `granularity` (`coarse`, `medium` som er default, eller `fine`, med andre namn enn i segment v2) og `hint`, som namngir delar. Resultatfila heiter `seg_model_url`, ikkje `model_url`. Svaret har òg `prompt` (delliste), `mask_url`, `seg_task_id` og `model_task_id`. Ta vare på alle. **Praksis A1:** `model` med `fine` gav 11 delar for 55 kreditt, og `model_task_id` var ein annan task enn masteren.

**Completion** tek berre task-ID frå ein `mesh/segment`-task, ikkje `file_token` eller URL. Delar frå `generate_parts` eller Smart Segment er ikkje dokumenterte som input. **Praksis A1:** `quick_cap` etter Smart Segment lukka dei 11 delane. Kvitteringa lagra `inner_segment_task_id`, men ikkje kva input completion fekk. Standardmodusen `ai_completion` (50 kreditt) genererer manglande geometri. `quick_cap` (30) lukkar opne grenser utan AI-generering. `completion_mode` finst berre i v3. Oppgi dei faktiske `part_names`, sidan ei utelating rører alle delane. Ein cap kan òg lukke eit tilsikta hol *(metodeval, eiga risikovurdering)*. Eldre offisiell dokumentasjon seier at completion slår delane saman til éin modell *(kjeldekonflikt)*. Kontroller derfor at delane framleis er separate før BOM og printplater. **Praksis A1:** alle 11 nodane overlevde og var vasstette. Node 5 vart likevel kopla saman internt (frontpanel og frontskive), og node 4 og 7 hadde to lukka komponentar kvar. CLI-oppskrifta for «make watertight» køyrer `segment,complete` med `ai_completion` som default, så vel `quick_cap` eksplisitt.

**H Smart Low Poly** (+10 kreditt, berre for `model ≥ v3.0-20250812`) passar enkle motiv og kan feile på komplekse. Mislukka taskar blir ikkje fakturerte. Grensene er 500–20 000 trekantar eller 500–10 000 quads, men v2 har 1 000 som nedre grense for trekantar. `quad` tvingar FBX, så hald deg til trekantar i kjeda GLB → CadQuery/manifold3d.

**P-serien** krev eksplisitt `model`. Utan han køyrer API-et alltid H3.1 og byter aldri til P av seg sjølv. P1 (`P1-20260311`, 50–20 000 flater) og P2 Preview (`P2-20260801`, 48–50 000 trekantar eller 48–25 000 quads, 100 kreditt utan tekstur) støttar ikkje `geometry_quality`, `generate_parts` eller `smart_low_poly`. P1 avviser `quad=true` med 400. P2 er Preview, og Tripo skriv at den komande offisielle utgåva skal betre mesh-stabiliteten. Når `--model` manglar, vel CLI-en P1 ved ein «low-poly request» eller eit face-budsjett på 20 000 eller lågare. Då fjernar han parts og `geometry_quality` og melder det berre som ei åtvaring («P1 does not support … (removed)»). Lås derfor `--model tripo-v3.1` for masteren.

**«Smart Low Poly» er tre ulike ting.** Det er H-genereringsflagget `smart_low_poly`. Det er ComfyUI-noden `TripoSmartLowPoly`, som er retopologi via `/mesh/decimate` (P-v2.0 → `v2.0`, P-v3.0 → `v3.0`). Og det er v2-tasken `highpoly_to_lowpoly` (`P-v2.0-20251225`), som no svarar til `/v3/mesh/decimate`. Generatornoden i ComfyUI har i tillegg sitt eige `smart_low_poly`-flagg. **Praksis A1:** både A1-kvitteringa og request-builderen i CLI-en fører v3.0-retopologien som task-typen `highpoly_to_lowpoly`.

**Retopologi og reduksjon.** `/mesh/decimate` har `v2.0` som default, så set `model` eksplisitt.

- `v1.0` (basic, 10 kreditt) krev `face_limit` (maks 2 M trekantar eller 150 000 quads) og støttar verken `bake` eller `part_names`. Tala manglar i markdown-eksporten, men står i fanene i PDF- og HTML-utgåva og i CLI-dokumentet `process.md`.
- `v2.0` (30 kreditt) og `v3.0` (35 for trekantar, 40 for quads) tek 500–20 000 trekantar eller 500–10 000 quads, og vel adaptivt når grensa er utelaten. Ein master på 2 M flater må altså reduserast om lag 100 gonger.
- `smart_uv` gjeld berre `v3.0` og gir 400/1004 på v1 og v2.
- `bake` har default `true`; set han til `false` for CAD.

Ingen reduksjon har ein oppgitt toleranse. `part_names` er dokumentert for v2/v3, men ein segment-task-ID står ikkje på lista over gyldige `task_id`. Det som passar med inputlista, er `file_token` eller URL til den segmenterte GLB-en, men om `part_names` då blir lesne, er *(udokumentert)*. CLI-verifikasjonen prøvde berre request-builderen.

**Praksis A1:** `v3.0` med 20 000 flater gav ein førehandsvisingsmodell på 0,35 MB, ikkje printgrunnlag. **Praksis Entropi:** lokal kvadrisk desimering til 400 000 trekantar, så pymeshfix, gav ein vasstett STL med største avvik 0,115 mm ved 120 mm breidd, utan Tripo-kostnad. Samanlikn silhuett, hol, ribber og måleavvik før godkjenning.

Kjelder: [H image](https://developers.tripo3d.ai/en/docs/generation-image-to-model/standard), [H-generering](https://developers.tripo3d.ai/en/docs/generation-text-to-model/standard), [P-generering](https://developers.tripo3d.ai/en/docs/generation-image-to-model/p), [P2](https://developers.tripo3d.ai/en/models/p2), [segment](https://developers.tripo3d.ai/en/docs/mesh-segment), [Smart Segment](https://developers.tripo3d.ai/en/docs/mesh-smartsegment), [completion](https://developers.tripo3d.ai/en/docs/mesh-complete), [retopologi](https://developers.tripo3d.ai/en/docs/mesh-decimate) (fanene i PDF-utgåva), [changelog](https://developers.tripo3d.ai/en/docs/changelog), [ComfyUI-nodar](https://developers.tripo3d.ai/en/docs/comfyui-nodes), [CLI](https://developers.tripo3d.ai/en/docs/cli), [v2 rig 2.5](https://docs.tripo3d.ai/animation/rig-v2-5-20260210.html), [v2 oversikt](https://docs.tripo3d.ai/get-started/overview.html), [v2 smart low poly](https://docs.tripo3d.ai/mesh-editing/smart-low-poly-p-v2-0-20251225.html), `tripo-cli@0.7.2` `skill/commands/process.md`, `skill/common-errors.md` og `skill/examples/print.md`. Praksis: `A4/arkiv/tripo-a1/{tripo-receipts,segmentation-result,parts-map}.json` og `A4/arkiv/entropi-a3/README.md`.

## Konkrete CLI-oppskrifter

CLI 0.7.2 er lesen statisk med sha256 frå `tripo-cli-verification.json`. Payload-forma er kontrollert utan nettverk for fem `make --dry-run`-planar og sju kall til den interne request-builderen. Builder-kalla køyrer ikkje `tripo mesh …`, så flaggparsinga for `generate` og `mesh` (`--completion-mode`, `--face-limit`, `--no-bake` og `--model`) er berre lesen i dokumentasjonen. Ingen betalte jobbar eller modellresultat er prøvde. **Praksis A1:** CLI-en lagra utdata i `tripo-out/<namn>-<id8>/`.

Byt ut filnamn, konkrete task-ID-ar og faktiske delnamn. Bruk etablert klient og innlogging. Ikkje les, skriv ut eller lim inn nøklar, og ikkje installer ein ekstra server for denne kjeda. Blir CLI-en installert, lås han til `tripo-cli@0.7.2` (Node 20 eller nyare): både `npm install -g tripo-cli`, `npx` og `tripo update` hentar siste versjon. Ikkje set `TRIPO_CLIENT_APP` eller `TRIPO_DISTRIBUTION_CHANNEL`. Dei styrer berre telemetri-attribusjon og blir sette av pluginane.

```bash
export TRIPO_ANALYTICS_ENABLED=0 TRIPO_NO_UPDATE_CHECK=1
# Gratis plan utan nettverk; same argument som den kontrollerte planen master_h31
tripo make to3d.png --dry-run --json --model tripo-v3.1 -p texture=false -p pbr=false -p geometry_quality=detailed -p auto_size=false -p enable_image_autofix=false -p export_uv=false --seed 12345
# Betalt, 40 kreditt; sender straks utan plan eller stadfesting
tripo generate image-to-model to3d.png --model tripo-v3.1 -p model_seed=12345 -p texture=false -p pbr=false -p geometry_quality=detailed -p export_uv=false --json -o reference-master
# Segmentering, 40 kreditt; Beta, så defaultverdiane er låste eksplisitt
tripo mesh segment MASTER_TASK_ID --model v2.0-20260430 -p segmentation_granularity=balanced -p split_by_connectivity=true --json
# Lukking utan AI, 30 kreditt; delnamna kjem frå nodane i segment-GLB-en
tripo mesh complete SEGMENT_TASK_ID --completion-mode quick_cap -p 'part_names=["DEL_A","DEL_B"]' --json
# Basic decimation, 10 kreditt; face_limit er påkravd
tripo mesh decimate MASTER_TASK_ID --model v1.0 --face-limit 50000 --json -o reference-basic-decimate
# Retopologi v3, 35 kreditt; --no-bake verkar ikkje på ein master utan tekstur, men skadar ikkje
tripo mesh decimate MASTER_TASK_ID --model v3.0 --face-limit 10000 --no-bake --json -o reference-retopo
# Etter tidsavbrot: vent vidare på same task
tripo task watch TASK_ID --download
```

- **Vel éi grein.** Ikkje køyr alle døma automatisk, og hopp over completion og lågpoly når dei ikkje trengst.
- **Berre `make` har `--dry-run`.** Berre `make` og `tripo ai` viser plan-kort og ber om stadfesting. `generate` og alle `model`-, `anim`- og `mesh`-kommandoar sender ein betalt jobb med ein gong. Utan TTY slår `make` på `--yes` av seg sjølv, og ein mesh-kommando utan input brukar `@last`. Krev derfor ein eksplisitt task-ID og ei godkjend kostnadsgrense før kvar linje utan `--dry-run` *(metodeval)*.
- **Utdatamappe.** `-o reference-master` legg filene i `reference-master/tripo-out/<namn>-<id8>/`. Sjekk den næraste `.tripo/context.json` oppover frå arbeidsmappa (`output_dir`) og `TRIPO_HOME`, som har default `~/.tripo`.
- **Modellval i generate.** Med `--model` vel `generate` ikkje P1. Utan `--model` vel `generate` P1 når `face_limit` er 20 000 eller lågare. Låg-poly-ord i prompten blir berre lesne av `make` og `ai`. I make-linja er `auto_size=false` og `enable_image_autofix=false` defaultverdiar og står berre der for å vise intensjonen.
- **`--for print`** set v3.1, `texture=false` og `pbr=false`, og legg til ein convert til STL med `flatten_bottom`. Convert-steget er Advanced og kostar 10, så eitt bilete kostar 30 til saman. «Watertight» er berre ein merkelapp, for presetet har inga reparasjon. Det lovar òg «3MF (colored)», medan API-et seier at 3MF er einfarga. Ikkje bruk presetet på masteren. `--then` erstattar presetkjeda.
- **Kontroller parametrane sjølv.** CLI 0.7.2 gir `valid=true` utan åtvaring for `generate_parts=true` saman med `smart_low_poly=true`, så kontroller interaksjonane mot API-sida også etter ein vellukka dry-run. Request-builderen set identitetsmatrisa for Smart Segment `model` når `transform` manglar. Kontroller ramma.
- **Tidsavbrot.** Køyr `tripo task watch <task-id> --download`, aldri `make` eller `redo` på nytt. Exit-kode 6 kan bety både at jobben feila (refundert) og at ventetida gjekk ut medan jobben framleis køyrer, så les feilteksten. Ikkje set eigen timeout under 15 minutt; CLI-defaulten er 1800 s.

Kjelder: [CLI](https://developers.tripo3d.ai/en/docs/cli) og `tripo-cli@0.7.2` `README.md`, `skill/SKILL.md`, `skill/commands/{make,generate,process,task,account}.md`, `skill/common-errors.md`, `skill/examples/print.md`, `dist/knowledge/scenarios.js` og `dist/core/download.js`. Npm-pakka er verifisert i kjeldeoversikta.

## Konvertering og CAD

API v3 ligg på `https://openapi.tripo3d.ai/v3`, medan Kina-kontoar brukar `openapi.tripo3d.com`. Ein task må spørjast med same nøkkel og region som oppretta han, elles svarar API-et «not found» eller `missed`.

- **Input.** `/v3/files` tek bilete i JPEG og PNG (20 MB) og modellar i GLB, GLTF, FBX, OBJ og STL (150 MB, presign tilrådd over 60 MB). Presign tek i tillegg 3MF og USDZ, men desse er ikkje gyldig input til convert, import, segment eller decimate. `/v3/files` listar GLTF, men CLI-dokumentet seier at `.gltf` ikkje kan lastast opp fordi fila viser til eksterne filer *(kjeldekonflikt)*. Bruk GLB.
- **Ta vare på GLB.** GLB kjem frå generering, segmentering og retopologi. Convert kan ikkje lage GLB, berre GLTF, USDZ, FBX, OBJ, STL og 3MF. Ta derfor vare på dei originale GLB-filene. Hald original eining, scene- og nodetransformasjon, rotasjon, pivot og skalafaktor sporbare.
- **Eining.** Ingen endepunkt har ein einingsparameter. `scale_factor` (default 1) har ikkje eining, og alle andre verdiar gir Advanced-pris. Skaler til mm lokalt i CAD.
- **Convert kan endre forma.** `quad` tvingar FBX og 10 000 flater når `face_limit` manglar. CLI-dokumentet seier i staden at quad ikkje kan eksporterast til GLTF *(kjeldekonflikt)*. `force_symmetry` verkar berre med quad. `face_limit`, `flatten_bottom`, `pivot_to_center_bottom` og `scale_factor` endrar modellen og gir Advanced-pris (10 mot 5). CLI-en reknar òg ikkje-default `export_orientation`, `bake`, `pack_uv`, `fbx_preset` og `part_names` som Advanced, så kontroller `credits_consumed`. Reint formatbyte er billegast (5).
- **`fbx_preset=bake_scale`** bakar nodeskalaen inn i geometrien i API-et, men CLI 0.7.2 avviser verdien. `bake` gjeld materialeffektar.
- **Print-format.** STL mistar teksturane, og 3MF er einfarga eller berre geometri. `export_vertex_colors` gjeld berre OBJ og GLTF.
- **Éitt convert-kall.** Ifølgje v2 kan ein konvertering etter den første berre ta `format`. Set derfor alle vala, også den endelege `export_orientation`, i same kall.
- **Delar.** `part_names` på convert kan eksportere enkeltdelar («Names of parts to export, from mesh/segment data»). API-sida dokumenterer `task_id` berre for generation-taskar, medan CLI-dokumentet seier at segmenterte og lukka delar kan eksporterast med `convert -p 'part_names=[...]'` *(kjeldekonflikt)*. Valider dette før kjeda byggjer på det.
- **Print i dette repoet.** Bruk ikkje Tripo-convert til printfiler. Lag STL og 3MF lokalt etter CadQuery/manifold3d, og bruk convert berre når ein ekstern mottakar treng FBX eller USDZ *(metodeval)*.

Kontroller dimensjonar og aksar etter import. Konvertering til STL eller 3MF gir ikkje parametrisk STEP/BRep.

Kjelder: [introduksjon](https://developers.tripo3d.ai/en/docs/introduction), [filer](https://developers.tripo3d.ai/en/docs/files), [presign](https://developers.tripo3d.ai/en/docs/files-presign), [konvertering](https://developers.tripo3d.ai/en/docs/models-convert), [import](https://developers.tripo3d.ai/en/docs/models-import), [prisar](https://developers.tripo3d.ai/en/pricing), [v2 konvertering](https://docs.tripo3d.ai/export/conversion.html), [v2 task-resultat](https://docs.tripo3d.ai/task-query/get-your-task-result.html), `tripo-cli@0.7.2` `skill/commands/{process,task,account}.md`, `dist/knowledge/{models,params}.js`. Sjå `tripo-og-cad.md` for mekanisk arbeid og kontroll.

## Køyring, kostnad og kjeldekonfliktar

**Krav til klienten** *(metodeval, bygd på dokumentasjonen)*. Kontroller klienten mot desse punkta før ei betalt køyring:

1. Rekn `success`, `failed`, `cancelled`, `banned` og `expired` som terminale. v2 har i tillegg `unknown`. Introsida og task-query listar berre fem statusar, og ei løkke som berre ser etter tre av dei, heng.
2. Bruk ein timeout på minst 1800 s. Ved tidsavbrot ventar du vidare på same task-ID og sender ikkje på nytt.
3. Spør tasken på nytt rett før nedlasting.
4. Set filending etter URL eller Content-Type, og hent alle URL-felt: `model_url`, `rendered_image_url`, `seg_model_url`, `mask_url`, `uv_render_url`, `generated_image_url` og `*_view_url`.
5. Bruk `Retry-After` og `X-RateLimit-Reset`, og la backoff ha eit tak på 32 s.
6. Avgrens parallelliteten per pool.
7. Skriv ein `task.json` per jobb med endepunkt, body utan nøkkel, wire-modell, seed, task-ID, `credits_consumed` som desimaltal og SHA-256 for kvar fil.
8. Valider lokalt før kostnad: eksplisitt modell, P1 utan quad, rett `face_limit`-område, `generate_parts`-reglane, `smart_uv` berre på v3.0 og maks 80 000 trekantar inn til `/mesh/uv`.

**Praksis:** A1 køyrde CLI-en via Codex, og Entropi køyrde repoet sin eigen v3-klient. `verktoy/tripo.py` og `verktoy/kjor.py` følgjer punkta 1–7 og validerer punkt 8 lokalt (utan `/mesh/uv`-grensa) sidan 20.10.2026; `python3 verktoy/tripo.py valider jobbar.json` sjekkar ei jobbliste utan kostnad.

**Innsending.** Lagre task-ID-en straks. CLI-en prøver oppretting på nytt berre ved 429, og spørjingar inntil tre gonger ved nettverksfeil eller 5xx. Feilsida rår til å prøve 500 på nytt, men CLI-dokumentet seier at oppretting ikkje skal sendast på nytt, og ingen idempotensnøkkel er dokumentert *(kjeldekonflikt)*. Send derfor aldri POST på nytt automatisk *(metodeval)*. Er utfallet av ein POST uvisst, sjekk `frozen` i `GET /v3/account/balance`, usage og konsollen før ei eventuell ny innsending. **Praksis:** i Entropi krasja to nedlastingar (a og d) på proxyavbrot, og filene vart henta frå same task. I A1 fekk retopologien eit nettverksavbrot, og same task vart henta inn att. Ingen av gongene trongst ny generering.

**Grenser for parallellitet.** Rate limit gjeld per API-nøkkel (1007), medan samtidigheit gjeld per konto og kategori (2000), så fleire nøklar gir ikkje meir parallellitet. Grensene er 10 for H, 5 for P, 1 for biletgenerering, 5 for Model Processing (texture, convert, refine) og 10 for Mesh Operations (segment, completion, retopologi). Smart Segment og Smart UV står ikkje i nokon kategori.

**Resultat.** Last ned med ein gong. Er berre URL-en utgått, spør tasken på nytt med `GET /v3/tasks/{id}` eller `tripo task get <id> --download`. Har tasken status `expired`, er filene borte, og berre ny generering hjelper. Batch-query tek inntil 100 ID-ar og legg slike taskar i `missed`. Kjeldene gir ulik levetid for lenkjer: 60 s (v2-FAQ), om lag 5 minutt (v2 task-query og CLI) og ingen oppgitt levetid i v3. Kor lenge Tripo lagrar input og resultat, er *(udokumentert)*: FAQ-en har plasshaldaren «XXX». Arkiver rå resultat lokalt med SHA-256 med ein gong. Webhooks (`task.completed`, `task.failed`, `balance.low`) kan erstatte polling. Dei krev eit HTTPS-endepunkt. Tripo tilrår signaturkontroll, 2xx-svar innan om lag 5 s og deduplisering på `Tripo-Webhook-Delivery`.

**Kostnad.** Sjekk saldo og pris per valt steg før betaling. Kreditt blir frosen ved oppretting og trekt når jobben lukkast. Feila og avbrotne taskar blir ikkje fakturerte. `credits_consumed` er eit desimaltal, så ikkje bruk heiltalsparsing. HTTP 403 kan vere kode 2010 (for lite kreditt) og skal ikkje prøvast på nytt. Webappen og API-et har kvar sine kredittar, og kreditt går ikkje ut på dato. Rapporter kvart fakturert steg og totalsummen. Bruk ikkje eksempelresultat med 100 kreditt som prisliste, men tabellen nedanfor. Under denne dokumentasjonskontrollen vart ingen Tripo-jobbar oppretta.

**Kjeldekonfliktar og versjonsetterslep**

- Den dedikerte presign-sida brukar `POST /files/presign`, medan changelog nemner `POST /v3/files/upload-credentials`.
- SDK-sida låser fem SDK-ar. JS, Go, Rust og Java er V3 og låste til commit. Berre Python er låst til 0.4.2, som i hovudsak er V2 med avgrensa V3 (segment, task og files). Bruk ikkje Python-SDK-en for v3 *(metodeval)*. ComfyUI 2.0.0 krev `tripo3d>=1.0.0,<2.0.0` (V3), men 1.x er ikkje dokumentert på SDK-sida. Ingen lokal kjelde oppgir nokon sluttdato for V2, og v2 og v3 kan køyre parallelt.
- Pluginsida viser ComfyUI 1.1.21 (V2), medan nodesida viser 2.0.0 (V3).
- Refine og Stylize er ikkje lenger støtta i ComfyUI 2.0.0: nodane er utfasa, skjulte og stoppar utan kall. CLI 0.7.2 har framleis `refine`, og Java-SDK-en når `/v3/models/refine` og `/stylize`. Changelog og migreringsguiden listar endepunkta, men ingen eigen v3-API-side finst. Funksjonane er irrelevante for denne kjeda.
- CLI 0.7.2 avviser lokalt både texture v3.5 og `bake_scale`. Han heng òg etter API-et på andre punkt: rig-check er «GLB only», og rig-defaulten er v2.5 der serveren har v1.0.
- Telemetri er på som default i CLI-en mot det internasjonale API-et. Dry-run sender ingenting, og `TRIPO_ANALYTICS_ENABLED=0` slår telemetrien av.
- GPT-6/Astra-cookbooken brukar `tripo auth login`, `tripo auth whoami` og `tripo account balance`, men CLI-sida har `tripo login`, `tripo whoami` og `tripo balance`.
- `tripo-dokumentasjon.json` dekkjer berre developers.tripo3d.ai og CLI-pakken. v2-dokumentasjonen, PDF-ane og showcase-sidene er brukte her, men er ikkje hasha der.

Bruk det dedikerte endepunktet, den aktuelle klientversjonen og faktisk validering i staden for å slå saman motstridande tabellar.

Kjelder: [task-livsløp](https://developers.tripo3d.ai/en/docs/task-lifecycle), [query](https://developers.tripo3d.ai/en/docs/task-query), [batch-query](https://developers.tripo3d.ai/en/docs/task-batch-query), [webhooks](https://developers.tripo3d.ai/en/docs/webhooks), [feil](https://developers.tripo3d.ai/en/docs/error-handling), [rate limits](https://developers.tripo3d.ai/en/docs/rate-limits), [billing](https://developers.tripo3d.ai/en/docs/billing), [konto](https://developers.tripo3d.ai/en/docs/account), [prisar](https://developers.tripo3d.ai/en/pricing), [SDK](https://developers.tripo3d.ai/en/docs/sdk), [pluginar](https://developers.tripo3d.ai/en/docs/plugins), [ComfyUI-nodar](https://developers.tripo3d.ai/en/docs/comfyui-nodes), [migrering](https://developers.tripo3d.ai/en/docs/migration-v2-to-v3), [CLI](https://developers.tripo3d.ai/en/docs/cli), [v2 task-resultat](https://docs.tripo3d.ai/task-query/get-your-task-result.html), [v2 FAQ](https://docs.tripo3d.ai/other/support-faq.html), `tripo-cli@0.7.2` `README.md`, `skill/common-errors.md` og `skill/commands/task.md`. Praksis: `A4/arkiv/tripo-a1/LES-MEG.txt` og `A4/arkiv/entropi-tripo/images/d_fusion_refs.json`.

## Kostnad og grenser per steg

1 kreditt = 0,01 USD. Prisane gjeld per 20.10.2026. Kontroller [prissida](https://developers.tripo3d.ai/en/pricing) før betaling.

| Steg | Endepunkt | Kreditt (dokumentert) | Grenser | Pool | Praksis |
| --- | --- | --- | --- | --- | --- |
| Opplasting | `POST /v3/files`, `/v3/files/presign` | 0 | Bilete JPEG/PNG ≤ 20 MB; modell ≤ 150 MB; presign over 60 MB, URL gyldig 30 min | – | – |
| Konseptbilete | `image-to-image`, `text-to-image` | seedream 5; banana_pro 15 (4K: 20); chat_image 2/2.5: 10 (4K: 15), `high` 20–40 | Input ≤ 20 MB og ≤ 36 MP, sideforhold 1/3–3; 4/10/16 ref.; ingen seed | Bilete 1 | Entropi: banana_pro 15, 2.5_flare `medium` 10 |
| Multiview-bilete | `image-to-multiview`, `edit-multiview` | 10; 5 per redigert bilete | Berre `file_token`/URL inn | Bilete 1 | – |
| Master | H3.1 image-/multiview-to-model | 20 geometri, 30 tekstur (HD 40, 8K 50); Ultra +20, parts +20, smart low poly +10, quad +5 | `face_limit` ≤ 1,5 M (Ultra 2 M), quad ≤ 150 000; input ≥ 256 px | H 10 | A1: Ultra utan tekstur 40. Entropi: Ultra + HD-tekstur 60, ca. 3 min |
| Lågpoly-generering | P1 / P2 Preview | P2: 100 (tekstur 110/120/130); P1: 40 i v2-prislista | P1 50–20 000; P2 48–50 000 tri / 48–25 000 quad | P 5 | – |
| Segmentering | `/mesh/segment` | 40 | ≤ 150 MB; `task_id` berre frå generering | Mesh 10 | – |
| Smart Segment | `/mesh/smartsegment` | image 85, model 55 | `file_token`/URL; model krev GLB og `transform` | ikkje lista | A1: `model`/`fine`, 11 delar, 55 |
| Completion | `/mesh/complete` | `ai_completion` 50, `quick_cap` 30 | Berre `mesh/segment`-task | Mesh 10 | A1: `quick_cap` 30 |
| Retopologi | `/mesh/decimate` | v1.0 10, v2.0 30, v3.0 35 tri / 40 quad | v1: ≤ 2 M, `face_limit` påkravd; v2/v3: 500–20 000 tri, 500–10 000 quad | Mesh 10 | A1: v3.0, 20 000 flater, 35 |
| Smart UV | `/mesh/uv` | 20 | ≤ 80 000 ekv. trekantar, elles feil (refundert) | ikkje lista | – |
| Konvertering | `/models/convert` | Basic 5, Advanced 10 | ≤ 150 MB; GLB er ikkje målformat | Processing 5 | – |
| Import | `/models/import` | Gratis i v2-prislista, ikkje lista i v3 | ≤ 150 MB | – | – |

**Døme med dokumenterte prisar:** Ultra-master 40 + segmentering 40 + `quick_cap` 30 + v3-retopologi 35 = 145 kreditt (1,45 USD). **Praksis A1:** 160 kreditt, fordi Smart Segment (55) erstatta segmentering (40). **Praksis Entropi:** 175 kreditt: kalibrering 15, fire banana_pro-variantar 60, éin chat_image-variant 10, hero 15, to3d 15 og 3D-master 60.

Kjelder: [prisar](https://developers.tripo3d.ai/en/pricing), [H3.1](https://developers.tripo3d.ai/en/models/v3-1), [P2](https://developers.tripo3d.ai/en/models/p2), [rate limits](https://developers.tripo3d.ai/en/docs/rate-limits), [filer](https://developers.tripo3d.ai/en/docs/files), [presign](https://developers.tripo3d.ai/en/docs/files-presign), [image-to-image](https://developers.tripo3d.ai/en/docs/generation-image-to-image), [segment](https://developers.tripo3d.ai/en/docs/mesh-segment), [Smart Segment](https://developers.tripo3d.ai/en/docs/mesh-smartsegment), [completion](https://developers.tripo3d.ai/en/docs/mesh-complete), [retopologi](https://developers.tripo3d.ai/en/docs/mesh-decimate), [Smart UV](https://developers.tripo3d.ai/en/docs/mesh-uv), [konvertering](https://developers.tripo3d.ai/en/docs/models-convert), [changelog](https://developers.tripo3d.ai/en/docs/changelog), [v2 prisar](https://docs.tripo3d.ai/get-started/pricing.html). Praksis: `A4/arkiv/tripo-a1/tripo-receipts.json` og `A4/arkiv/entropi-a3/README.md`.
