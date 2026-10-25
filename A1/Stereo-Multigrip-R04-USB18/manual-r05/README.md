# ENTROPI R04 USB18: monteringsutkast

Ti separate A4-sider med vektorteikningar frå STEP-solidane i R04. Skjulte kantar er fjerna med OpenCascade HLR. Elektronikkvoluma er rekonstruerte med dei same parametrane som byggjekjelda; små kontaktpinnar er utelatne frå teikningane for lesbarheit. Geometrien og printfila er uendra.

Køyr `python source/build_manual.py` frå denne mappa. Krav: Python 3, CadQuery 2.7, NumPy, ReportLab og PyMuPDF. Kjelde-STEP og parameter ligg i foreldremappa. `scene-manifest.json` bind kvar figur til del-ID, kamera og eksplodering. PDF og separate SVG/PNG-sider blir bygde frå same kjelde.

Innføringa av kamerakorta er ikkje avklart. Ein kontrollert rett innføringsveg bakfrå gav kollisjon mot kameraberaren. Side 3 viser difor sluttplassering utan rørslepiler. Resten av sidefølgja er eit monteringsutkast, ikkje ei ferdig fysisk verifisert byggjerettleiing. Bakhaldarinnføringa og fleire endelege posisjonar er digitalt kontrollerte. Faktisk passform på den nye utskrifta, pluggane og kabelbøyane er ikkje stadfesta.
