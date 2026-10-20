# Tripo bruk frå skisse til CAD

Metodegrunnlag kontrollert 20. oktober 2026 mot heile den engelske API-dokumentasjonen, modell-/prissider og publiserte CLI-dokument. Sjå `tripo-dokumentasjon.json` for dekning og versjonar. Oppskrifta er ei ingeniørfagleg tilråding basert på dokumenterte funksjonar; ho er ikkje ei påstand om at Tripo produserer målsett CAD.

## Vel kjede etter kva som alt er godkjent

| Utgangspunkt | Føretrekt kjede | Kvifor |
| --- | --- | --- |
| Éi vald skisse | H3.1 image-to-model → vurder master → ordinær segmentering ved behov | Bevar detaljert formgrunnlag før nedbygging |
| Fleire konsistente faktiske visingar | H3.1 multiview-to-model → vurder master | Meir oppgitt formgrunnlag utan å dikte nye visingar |
| Ny generering der delar er ønskt frå starten | H3.1 med generate_parts, utan tekstur/PBR/Smart Low Poly | Eiga delingsgrein, ikkje kombinasjon med lågpoly |
| Godkjend eksisterande mesh | Hent eksisterande task/GLB → ordinær segmentering | Unngå å generere forma på nytt |
| Behov for lettare CAD-referanse | Avlei basic decimation eller v3-retopologi frå master | Bevar høgdetaljert original og kontroller avvik |
| Enkel form med lågpoly som sjølve målet | H Smart Low Poly eller eksplisitt P1/P2 | Annan topologi-/fidelitetsprioritet enn detaljert master |
| Behov for auto-modellert deling | Smart Segment i eiga grein | Vurder ny/geometrisk endra utgåve mot originalen |

