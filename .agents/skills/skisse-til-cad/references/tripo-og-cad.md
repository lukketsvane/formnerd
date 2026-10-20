# Tripo og mekanisk CAD

Les først `tripo-bruk.md` for det dokumentasjonskontrollerte valet av Tripo-kjede. Bruk denne sida til bevaring, mekanikk og eksport etter valet.

## Vel rett operasjon

| Behov | Operasjon | Krav til vidare bruk |
| --- | --- | --- |
| Skisse til første form | image-to-model eller konsistent multiview-to-model | Lagre vald original og geometritask før behandling |
| Dele vald form | ordinær segmentering av vald task/mesh | Bevar master, global skala og deltransformasjonar; kontroller resultat |
| Delingsvariant via Smart Segment | Smart Segment `model` med GLB og transform (55 kreditt) | Bevar som eiga grein. Om model-modus genererer geometrien på nytt eller berre importerer, er udokumentert; samanlikn med master |
| Ny modell med delar frå eit bilete | H3.0/H3.1 med `generate_parts=true`, `texture=false`, `pbr=false` (+20), eller Smart Segment `image` (85) | Rekn som ny geometri; samanlikn med vald form |
| Lett modell ved generering | `smart_low_poly` på H3.0/H3.1 (ikkje v2.5, P1 eller P2), eller P1/P2 | Lag separat variant og kontroller kompatibilitet |
| Færre polygon i eksisterande mesh | decimate | Bevar detaljert master og dokumenter avvik |
| Lukke hol etter segmentering | complete, til dømes `quick_cap` | Kontroller snitt, volum, veggar og passflater, og at delane framleis er separate (kjeldene er usamde om completion slår dei saman) |
| Eksakte mekaniske grensesnitt | deterministisk CAD/meshmodellering | Dimensjoner mot mål framfor generert utsjånad |

Les gjeldande Tripo-skill og dry-run før køyring. I grunnlaget kontrollert 20. oktober 2026 undertrykkjer `smart_low_poly=true` automatisk `generate_parts`; v3.x-parts krev `texture=false` og `pbr=false`. P-serien og H/v3-serien har ulik funksjonsstøtte. I CLI-en kan eit `face_limit` på 20 000 eller lågare velje P1 når `--model` manglar; API-et byter aldri til P-serien av seg sjølv. Set eksplisitt modell når bestemte funksjonar er nødvendige, og kontroller faktisk payload. Ikkje frys modellnamn, prisar eller flagg frå dette dømet som framtidig API-sanning.

Smart Segment model tek eksisterande GLB som fil/URL; ordinær segmentering kan referere til ein generation-task (text-, image- eller multiview_to_model); resultat frå import, decimate eller convert og eigne STL-ar går som `file_token`/URL (≤ 150 MB). Smart Segment image genererer modellen på nytt. Løys `@last` til konkret task-ID før ei viktig grein. Hald ulike delings- og polygonvariantar separate.

## Bevar opphav og form

Lagre råresultat før reparasjon. Registrer kjeldefil, SHA-256, task-/foreldre-ID, faktisk modellversjon, prompt, seed, parameter, kostnad og varig fil. Seed finst berre for generering; segment, Smart Segment, completion og decimate har ingen seed, så lagra output og låst modellversjon er det som sikrar sporbarheit. Hald API-nøklar og mellombelse nedlastingsadresser ute av repoet.

Bruk same globale transformasjon for alle delar. Dokumenter einingar, rotasjon og skalafaktor. Ikkje sentrer eller skaler kvar del uavhengig. Opprett stabile del-ID-ar før BOM, printlayout og manual.

Samanlikn master og bearbeidd modell frå front, side, bak og 3/4. Kontroller silhuett, negativt rom, ribber, overflater som signaliserer funksjon, knappeplassering og linse-/portopningar. Mål avvik der dei er avgjerande. Oppgi tilnærminga dersom ei lett utgåve taper detaljar.

Hald `enable_image_autofix=false` når automatisk endring ikkje er tilsikta. Ikkje legg inn symmetri, flat botn, AI-completion eller ny generering som skjult reparasjon. Bevar originalen, og vurder endringa mot det brukaren har bedt om.

## Modellér funksjon

Definer maskinvarevolum frå mål/datablad, inkludert kontaktar, plugginnføring, kabelbøy og verktøytilgang. Registrer føresetnader når maskinvara manglar. Vel feste som kan produserast, monterast og brukast i materialet. Ikkje overfør kameramål eller PLA-passningar ukritisk til andre produkt.

Bevar vald native yttermesh. Bruk robuste boolske operasjonar for innvendige hulrom/opningar og parametriske solids for haldarar, låsar, kassettar og feste. Før mekaniske endringar inn i modellen før instruksjonsfiguren.

Kontroller samanhengande delar, orientering, positivt volum, lukka topologi og lause fragment. Ved fragmentfjerning: definer og rapporter volumgrense, mengd og samla fjerna volum. Ein vellukka boolsk operasjon eller manifold-rapport stadfestar ikkje veggtjukkleik og funksjon.

Kontroller relevante delpar, låseflate, knappevandring og monterings-/uttaksveg. Skil diskret prøvde posisjonar frå kontinuerleg rørslekontroll. Merk kva som faktisk er testa.

## Eksporter etter faktisk innhald

| Leveranse | Innhald |
| --- | --- |
| Native CAD og parameter | Redigerbar mekanikk og konstruksjonsgrunnlag |
| STEP | Delar som faktisk er BRep-solids |
| GLB / montert 3MF | Visingsmodell med stabile deltransformasjonar |
| Individuell STL/3MF | Eintydig printdel per fil i rett skala |
| Printplater | Plasserte delar med kontrollert tal og orientering |
| Verifikasjon og BOM | Del-ID, namn, mengd, materiale, målgrunnlag og status |

Opplys dersom STEP berre dekkjer analytisk mekanikk og ikkje detaljert yttermesh. Filendinga stadfestar ikkje fullstendig native CAD.

## Print og fysisk kontroll

Lag lita prøve for kritiske passningar/låsar først. Definer observerbart krav, til dømes innføring, bestemt rotasjon, aksialt hald og opning utan skade. Prøv knappar, fleksfeste og klips der dei avgjer funksjon.

Vel faktisk maskin/dyse/plate/filament i sliceren, og kontroller alle objekt i verktøybanene. Lagre prosjekt og maskintilpassa slicing. Bruk generiske testresultat som generiske testresultat; lag ny P1S-slicing før P1S-utskrift.

Loggfør digital, slicer- og fysisk kontroll kvar for seg. Frigje resten av utskrifta etter relevant prøvedel, og sluttmontering etter faktisk prøvepass.
