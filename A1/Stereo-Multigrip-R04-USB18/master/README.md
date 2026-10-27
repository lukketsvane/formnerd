# ENTROPI samla CAD- og printprosjekt

`ENTROPI_MASTER.3mf` er den faste leveransefila for vidare arbeid med R04. Alle printdelane høyrer til denne eine prosjektfila, fordelte på namngjevne plater. Endra delar blir oppdaterte på plass. Sjå [prosjektreglane](../AGENTS.md).

[Opne masterfila](https://chatgpt.com/library?file_id=libfile_66eceed431c88191aa7e8dd1b2673c8d&account_id=personal). Denne lenkja og filidentiteten skal bevarast når innhaldet blir oppdatert. Den binære 3MF-leveransen blir lagra éin stad, ikkje kopiert inn i dette repositoriet i tillegg.

`source/build_backcase.py` og `cad/01_backcase.step` er kjelda og den solide CAD-modellen for det valde bakdekselet. `checks/` inneheld resultata frå CAD-, mesh- og slicerkontroll. Den fullstendige 30-delars STEP-samanstillinga, alle printdelane og skripta for å byggje og pakke treplatersprosjektet ligg i `Engineering/` inne i masterfila. Oppdater desse saman med modellen.

Arbeidsmappa `entropi-master` er mellomgrunnlaget for bygging, rendering, slicing og pakking. Ho er ikkje ei ekstra printleveranse. STEP-kjelder inne i 3MF-pakken kan hentast ut med eit ZIP-verktøy når modellen skal redigerast i eit CAD-program. Bambu Studio opnar printplatene direkte.

Kvar utgåve må dokumentere kva som er digitalt kontrollert og kva som står att som fysisk prøvepass. Slicing eller lagring av ei fil dokumenterer ikkje at utskrifta er starta eller at delane passar den faktiske maskinvara.

Den valde baksida har åtte asymmetriske opningar, 2,4 mm integrert bakvev og innfelt finne/ENTROPI. Bakdekselet på plate 1 er slica til 3 t 10 min 49 s og 31,25 g. Begge dei andre platene er òg slica. 0,4 mm nominell klaring til powerbanken og 3,95 mm minste ribbe er digitalt kontrollerte; fysisk prøvepass står att.
