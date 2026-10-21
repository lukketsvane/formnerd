---
name: skisse-til-cad
description: Gå frå skisse eller produktbilete via Tripo image-to-3D, segmentering eller Smart Low Poly, til mekanisk CAD, printfiler og IKEA-liknande monteringsrettleiing. Bruk ved skisse til CAD, sketch to CAD, Tripo til CAD, Smart Segment, vidareføring av vald 3D-form eller isometrisk assembly frå ein faktisk modell.
license: Apache-2.0
---

# Skisse til CAD og montering

Kjelde: [lukketsvane/formnerd](https://github.com/lukketsvane/formnerd). Stiar merka **Praksis** i referansane (t.d. `A4/arkiv/...`, `verktoy/tripo.py`) viser til det repoet.

Følg kjeda: skisse / referansebilete → Tripo image-to-3D → segmentering og eventuelt lettare mesh → mekanisk CAD → kontrollert printgrunnlag → IKEA-liknande assembly. Bevar den valde forma gjennom heile kjeda.

## Start frå rett grunnlag

1. Les oppgåvetekst, vald skisse, formanalysen og tilbakemeldingane. Registrer konsept, formgrep, funksjonar, materiale, produksjonsmåte og det som skal bevarast. Vurder silhuett, proporsjonar, negativt rom, overflater og funksjonsteikn før teknikken blir pakka inn. Bruk prosjektspesifikke krav; ikkje gjer Entropi eller kameramål til universelle standardar.
2. Finn siste kjelde, Tripo-taskar, CAD, kontrollrapportar og filplassering før nytt arbeid. Les repo-instruksar og sjekk andre sine endringar. Oppdag flytta mapper på nytt. Hald fram frå siste verifiserte steg.
3. Skil målte dimensjonar, databladmål og føresetnader. Set éin dokumentert hovudskala i mm. Spør berre etter eit manglande mål når det faktisk avgjer vidare konstruksjon; gjer anna uavhengig arbeid medan du ventar.
4. Prioriter rett Tripo-bruk. Les [Tripo-oppskrifta](references/tripo-bruk.md), [Tripo og CAD](references/tripo-og-cad.md) og den kontrollerte [kjeldeoversikta](references/tripo-dokumentasjon.json). Sjekk gjeldande offisielle API-/CLI-sider for operasjonane og faktisk klientversjon før køyring; bruk ein installert Tripo-skill når han finst. Skill API-støtte frå klientstøtte. Last imagegen-skill ved biletskaping og PDF-skill ved manualarbeid. Les [assembly-standarden](references/ikea-assembly.md) før illustrasjon/layout og [A1-dømet](references/a1-dome.md) for kjelder og stil.

## 1. Klargjer biletet

Bruk éi eintydig vald skisse eller eitt produkt per bilete, kvit bakgrunn og lesbar silhuett. Bruk imagegen til formutprøving, konsistente referansevisingar eller layoututkast når det hjelper. Merk utkast. Bruk faktisk CAD til endelege tekniske rendringar og monteringsillustrasjonar.

Følg biletsteget i [Tripo-oppskrifta](references/tripo-bruk.md#biletsteget-før-3d): konseptvariantar med image-to-image éin om gongen (biletgenerering har samtidigheit 1), val, eit eige to3d-bilete (1:1, sentrert, kvit bakgrunn, nøytralt mjukt lys, matte flater, 3/4 litt ovanfrå), og godkjenning før 3D. Bevar originalreferansen og namngi den valde varianten. Bruk multiview berre når bileta viser same objekt og detaljar. Ikkje generer nye variantar når brukaren har valt og bedt om ferdigstilling.

## 2. Bygg og del Tripo-forma

Vel ein detaljert master før deling eller lågpoly. Dokumentasjonen kontrollert 20. oktober 2026 peikar på H3.1 image-/multiview-to-model som første kandidat for detaljert industriform, med eksplisitt modell, `texture=false`, `pbr=false` og eventuelt `geometry_quality=detailed` (Ultra). Dette er eit metodeval, ikkje ein garanti for målpresisjon. La lågpoly vere ei eiga avleiing. Bruk ikkje eit lågt face-budsjett eller eit uinspisert printpreset på masteren.

Før nye betalte oppgåver: følg gjeldande kostnadsreglar og autorisert omfang/budsjett. Bruk `make --dry-run` til planlegging når CLI-en er tilgjengeleg, og kontroller payload/kostnad. Ikkje finn på dry-run-flagg for kommandoar som ikkje støttar det. Å lagre denne arbeidsflyten autoriserer ingen nye betalte modelloppgåver.

Lagre original mesh, preview, task-/foreldre-ID, prompt, seed, parameter, skala og faktisk kostnad. Hent eksisterande resultat med task-ID framfor ny generering. Ved tidsavbrot: følg eksisterande task.

Del normalt ein godkjend eksisterande modell med ordinær `/mesh/segment`. Vurder eksplisitt v1 geometrisk eller v2 semantisk segmentering ut frå delgrensene; ingen av dei garanterer identisk geometri. Smart Segment er ein separat auto-modelleringsgrein: image-modus genererer ny modell; model-modus krev GLB og 16-talstransformasjon og lovar heller ikkje eksakt bevaring. Bevar masteren og samanlikn resultatet.

Ved ny H-generering med deler frå starten: send `generate_parts=true`, `texture=false`, `pbr=false`, utan Smart Low Poly eller quad. `smart_low_poly=true` overstyrer parts. For eit allereie valt produkt skal ny generering ikkje erstatte deling av den godkjende masteren.

Skil H Smart Low Poly under generering, P1/P2 lågpoly-generering og seinare `/mesh/decimate`. Bruk eksisterande master som kjelde ved seinare reduksjon. Vel basic v1 for eit høgare mellomnivå eller v3-retopologi for reell lågpoly der det passar, og kontroller avviket. Fullfør berre valde opne delar når nødvendig; `quick_cap` fyller grenser, medan standard AI-completion genererer ny geometri. Gjer ikkje completion, symmetri, skalering, flat botn eller pivotendring som skjult opprydding.

## 3. Gjer forma mekanisk

Lås del-ID-ar, mm-skala og felles koordinatsystem. Bruk den valde Tripo-overflata som formgrunnlag. Modellér opningar, veggar, feste, styreflater, låsar, knappar og haldarar eksplisitt og parametrisk der det er tenleg. Bevar ytre silhuett og detaljar når innmaten blir endra.

Bruk ei ærleg hybridløysing når ytterforma er mesh og mekanikken er analytisk CAD. Ein segmentert eller lukka mesh er ikkje automatisk ein redigerbar CAD-solid. Eksporter native CAD/STEP for faktiske BRep-delar og meshformat for meshdelane; opplys om dekninga.

Dimensjoner mot faktisk maskinvare, materiale og produksjonsmåte. Dokumenter klaringar og føresetnader. Kontroller korleis kvar del kjem inn, blir festa, blir betent og kan takast ut. Modellér geometrien som rettleiinga skal vise.

## 4. Kontroller og klargjer print

Kontroller lukka mesh/solids, positivt volum, utilsikta restar, kritiske veggar, kollisjonar, låse-/knapperørsler og innføringsvegar. Oppgi om rørslekontroll er kontinuerleg eller diskret prøvd. Lag små prøvedelar for kritiske passningar før hovuddelane.

Eksporter individuelle delar og tydeleg merkte printplater. Hald montert visingsmodell skild frå printlayout. Bruk faktisk skrivar-, dyse-, plate- og filamentprofil; lag ny slicing og sjå gjennom støtte og verktøybaner. For P1S/PLA med 0,4 mm dyse kan 0,20 mm lag, 3 veggar, 15 % gyroid og automatisk støtte vere eit startgrunnlag som må vurderast for modellen.

Skil visuelt konsept, digital mekanisk kontroll, slicer-kontroll og fysisk prøvd prototype. Oppgi berre status det finst resultat for.

## 5. Lag IKEA-liknande assembly

Bygg endelege tekniske bilete frå same verifiserte geometri og del-ID-ar. Bruk ortografisk/isometrisk projeksjon, fjerna skjulte linjer, svart strek på kvitt, få strekvekter, mykje luft og sparsam nynorsk tekst. Vis faktisk innføring, rotasjon og inngrep med eksplodering, piler og forstørra detaljar.

Lag framside, del-/verktøyoversikt med mengder, eksplodert oversikt, byggjesteg, funksjonsprøve og relevant feilsøking. Vis éi hovudhandling om gongen. Hald kamera, delnummer, pose og linjestil konsistente. Tilpass sidetalet til objektet.

Bruk imagegen til stil-/layoututkast ved behov; bygg endeleg layout og monteringsrender frå presise kjelder. Rasteriser PDF-en og sjå kvar side. Rett kollisjonar, avkutta grafikk, uleselege detaljar og tvitydig rekkjefølgje før levering.

## 6. Lagre og overlever

Lagre alle leverte bilete og synlege bileteutkast i rett Space med native biletblokker, også dei einskilde manualsider. Merk utkast og sluttsider. Kontroller tilgang og les tilbake at alle bileta er med. Ei filnamnliste eller eit ZIP-vedlegg erstattar ikkje biletblokkene.

Ta vare på referanse, rå Tripo-resultat, transformasjonar, CAD-kjelde, delmanifest/BOM, kontrollresultat, printfiler, illustrasjonsgrunnlag, PDF, side-PNG og portabel byggjekjelde. Bruk eksisterande repo for gitbaserte kjelder; lagre andre leveransar i Library og lenk frå Space. Ikkje stol på scratch eller mellombelse nedlastingslenkjer som varig lagring.

Når GitHub-synk er autorisert: lag ein avgrensa commit, bevar andres endringar, push utan force og kontroller publisert revisjon. Oppgi attståande fysisk prøvepass ved printfila. Avslutt med korte lenkjer og, når relevant, ein tett kodeblokk til lokal printagent: repo/revisjon, rett mappe, modellfiler, skrivarprofil, prøvedelar, godkjenningskrav og neste handling.
