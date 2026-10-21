# IKEA-liknande assembly frå CAD

## Visuell standard

Bruk monteringsreferansane som kvalitetsmål: rein svart kontur på heilt kvitt, ortografisk/isometrisk geometri, synleg tjukkleik og presise samanføyingar. La store teikningar, delmengder, rørslepiler og detaljar bere forklaringa. Bruk eigen produkttittel og eigne symbol.

Bruk få strekvekter: tydeleg ytterkontur, lettare detaljar og fine leiarar. Bruk stipling med konsekvent funksjon, til dømes innføringslinje eller målposisjon. Fjern skjulte kantar og tesselleringsnett. Unngå svarte flekkar frå for små detaljar ved faktisk printstorleik.

Hald same grunnkamera og skala gjennom samanhengande steg. Roter berre for å vise ei elles skjult handling, og gjer vendinga tydeleg. Bruk modellavleidd line-render, vektor der det fungerer og raster med tilstrekkeleg oppløysing for print der meshforma krev det. Bevar kjelda for ny projeksjon.

## Referansesider

Ti sider frå ein ekte monteringsrettleiing er valde som stilmål. Dei er tredjepartsmateriale og ligg difor ikkje i skillpakken, men i repoet [`referansar/ikea-monteringsstil/`](https://github.com/lukketsvane/formnerd/tree/claude/stereoskopisk-kamerahus-cjqyqr/referansar/ikea-monteringsstil). Sjå dei før du teiknar når du har repoet; elles gjeld skildringa under:

- `01-framside.jpg`, `02-produkt.jpg`: tittel og éi stor isometrisk strekteikning av det ferdige produktet, i tynn sideramme.
- `03-deloversikt.jpg`: rutenett med små isometriske delar, kvar med nummer i sirkel og mengd (①×1).
- `04-beslag.jpg`: beslag med bokstav over og mengd under (A ×81), rader skilde med vassrette strekar.
- `05-eksplodert-oversikt.jpg`: heile produktet eksplodert, med nummer i sirkel på kvar del og innfelt boks for underenheiter som går igjen (×8).
- `06-steg-forstorringsbobler.jpg`: førebuing av delar med stipla innstikksliner, merke som «A×6» og runde forstørringsbobler som viser ei handling i tre trinn med hole piler mellom.
- `07-steg-underdelar.jpg`, `08-steg-beslagkolonne.jpg`: fleire delhandlingar på same side, hole piler (⇨) mellom før og etter, og beslagkolonne til høgre med bokstav, bilete og mengd for steget.
- `09-steg-multiplikator.jpg`: stor multiplikator (×8) ved figurar som skal gjentakast.
- `10-atvaring-verktoy.jpg`: åtvaringar, verktøy og forbodssymbol.

Felles for alle: berre svart strek på kvitt, jamn linjevekt, inga skugge eller farge, glas markert med to skrå strekar, enkel sans-serif, tal og bokstavar i staden for tekst.

## Bygg frå deldata

Lag scenemanifest med del-ID-ar, synlege delar, transformasjonar, innføringsvektor/rotasjonsakse og kamera per steg. Bruk monterte posisjonar som felles fasit. Eksplodering er ei illustrasjonstransformasjon av rette delar langs forståelege retningar.

Vis før/etter eller eksplodering mot målposisjon når handlinga er tvitydig. Teikn piler langs faktisk innføring og rotasjonspiler med mekanismens vinkel. La detaljsirkelen vise rett grensesnitt med leiar frå oversikta. Vis verktøy, grep og kontaktflate når det avgjer handlinga.

Bruk skjematisk elektronikk når målgrunnlaget ikkje finst. Merk nominelle volum og pinnenamn eintydig. Skil straumveg, signalveg og mekanisk innføring. Vis berre leidningar, skruar, fjører og låserørsler som finst i modell/BOM.

Bruk imagegen til sidestil, kameravinkel og rytmeutkast. Når brukaren har lagt ved monteringssider som stilreferanse, legg dei ved biletkallet og lag eit eige utkast for å avklare layout, strekvekter og luft. Bygg endelege tekniske figurar med CAD, deterministisk SVG/vektor eller modellavleidd raster, og samanlikn sidene med stilutkastet. Ikkje baser presise byggjesteg på eit generert eksplodert bilete.

## Sidefølgje

1. Framside med eitt stort bilete av faktisk produkt, namn og revisjon.
2. Deloversikt med same ID-ar som modell/BOM/printfiler, mengder og tydelege teikningar.
3. Verktøy, maskinvare og førebuing som faktisk trengst; relevante åtvaringar.
4. Eksplodert oversikt med lesbare ID-ar og rett delsamanheng.
5. Fysisk moglege byggjesteg, éi hovudhandling per scene og nødvendig kontroll før neste steg.
6. Open funksjonsprøve før lukking når innmaten elles blir utilgjengeleg.
7. Sluttkontroll, feilsøking, revisjon og relevant skilje mellom mål/føresetnader og prøvd status.

Tilpass omfanget til objektet. A1 sine 29 sider og 23 steg er eit døme, ikkje eit obligatorisk sidetal.

## Steglayout og QA

Plasser tydeleg stegnummer øvst og la hovudfiguren få mesteparten av sida. Samle aktuelle delar/mengder i ei avgrensa sone. Bruk detaljsirklar for lås, finger og verktøy. Bruk korte handlingsverb på nynorsk og konkrete kontrollpunkt. La teikninga få plass framfor lange avsnitt og dekorative kort.

Hald del-ID-ar unna hola/kantane dei forklarer. Skil leiarar frå produktkontur og monteringspiler. Kontroller låsedetaljar for innføring, inngrep, rotasjon og ferdig posisjon. Bruk typografi som er lesbar på faktisk A4.

Bygg PDF frå kjelde, rasteriser og sjå alle sider. Lever separate sidebilete, eitt bilete per motiv/side. Kontroller at modell/teikning viser same delar; at rørsle og rekkjefølgje er fysisk mogleg; at mengdene stemmer; og at tekst, nummer, piler og detaljar ikkje overlappar eller blir avkutta. Kontroller same revisjon i PDF, side-PNG og kjeldepakke.

Pakk portabel PDF-byggjar med brukt figurgrunnlag og avhengigheitsliste. Prøv bygging frå ny utpakking. Lagre PDF og kvar side på den valde varige filstaden. Når prosjektet brukar Space, bruk fungerande referansar og native bilete der. Les tilbake og samanlikn bilettalet med eksporten. Lenke til repo når det finst, og oppgi nødvendig fysisk prøvepass.