Kjelder: [H image](https://developers.tripo3d.ai/en/docs/generation-image-to-model/standard), [H multiview](https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/standard), [modellar](https://developers.tripo3d.ai/en/docs/models-and-versions), [segmentering](https://developers.tripo3d.ai/en/docs/mesh-segment), [retopologi](https://developers.tripo3d.ai/en/docs/mesh-decimate).

## Referansebilete og master

Bruk tydeleg motiv, lite okklusjon og rein bakgrunn. Single-image støttar PNG/JPEG/WebP, inntil 20 MB; minst 256 × 256 er tilrådd. Image-to-model har ikkje dokumentert promptfelt for å leggje til mekanikk. Gjer nødvendige formval før generering, og teikn presis mekanikk etterpå.

Ved multiview krevst front og minst éi anna vising av same objekt. Bruk anten view-key-array, fire posisjonar i rekkjefølgja front/left/back/right med tom streng for ei manglande vising, eller éin tidlegare multiview-task i ei eiga task-array. Ikkje bland formata. Image-to-multiview og Edit Multiview kan hjelpe formutprøving, men nye AI-visingar er ikkje målte sider av produktet. Godkjenn kvar vising før 3D-generering.

For detaljert master er den kontrollerte modellen `v3.1-20260211` (CLI-alias `tripo-v3.1`). `geometry_quality=detailed` er Ultra-geometri; detaljert tekstur er eit anna val og tilfører ikkje fysisk geometri. Til print/CAD: set både `texture=false` og `pbr=false`, sidan PBR elles kan tvinge tekstur på. Vurder `export_uv=false` når UV ikkje trengst. Hald `auto_size=false` og målsett modellen sjølv; Tripo si automatiske meterskalering har ingen oppgitt dimensjonstoleranse. Bevar seed og eksakte inputfiler.

Hald `enable_image_autofix=false` når nytolking ikkje er tilsikta. `orientation=align_image` verkar berre på teksturert generering. La `export_orientation` vere uendra under etterbehandling og set endeleg orientering i siste konvertering. Verifiser transformasjonar ved innlesing i CAD.

Kjelder: [H image](https://developers.tripo3d.ai/en/docs/generation-image-to-model/standard), [H multiview](https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/standard), [multiview-bilete](https://developers.tripo3d.ai/en/docs/generation-image-to-multiview), [rediger visingar](https://developers.tripo3d.ai/en/docs/generation-edit-multiview).

## Deler og lågpoly er ulike val

H `generate_parts=true` krev eksplisitt `texture=false` og `pbr=false`. Quad blir ignorert; Smart Low Poly vinn og undertrykkjer parts. Bevar masteren frå den valde genereringa, ikkje lov både parts og Smart Low Poly i same kall.

Ordinær segmentering deler eksisterande mesh. Default `v1.0-20250506` er geometrisk; `v2.0-20260430` er semantisk Beta med simple/balanced/detailed og connectivity-val. `ref_image` i v2 overstyrer både granularity og connectivity. Bruk ei slik maske berre når tilsikta delgrenser faktisk er viste. Kontroller grensene og ikkje stol på semantiske etikettar som mekaniske skøytar.

Smart Segment tek filtoken/URL, ikkje ein vilkårleg master-task-ID. Image-modus lagar ny geometri; model-modus krev GLB og ein dokumentert kolonnemajor 4 × 4-transformasjon med 16 tal. Sida skildrar auto-modellering og lovar ikkje eksakt formbevaring. Ta vare på ytre og returnerte del-/modell-task-ID-ar, og vurder ei separat avleiing.

Completion krev segment-task. Standard `ai_completion` genererer manglande geometri; `quick_cap` lukkar opne grenser utan slik AI-generering. Oppgi faktiske `part_names` for målretta handling; utelating rører alle delane. Ein cap kan også lukke eit tilsikta hol. Kontroller resultatet før CAD.

H Smart Low Poly passar enkle motiv, med 500-20 000 trekantar eller 500-10 000 quads. P1 er eiga lågpoly-generering utan quads; P2 Preview har native quads, men støttar ikkje H-val som generate_parts, smart_low_poly eller geometry_quality. Ikkje byt master til P-serien berre fordi CLI automatisk vel P1 ved lågt face-budsjett.

Avklar kva «Smart Low Poly» betyr i det aktuelle verktøyet. ComfyUI sin Smart Low Poly-node er etterfølgjande retopologi via `/mesh/decimate`, medan H `smart_low_poly` er eit genereringsflagg. Segmentering → retopologi av eksisterande delar er ei gyldig kjede; det som ikkje skal lovast, er både H generate_parts og H smart_low_poly i same genereringskall.

For eksisterande master: basic decimation `v1.0` har høgare face-grense, medan retopologi v2/v3 byggjer lettare topologi innan dei låge face-grensene. Default er framleis v2; vel v3 eksplisitt når ønskt. V2/v3 kan målrette segmenterte part_names. V3 smart_uv er eit val for UV, ikkje eit CAD-krav. Ingen reduksjon gir oppgitt mekanisk toleranse. Samanlikn silhuett, hol, ribber og måleavvik før godkjenning.

Kjelder: [H-generering](https://developers.tripo3d.ai/en/docs/generation-text-to-model/standard), [P-generering](https://developers.tripo3d.ai/en/docs/generation-image-to-model/p), [segment](https://developers.tripo3d.ai/en/docs/mesh-segment), [Smart Segment](https://developers.tripo3d.ai/en/docs/mesh-smartsegment), [completion](https://developers.tripo3d.ai/en/docs/mesh-complete), [retopologi](https://developers.tripo3d.ai/en/docs/mesh-decimate).

UI-namngjeving: [ComfyUI-nodar](https://developers.tripo3d.ai/en/docs/comfyui-nodes).

## Konkrete CLI-oppskrifter

Syntaksen nedanfor er dokumentasjonskontrollert mot CLI 0.7.2. Fem CLI-planar og sju request-builder-kontrollar er også køyrde utan nettverk eller innlogging; sjå `tripo-cli-verification.json`. Ingen betalte jobbar eller faktiske modellresultat vart testa. Byt filnamn, konkrete task-ID-ar og faktiske deletikettar. Last gjeldande klientdokument ved versjonsbyte. Bruk etablert klient/innlogging. Ikkje les eller skriv ut nøklar, og ikkje installer ein ekstra server for denne kjeda.

```bash
export TRIPO_CLIENT_APP=codex TRIPO_DISTRIBUTION_CHANNEL=codex_plugin
tripo make sketch.png --model tripo-v3.1 -p geometry_quality=detailed -p texture=false -p pbr=false -p auto_size=false -p enable_image_autofix=false -p export_uv=false --dry-run --json
tripo generate image-to-model sketch.png --model tripo-v3.1 -p geometry_quality=detailed -p texture=false -p pbr=false -p auto_size=false -p enable_image_autofix=false -p export_uv=false --json -o reference-master
tripo mesh segment MASTER_TASK_ID --model v2.0-20260430 -p segmentation_granularity=balanced -p split_by_connectivity=true --json
tripo mesh complete SEGMENT_TASK_ID --completion-mode quick_cap -p 'part_names=["housing","cover"]' --json
tripo mesh decimate MASTER_TASK_ID --model v1.0 --face-limit 50000 --json -o reference-basic-decimate
tripo mesh decimate MASTER_TASK_ID --model v3.0 --face-limit 10000 --no-bake --json -o reference-retopo
```

Vel éi nødvendig grein; ikkje køyr alle eksempel automatisk. Hopp over completion og lågpoly når dei ikkje trengst. Make-dry-run skal vise rett payload utan uønskt kjede; generate køyrer eksplisitt eitt endepunkt. Dry-run er dokumentert for make, ikkje som vilkårleg flagg på alle prosesskommandoar. `--for print` legg inn STL-konvertering og flatten_bottom; bruk ikkje det som skjult endring av godkjend produktform. CLI `--then` erstattar presetkjeda, og lokale kontekstval må sjekkast.

Kontrollen viste at CLI 0.7.2 returnerer `valid=true` utan åtvaring sjølv når både `generate_parts=true` og `smart_low_poly=true` står i payloadet. Kontroller derfor parameterinteraksjonane mot API-dokumentasjonen også etter ein vellukka dry-run. Lågpoly/parts-regelen er ein dokumentert serverregel; han vart ikkje prøvd som betalt jobb. Request-builderen set dessutan identitetsmatrise automatisk for Smart Segment model utan transform; kontroller om dette svarar til den faktiske koordinatramma.

Kjelder: [CLI](https://developers.tripo3d.ai/en/docs/cli) og `tripo-cli@0.7.2` sine `skill/commands/{make,generate,process}.md` og `skill/examples/print.md`, med verifisert npm-pakke i kjeldeoversikta.

## Konvertering og CAD

API v3 er `https://openapi.tripo3d.ai/v3`. Bruk dokumenterte inputformat for kvart endepunkt; filupload og etterbehandling har ulike formatlister. Føretrekk sjølvstendig GLB mellom verktøy. Hald original eining, scene-/node-transformasjon, rotasjon, pivot og skalafaktor sporbare. Bruk `scale_factor=1` til ei faktisk kalibrering er definert.

Konvertering kan endre form: quad kan tvinge FBX og redusere til 10 000 faces når grensa er utelaten; symmetry, face_limit, flatten_bottom og pivot er aktive val. `fbx_preset=bake_scale` bakar nodeskala, medan `bake` gjeld materialeffektar. La formendrande val vere av når berre formatbyte trengst. Kontroller dimensjonar og aksar etter import. Konvertering til STL/3MF er ikkje konvertering til parametrisk STEP/BRep.

Kjelder: [introduksjon](https://developers.tripo3d.ai/en/docs/introduction), [konvertering](https://developers.tripo3d.ai/en/docs/models-convert), [import](https://developers.tripo3d.ai/en/docs/models-import). Sjå `tripo-og-cad.md` for mekanisk arbeid og kontroll.

## Køyring, kostnad og kjeldekonfliktar

Lagre task-ID ved innsending. Ved venteavbrot: følg eksisterande task. Ved uviss POST/nettverksfeil: sjekk task/console og frosne kredittar før eventuell ny innsending; ingen generell idempotenskontrakt er dokumentert. Hent mellombelse resultat straks. Ei utgått nedlastingslenkje er grunn til å spørje eksisterande task på nytt, ikkje til ny generering. Ikkje lov fast femminuttslevetid for alle resultat.

Kontroller gjeldande saldo og pris per valt steg før betaling. Kredittar blir reserverte ved oppretting og belasta ved vellukka jobb; faktisk kostnad er eit desimaltal frå task/usage. Rapporter kvart fakturert steg og totalsum. Ikkje bruk eksempelresultat med 100 kredittar som prisliste. Under denne dokumentasjonskontrollen vart ingen Tripo-jobbar oppretta.

Før vidare desse dokumenterte skilja: dedikert presign-side brukar `/files/presign` der changelog nemner anna namn; SDK-sida er eit låst Python 0.4.2-døme medan offisielt SDK-master dokumenterer 1.0.0/API v3 og V2-slutt 31. oktober 2026; generisk pluginside og dedikert ComfyUI-side viser ulike versjonar. Gamle Refine/Stylize-tabellar er ikkje prov på gjeldande klientstøtte. API-støtte for texture v3.5/fast/bake_scale er ikkje prov på at ein eldre installert CLI aksepterer det. Bruk dedikert endepunkt, aktuell klientversjon og faktisk validering framfor å slå saman motstridande tabellar.

Kjelder: [task-livsløp](https://developers.tripo3d.ai/en/docs/task-lifecycle), [query](https://developers.tripo3d.ai/en/docs/task-query), [feil](https://developers.tripo3d.ai/en/docs/error-handling), [billing](https://developers.tripo3d.ai/en/docs/billing), [prisar](https://developers.tripo3d.ai/en/pricing), [SDK](https://developers.tripo3d.ai/en/docs/sdk), [SDK README](https://github.com/VAST-AI-Research/tripo-python-sdk/blob/master/README.md), [SDK changelog](https://github.com/VAST-AI-Research/tripo-python-sdk/blob/master/CHANGELOG.md).
