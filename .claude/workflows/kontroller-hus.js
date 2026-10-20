export const meta = {
  name: 'kontroller-hus',
  description: 'Uavhengig, målande kontroll av ei printpakke laga med verktoy/bygg_hus.py (print, toleransar, optikk/USB, montering) + kritikar. args: {prosjekt: "A2"}',
  whenToUse: 'Etter at verktoy/bygg_hus.py har bygd eit hus og før nokon kallar printpakka klar for print.',
  phases: [{ title: 'Kontroll', detail: 'fire målande kontrollørar' }, { title: 'Kritikk', detail: 'kritikar over alle resultata' }],
}
const P = (args && args.prosjekt) || 'A2'
const TMP = `/tmp/kontroller-hus-${P}`
const CTX = `Repo: noverande arbeidsmappe (formnerd). Prosjekt: ${P}. Huset er bygd med verktoy/bygg_hus.py ${P} (køyr frå rota; bygg(P) returnerer deler, innmat, kontroll; ca. 90 s), med parametrar i ${P}/print/parametrar.json (les med bygg_hus.les(sti)) og rapport i ${P}/print/kontroll.json. Publiserte delmål med kjelder: ${P}/print/delmaal.json. Les ${P}/README.md og .claude/skills/formnerd-hus/SKILL.md først.
Koordinatar (montert, ${P}/print/montert/*.glb): x = djupn, fram +x (linsene peikar +x); y opp; z = breidd. Delar: fremre_skal (blir skyvd på langs -x), bakre_skal, innmatsramme (plate klemd i skøyten med styreben og hjørnehyller for stablane), stabel_<i>_* (elektronikkmodellen). Printretta STL-ar: ${P}/print/*.stl og ${P}/print/provebitar/*.stl (skala skøytesida ned, ramma plata ned). Printar: Bambu P1S, 0,4 dyse, 0,20 mm lag, PLA, tre-støtte berre frå plata, elefantfotkompensasjon 0,15 på. manifold3d (Manifold.min_gap, slice, CrossSection.offset), trimesh, numpy, scipy og scikit-image er installerte.
REGLAR: Ikkje endre noko i repoet. Arbeid berre i di eiga mappe under ${TMP}/. Skriv aldri ut hemmelege miljøvariablar. Mål, ikkje gjett: kvar påstand treng eit tal frå eit skript du har køyrt. Alvor: blokkerer = printen feilar eller delane kan ikkje setjast saman; hoeg = truleg feil passing eller print; middels = risiko verd å rette; laag = kosmetisk; ok = kontrollert og i orden. Skriv tittel, prov og fiks på nynorsk, og fiksen skal peike på ein parameter eller ei line i bygg_hus.py.`
const S = {
  type: 'object',
  properties: {
    funn: { type: 'array', items: { type: 'object', properties: {
      tittel: { type: 'string' }, alvor: { type: 'string', enum: ['blokkerer', 'hoeg', 'middels', 'laag', 'ok'] },
      prov: { type: 'string' }, fiks: { type: 'string' } }, required: ['tittel', 'alvor', 'prov', 'fiks'] } },
    samla_dom: { type: 'string' },
  },
  required: ['funn', 'samla_dom'],
}
const LINSER = [
  { key: 'print', prompt: `LINSE: PRINTBARHEIT. Snitt kvar STL lag for lag (0,2 mm): kontakt og samanheng i lag 1, og breidd (del smalare enn 2 liner). Finn flate overheng og øyar som startar i lufta. Kan tre-støtte frå plata nå dei, og kan støtta fjernast gjennom den opne enden? Mål minste veggtjukkleik, særleg rundt linsehol, fresing, synsfeltkjegle og USB-tunnelar. Sjekk at 45°-fasane (skulder, fuge, platekant) er sjølvberande, og sjekk klikk-knastane: form, kva lag dei ligg i, utstikk og interferens mot gropa. Mål òg om kvar del får plass på plata.` },
  { key: 'variantar', prompt: `LINSE: ROBUSTHEIT MOT MÅLTE VERDIAR. Køyr bygg_hus.bygg(P) i minnet med multiprocessing Pool(3) for: nominell; ytterpunkta for kvar stabel-parameter med "målt": false og eit spenn i delmaal.json (t.d. linsetopp_over_pcb, djupn, linse_frå_sd_ende, linse_tverr, lengd_mb); og den verste kombinasjonen du kan grunngje. Rapporter for kvar variant: byggjer han, kollisjonar_mm3, påskyving_mm3, klaring_til_fremre_skal_mm, linseløp_til_holkant_mm, linse_under_maks, usb_kontakt_til_ytterflate_mm og x_skøyt. Mål klaringane i éin variant på nytt med din eigen eksakte min_gap.` },
  { key: 'optikk-usb', prompt: `LINSE: OPTIKK OG USB. (1) Kast ei kjegle frå kvar linsetopp (pupill r 0,75 mm; test òg pupillen flytt 1,5 mm sidevegs og linsetoppen 2,4 mm lågare) mot heile huset, og rapporter største frie halvvinkel mot kravet i parametrar.json (synsfelt_halvvinkel). (2) Rekn ut sidetoleransen for linseløpet i holet, saman med spelet for MB i lomma, mot ±1,5 mm handmontert linse. (3) Prøv USB-pluggar (10,6 × 8,5 maks og 10 × 6 typisk) langs innstikksretninga gjennom tunnelen, med kontakthøgda flytt -0,85 til +0,3 mm. (4) Mål kor mykje fresing og kjegle skjer ut av ytterflata, og om nye tynne veggar (< 1,2 mm) har oppstått.` },
  { key: 'montering', prompt: `LINSE: MONTERINGSREKKJEFØLGJE OG HALD, med eksakte manifold-boolske operasjonar. (a) Senk kvar stabel langs -x ned i ramma (0–20 mm): er vegen fri, kviler MB på hyllene, og kor stort er sidespelet? Sjekk òg loddepad og loddespissar mot hyllene og plata. (b) Senk ramma ned i bakre skal: er vegen fri, og kviler plata på enden av leppa? (c) Skyv fremre skal på i steg på 0,05 mm frå 0 til 6 mm, med knastane: rapporter interferensvolum og kor mykje leppa må gi etter. (d) Sluttstilling: aksialt spel for ramma, kontaktflate mellom platekanten og skuldra, og kor langt kvar stabel kan flytte seg fram. (e) Kan skala dragast frå kvarandre igjen?` },
]
phase('Kontroll')
const res = await parallel(LINSER.map(l => () => agent(`${CTX}\n\nDi arbeidsmappe: ${TMP}/${l.key}/ (lag ho).\n\n${l.prompt}\n\nReturner konkrete funn med alvor, prov (tal frå skript du har køyrt) og minimal fiks.`, { label: `kontroll:${l.key}`, phase: 'Kontroll', schema: S })))
const resultat = res.map((r, i) => r ? { linse: LINSER[i].key, ...r } : { linse: LINSER[i].key, feil: 'agenten returnerte ingenting' })
phase('Kritikk')
const kritikk = await agent(`${CTX}\n\nDi arbeidsmappe: ${TMP}/kritikk/ (lag ho).\n\nFire uavhengige kontrollørar returnerte:\n${JSON.stringify(resultat)}\n\nOPPGÅVE: kritikar for heilskapen. (1) Mål sjølv dei to viktigaste påstandane på nytt, altså dei ein print eller montering ville feile på. (2) Finn det ingen av dei sjekka, som kan få første print eller montering til å feile: støtte inne i lukka rom, vridning av tynne skal, utmatting i knastane, strekk på USB-kontakten, varme frå elektronikken i eit lukka PLA-skal (rekn med tal), tilgang til SD-kortet, og lys frå blitsen inne i huset. (3) Gi ein ærleg samla dom: er pakka klar for prøveprint av prøvebitane, og kva må vere sant før heile huset blir printa? Same skjema.`, { label: 'kritikk', phase: 'Kritikk', schema: S })
return { prosjekt: P, kontroll: resultat, kritikk }
