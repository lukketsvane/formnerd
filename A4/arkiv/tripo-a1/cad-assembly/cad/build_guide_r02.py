import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review'
FIG = OUT / 'steps-r02'
PATH = OUT / 'A1-Byggjesteg-R02.pdf'
W, H = landscape(A4)
INK = colors.HexColor('#17191a')
GREY = colors.HexColor('#697174')
LIGHT = colors.HexColor('#eff1f1')
ACCENT = colors.HexColor('#d35419')
pdfmetrics.registerFont(TTFont('Guide', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('GuideBold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
styles = {
    'body': ParagraphStyle('body', fontName='Guide', fontSize=10.5, leading=15.3, textColor=INK),
    'small': ParagraphStyle('small', fontName='Guide', fontSize=8, leading=11.3, textColor=GREY),
    'action': ParagraphStyle('action', fontName='GuideBold', fontSize=12, leading=16, textColor=INK),
    'check': ParagraphStyle('check', fontName='Guide', fontSize=10, leading=14, textColor=INK),
    'screen': ParagraphStyle('screen', fontName='Guide', fontSize=13, leading=19, textColor=INK),
}
pages = []


def page(number, title, phase, figure, actions, checkpoint, parts='', note='', power=''):
    pages.append(dict(number=number, title=title, phase=phase, figure=figure, actions=actions,
                      checkpoint=checkpoint, parts=parts, note=note, power=power))


page('A1', 'Bygg kameraet, steg for steg', 'ARDUINO IDE > ESP32-CAM > UTLØYSAR > KAMERAHUS', 'm12-finished.png', [
    ('Start med elektronikken', 'Få eit testbilete på telefonen før du set delane i huset.'),
    ('Bygg éin del om gongen', 'Store isometriske teikningar viser delen, retninga og neste kontroll.'),
    ('Bruk rett versjon', 'A1-assembly R01 og byggjesteg R02. Denne ruta brukar ESP32-CAM + MB og ingen SD-kort.'),
], 'Elektronikken er skjematisk. Plastdelane er rendera frå dei leverte CAD-/meshdelane.',
     note='Rettleiing for ein prototype. Faktiske kortmål, kamerafleks, brytar og fysisk passform må stadfestast før sluttmontering.')

page('00', 'Finn delane på bordet', 'DELLISTE / PRINTDELAR', 'm01-inventory.png', [
    ('Huset', '01 ytterskal ×1, 02 baklokk ×1, 04 frontring ×1.'),
    ('Innmat og knapp', '03 kamerahaldar ×1, 07 utløysar ×1, 08 kassett ×1, 09 kameraklemme ×1.'),
    ('Låsar og hjelp', '05 låsar ×4. I tillegg: 06 verktøy ×1 og testhylse ×1.'),
], 'Du har 11 plastdelar til produktet. Verktøyet og testhylsa kjem i tillegg.',
     note='Filnamna i print/ startar med dei same delnummera. Samla assembly-3MF er ei vising av montert posisjon.')

page('01', 'Finn CAM-kortet og MB-kortet', 'ELEKTRONIKK / IDENTIFISERING', 'e01-stack.png', [
    ('E1 er datamaskina i kameraet', 'ESP32-CAM har kamerakontakt, kameramodul og to pinnerader.'),
    ('E2 er USB-adapteren', 'ESP32-CAM-MB har USB-port og to sokkelrader. Han gir straum og seriell programmering.'),
    ('Arduino IDE er på PC-en', 'Eit separat Arduino-kort trengst ikkje i denne byggjeruta. Brytar og leidningar kan hentast frå startsettet dersom dei passar.'),
], 'Legg fram CAM, MB, kameramodul, datakabel og PC. La SD-kortet liggje ute.',
     parts='E1 CAM ×1  /  E2 MB ×1  /  kamera med fleks ×1', power='USB FRÅ',
     note='Teikninga viser funksjon og lagdeling, ikkje eit målt kortoppsett. Samanlikn med merkinga på ditt sett.')

page('02', 'Set CAM rett ned i MB', 'ELEKTRONIKK / TO PINNERADER', 'e01-stack.png', [
    ('Kontroller retninga', 'Les pinnenamna på begge korta. Match namna; ikkje bruk berre plasseringa av linsa som orientering.'),
    ('Start begge radene samstundes', 'Sjekk at ingen pinne står utanfor eller ei rad forskyvd. Hald i kortkantane.'),
    ('Press jamt ned', 'Støtt MB under soklane. Stopp dersom pinnane bøyer seg eller kortet møter motstand.'),
], 'Begge pinneradene står rett og like djupt i soklane. Ingen pinnar er skeive.',
     parts='E1 + E2', power='USB FRÅ',
     note='Behald kamerafleksen slik han kom frå leverandøren. Ikkje opne ein fungerande kontakt berre for å følgje teikninga.')

page('03', 'Kople USB til PC-en', 'ELEKTRONIKK / FØRSTE STRAUM', 'e02-usb.png', [
    ('Bruk ein datakabel', 'Set den vesle pluggen i MB og den andre enden i PC-en. Porttypen på ditt MB-kort avgjer kabelen.'),
    ('Finn serieporten', 'Sjå kva port som kjem til når du koplar til. Noter COM-port på Windows eller /dev-port på macOS/Linux.'),
    ('Ingen port?', 'Prøv ein kjend datakabel og ein annan PC-port. Bruk rett USB-UART-drivar for brikka som faktisk står på MB.'),
], 'PC-en ser éin ny serieport. Det viser at datatilkoplinga er oppretta.',
     parts='CAM/MB + USB-datakabel + PC', power='USB PÅ',
     note='Vanlege MB-kort har Micro-USB og CH340G. USB-porten er ikkje dokumentasjon på batterilading eller USB-biletfiler.')

page('04', 'Installer Arduino IDE og ESP32', 'PROGRAMMERING / PC', 'ui-install', [
    ('Installer Arduino IDE', 'Hent programmet frå arduino.cc/en/software og opne det.'),
    ('Legg inn pakkekjelda', 'Opne Preferences / Settings. Lim inn den stabile ESP32-adressa i Additional Boards Manager URLs.'),
    ('Installer kortpakka', 'Opne Boards Manager, søk esp32 og installer esp32 by Espressif Systems. Noter versjonen du brukar.'),
], 'ESP32-pakka finst i Boards Manager og er installert.',
     note='A1-skissa er kompilert med esp32 3.3.12. Menynamn varierer med operativsystem og IDE-versjon. Pakkelenka kan klikkast i PDF-en. [S1]')

page('05', 'Opne A1-programmet', 'PROGRAMMERING / RETT KORT OG PORT', 'ui-board', [
    ('Opne skissa frå A1-mappa', 'Opne firmware/A1_Bench_Camera/A1_Bench_Camera.ino. Behald mappa og skissa med same namn.'),
    ('Vel kamerakortet', 'Vel AI Thinker ESP32-CAM. MB er adapteren, ikkje kortmodellen du skal velje i IDE-en.'),
    ('Vel serieporten frå steg 03', 'Bruk PSRAM og AI Thinker-standardane. Start med 115200 som opplastingsfart om høgare fart er ustabil.'),
], 'Skissa heiter A1_Bench_Camera, kortet er AI Thinker ESP32-CAM og porten er vald.',
     note='A1-skissa har kamerakartet innebygd. Ho brukar GPIO13-utløysar og eit eige Wi-Fi-nett; ingen SD-kort eller heimeruter er nødvendig.')

page('06', 'Last programmet inn på ESP32', 'PROGRAMMERING / OPPLASTING', 'ui-upload', [
    ('Trykk Verify, så Upload', 'Rett kompileringsfeil før du prøver å laste opp. La kameraet liggje ope på bordet.'),
    ('Berre dersom tilkoplinga står fast', 'Hald IO0/BOOT inne, trykk og slepp RST. Start Upload og hald IO0 gjennom reset/tilkoplinga. Slepp når skrivinga er i gang.'),
    ('Start vanleg drift', 'Etter opplasting: slepp IO0 og trykk RST. Opne Serial Monitor med 115200 baud.'),
], 'IDE-en melder ferdig opplasting, og seriell logg viser oppstart utan kamerafeil.',
     power='USB PÅ', note='MB-revisjonar har ulik resetkopling. IO0/BOOT og RST er programmeringsknappar; ingen av dei er fotoutløysaren. [S2]')

page('07', 'Ta det første testbiletet', 'FUNKSJONSPRØVE / TELEFON ELLER PC', 'ui-photo', [
    ('Kople til kameraet sitt Wi-Fi', 'Vel A1-Camera. Passord: A1camera2026. Godta tilkopling utan internett.'),
    ('Opne nettlesaren', 'Skriv http://192.168.4.1/ i adressefeltet. Trykk på knappen for nytt foto.'),
    ('Last ned og opne JPEG', 'Rett kameraet mot eit lyst motiv. Kontroller at motivet er skarpt nok, og at teljaren aukar.'),
], 'Du ser eit nytt bilete frå det faktiske kameraet og kan laste ned JPEG-fila.',
     power='USB PÅ', note='A1-programmet lagrar berre siste foto i RAM. Last ned det du vil behalde før du tek neste foto eller koplar frå straumen.')

page('08', 'Kople frå før du legg til knappen', 'ELEKTRONIKK / ARBEID UTAN STRAUM', 'e08-disconnect.png', [
    ('Lagre testbiletet', 'Last det ned frå nettlesaren dersom du vil behalde det.'),
    ('Trekk USB ut av MB', 'Hald i pluggen. La CAM stå i soklane medan du kontrollerer pinnemerkinga.'),
    ('Finn brytaren i settet', 'Bruk ein normalt open trykkbrytar. Mål brytaren før du vurderer det nominelle 6 × 6 mm setet.'),
], 'USB er fysisk kopla frå. Ingen annan straumforsyning er tilkopla.',
     power='USB FRÅ', note='Batteri, lademodul og USB-C-lading er ikkje ein del av denne benktestruta.')

page('09', 'Finn to kontaktar som sluttar ved trykk', 'UTLØYSAR / MÅLING FØR KOPLING', 'e03-switch-test.png', [
    ('Bruk kontinuitet på multimeteret', 'Mål mellom to bein på den lause brytaren. Test både utan og med trykk.'),
    ('Vel eit fungerande kontaktpar', 'Utan trykk: open krins. Med trykk: samband. Bein som allereie har samband utan trykk, er feil par.'),
    ('Merk dei to vala', 'Desse to kontaktane skal til GPIO13 og GND. Fire bein betyr ikkje fire separate brytarar.'),
], 'Det valde paret har berre samband medan du held knappen inne.',
     parts='Normalt open brytar + multimeter', power='USB FRÅ',
     note='1-4 er teikningsnamn, ikkje stadfesta merking på din brytar. Eit multimeter er nødvendig for denne kontrollen.')

page('10', 'Kople GPIO13 til knappen og GND', 'UTLØYSAR / ELEKTRISK KOPLING', 'e04-schematic.png', [
    ('Følg merkinga på CAM-kortet', 'Éin leidning frå GPIO13 / IO13 til den eine målte brytarkontakten.'),
    ('Lag retur til GND', 'Den andre målte kontakten går til GND på same kort. Isoler leiarane og gi leidningane litt slakk.'),
    ('Kontroller koplinga', 'Ikkje bruk IO0, RST eller ein 5 V-pinne. Ingen SD-kort: GPIO13 er òg brukt av SD-bussen.'),
], 'Kontinuitet: GPIO13 til GND berre ved trykk. Ingen kortslutning mot 5 V eller 3V3.',
     parts='Brytar + to isolerte leidningar', power='USB FRÅ',
     note='INPUT_PULLUP ligg i A1-programmet. Signalet er 3,3 V-logikk. Koplingsskjemaet viser pinnamn, ikkje fysisk pinneplassering. [S3, S4]')

page('11', 'Prøv den elektriske utløysaren', 'FUNKSJONSPRØVE / FØR INNBYGGING', 'e05-wiring.png', [
    ('Kople USB til att', 'Opne A1-Camera og kameraet si nettside som i steg 07.'),
    ('Trykk den lause brytaren éin gong', 'Vent på nytt bilete og at teljaren aukar med éin. Hald knappen inne: han skal ikkje ta ei rekkje bilete.'),
    ('Slepp og trykk på nytt', 'Ta minst fem foto, og prøv nedlasting. Trekk USB ut att før mekanisk arbeid.'),
], 'Fem separate trykk gir fem nye foto. Knappen verkar før han blir bygd inn i huset.',
     power='USB PÅ FOR TEST, SÅ FRÅ',
     note='Denne funksjonen er lagd inn i A1-skissa. Standard CameraWebServer reagerer ikkje automatisk på ein fysisk knapp.')

page('12', 'Prøveprint éin lås først', 'MEKANIKK / TOLERANSEPRØVE', 'm02-lock-test.png', [
    ('Print testhylsa og éin 05-lås', 'Vel faktisk P1S, dyse og filament i Bambu Studio. Kontroller første lag og støtte.'),
    ('Før øyra inn i spora', 'Bruk innføringsretninga på teikninga. Drei 90° med verktøy 06.'),
    ('Lås opp og gjenta', 'Låsen skal halde aksialt, men kunne løysast att utan skade. Stopp ved sprekk eller behov for stor kraft.'),
], 'Prøvelåsen kan låsast og løysast fleire gonger med filamentet du skal bruke.',
     parts='05 ×1 + 06 ×1 + testhylse ×1',
     note='Print resten først når prøva passar. Dei digitale kontrollane erstattar ikkje denne toleranseprøva.')

page('13', 'Kontroller innmaten før du pressar noko inn', 'MEKANIKK / MÅL OG PRØVEPASS', 'e07-flex.png', [
    ('Mål den samla CAM/MB-stakken', 'Samanlikn kort, soklar, USB-plugg og leidningar med rommet i 03. Modellert stakkplass: 28 × 48 × 22 mm.'),
    ('Kontroller kamerafleksen', 'Linsa skal nå framsetet utan strekk, skarp knekk eller laus kontakt. Behald rett sensororientering.'),
    ('Kontroller brytarhøgda', 'Brytaren må passe 08, og 07 må trykkje og sleppe han. 6 × 6 mm er berre eit nominelt fotavtrykk.'),
], 'Alle faktiske delar passar og kan fungere utan tvang. Ved avvik må CAD-en tilpassast før neste steg.',
     power='USB FRÅ', note='Dette er eit stoppunkt ved avvik. Kortvariant, flekslengd, brytarhøgd og klemmas fasthalding er ikkje fysisk stadfesta.')

page('14', 'Legg CAM/MB i haldaren', 'MEKANIKK / DEL 03', 'm03-carrier.png', [
    ('Ta berre i kortkantane', 'Hald kablar og kamerafleks unna kontaktflater og styrespor.'),
    ('Prøv plasseringa i 03', 'Sjå snittet. Vegen inn må prøvast med dei faktiske korta. Prøv kabelpluggen medan haldaren er laus.'),
    ('Prøv fasthaldinga', 'Elektronikken skal ikkje falle ut eller flytte seg når kameraet blir snudd. Ikkje klem komponentar eller loddepunkt.'),
], 'Kortet sit utan spenn. USB-pluggen og to utløysarleidningar har fri plass.',
     parts='03 ×1 + ferdig benktesta CAM/MB', power='USB FRÅ',
     note='Elektronikken er eit nominelt volum. Teikninga viser plassering, ikkje ein verifisert innføringsveg for ditt kort. Prøvepass frå steg 13 er nødvendig.')

page('15', 'Før kameraet fram og set på klemma', 'MEKANIKK / DEL 09 OG FRAMSETET', 'm04-camera.png', [
    ('Før modulen fram', 'Legg den vesle kameramodulen i framsetet på 03 med linsa peikande fram.'),
    ('Legg flekskabelen i ein mjuk boge', 'Ingen vriding ved kontakten og ingen skarp brett. Ikkje trekk i kabelen for å nå setet.'),
    ('Set på 09 bak modulen', 'Klemma skal halde modulen utan å presse linsa, sensorhuset eller flekskontakten.'),
], 'Modulen er halden, linsa er fri og flekskabelen er avlasta. Elles: tilpass innfestinga.',
     parts='03 + kameramodul + 09 ×1', power='USB FRÅ',
     note='09 har nominelle styretappar. Faktisk låsing og retur ved demontering må prøvast med den fysiske modulen.')

page('16', 'Før utløysaren ned ovanfrå', 'MEKANIKK / DEL 07 I DEL 01', 'm05-button.png', [
    ('Fjern støtterestar i føringa', 'Prøv knappen utan brytar og kassett først. Ta bort laus plast utan å endre føringsforma.'),
    ('Før 07 ned i toppopninga', 'Stemmet går ned i huset. Toppen skal følgje den valde ytterforma.'),
    ('Prøv rørsla', 'Knappen skal gli fritt. Modellert mekanisk slag er 1,2 mm; dette er ikkje brytaren si tillatne overvandring.'),
], 'Knappen kan flyttast fritt i føringa før kassetten blir sett inn.',
     parts='01 ×1 + 07 ×1', power='USB FRÅ')

page('17', 'Set brytaren i kassetten', 'MEKANIKK / DEL 08', 'm06-switch-seat.png', [
    ('Legg brytaren i setet', 'Bruk den målte og benktesta brytaren. Kontaktane skal ha klaring til plast og kvarandre.'),
    ('Legg leidningane bakover', 'Hald dei unna gaffelen som skal fange utløysarflensen.'),
    ('Prøv trykkpunktet laust', 'Brytaren skal bli trykt inn før mekanisk stopp og sleppe heilt når knappen blir sleppt. Juster setet ved feil høgd.'),
], 'Brytaren sit stabilt og kan aktiverast utan å bli overbelasta eller halde inne.',
     parts='08 ×1 + brytar med to leidningar', power='USB FRÅ',
     note='Ikkje lim eller tving inn ein brytar som ikkje passar. Brytarhøgd, returkraft og fasthalding er enno ikkje målt på det eigde settet.')

page('18', 'Skyv kassetten inn bakfrå', 'MEKANIKK / DEL 08 FANGAR DEL 07', 'm07-cassette.png', [
    ('Hald utløysaren lett oppe', 'La flensen stå slik at den opne gaffelen i 08 kan gå rundt stemmet.'),
    ('Skyv 08 inn frå baksida', 'Følg den rette pila. Leidningane går bakover og vidare i kabelvegen.'),
    ('Prøv utløysaren', 'Kontroller klikk, full retur og at ingen leiar blir klemd. Baklokket held kassetten i lengderetninga når huset er lukka.'),
], 'Utløysaren går tilbake kvar gong og kassetten står rett i føringa.',
     parts='01 + 07 + ferdig 08', power='USB FRÅ')

page('19', 'Skyv kamerahaldaren inn bakfrå', 'MEKANIKK / DEL 03 I DEL 01', 'm08-carrier-insert.png', [
    ('Samle leidningane i kabelvegen', 'Legg GPIO13/GND-para slik at dei ikkje går mellom styreflater.'),
    ('Skyv 03 rett fram', 'Kamera og klemme er på plass frå steg 15. Stopp om linsa eller flekskabelen møter huset.'),
    ('Kontroller framme og bak', 'Linsa står sentrert i frontopninga. USB-plugg og leidningar har fri plass i serviceopninga.'),
], 'Haldaren er heilt inne utan klemde leidningar. Linsa og kabelen har fri rørsle.',
     parts='01 + 07/08 + ferdig 03/09', power='USB FRÅ',
     note='Retninga er henta frå den mekaniske modellen. Faktisk USB-pluggvolum og fleksføring må kontrollerast under prøvepass.')

page('20', 'Prøv kameraet med huset ope', 'FUNKSJONSPRØVE / SISTE INNSYN', 'e06-bench.png', [
    ('Kople til USB utan å lukke huset', 'Hald innmaten på plass. Kontroller at pluggen ikkje dreg i kortet.'),
    ('Prøv den ytre utløysaren', 'Ta fem foto via 07, sjå teljaren og last ned eit bilete. Prøv også nettlesarknappen.'),
    ('Sjå etter klem og rørsle', 'Sjekk kamerafleks, leidningar og full knappretur. Last ned fotoet og trekk USB ut att.'),
], 'Både fysisk knapp og nettsida gir foto med elektronikken i huset. USB er frå før lukking.',
     power='USB PÅ FOR TEST, SÅ FRÅ',
     note='Figuren viser benkprinsippet. Huset skal stå ope under denne prøva, slik at du kan sjå alle kontaktane.')

page('21', 'Set inn frontringen og drei 45°', 'MEKANIKK / DEL 04', 'm09-bezel.png', [
    ('Finn bajonettspora', 'Før øyra på 04 inn i dei tilsvarande inngangane i huset.'),
    ('Før ringen heilt inn', 'Ikkje press mot den faktiske kameralinsa. Ho skal vere fri innanfor ringen.'),
    ('Drei til låst posisjon', 'Drei 45° langs låsekanalen. Kontroller at ringen held, og at han kan løysast att.'),
], 'Frontringen sit jamt og held aksialt. Linsa er urørt og fri.',
     parts='04 ×1 + hus med innmat', power='USB FRÅ',
     note='Opninga er 30 mm i CAD. Dette er ikkje ei 30 mm optisk linse; faktisk biletkant må testast i steg 24.')

page('22', 'Legg på baklokket', 'MEKANIKK / DEL 02', 'm10-cover.png', [
    ('Sjå langs heile fugekanten', 'Flytt alle leidningar og kamerafleks innanfor huset. Ingen kabel skal liggje over styretunga.'),
    ('Før 02 rett inn bakfrå', 'Tunga styrer lokket. Bruk lett handkraft og jamt trykk.'),
    ('Kontroller alle fire låsehola', 'Lokket skal sitje jamt før du set inn låsane. Låsane skal ikkje trekkje eit skeivt lokk på plass.'),
], 'Fuga er jamn, lokket ligg på setet og alle fire låsehola er på linje.',
     parts='02 ×1 + samla hus', power='USB FRÅ',
     note='Modellert fuge er 0,30 mm. Prøveprint og etterarbeid avgjer den faktiske passforma.')

page('23', 'Set inn fire låsar og drei 90°', 'MEKANIKK / DEL 05 OG VERKTØY 06', 'm11-locks.png', [
    ('Rett inn øyra på kvar lås', 'Set ein 05 i kvart av dei fire hola i baklokket.'),
    ('Drei kvar lås 90°', 'Bruk verktøy 06 og same retning som i låseprøva. Stopp ved enden av kanalen.'),
    ('Prøv lokket forsiktig', 'Lokket skal halde utan glippe eller rasling. Prøv også opplåsing før du avsluttar bygginga.'),
], 'Alle fire låsar held lokket og kan løysast att utan å skade plasten.',
     parts='05 ×4 + 06 ×1', power='USB FRÅ')

page('24', 'Ta foto med det samla kameraet', 'SLUTTPRØVE / REELL FUNKSJON', 'm12-finished.png', [
    ('Start kameraet som i steg 07', 'USB til MB, Wi-Fi A1-Camera og nettlesar på 192.168.4.1.'),
    ('Prøv heile produktet', 'Ta ti separate foto med utløysaren. Kontroller full retur, stabil innmat og fri biletkant med frontringen på.'),
    ('Opne og kontroller etter prøva', 'Kople frå USB. Sjå etter kontaktmerke, klemde kablar, laus innfesting og unormal varme under drift.'),
], 'Noter dato, kortmodell, brytarmål, filament og resultat. Først fysisk test kan stadfeste monteringa.',
     power='USB PÅ FOR TEST',
     note='Denne guiden leverer benktest og prototypebygging. Batteridrift, USB-C-lading, varig fotolagring og endeleg produksjonsfrigjeving står att.')

page('?', 'Finn feilen før du byggjer vidare', 'FEILSØKING / EITT PROBLEM OM GONGEN', 'ui-trouble', [
    ('Ingen port eller opplasting', 'Kontroller datakabel, portval og rett USB-UART-drivar. Prøv bootrekkjefølgja i steg 06.'),
    ('Ingen foto eller utløysing', 'Les Serial Monitor. Kontroller kamera/FPC utan straum. Test GPIO13/GND-paret og A1-skissa før du endrar mekanikken.'),
    ('Knappen heng eller delen passar ikkje', 'Opne huset og isoler steget: 07 åleine, så 08, så innmat. Mål avviket og tilpass CAD; ikkje bruk meir kraft.'),
], 'Gå tilbake til siste steg som fungerte. Rett feilen der før du monterer resten.',
     note='A1-programmet og manualen er nye. Sjå verification/firmware-r02.json for faktisk kompilering og programkontroll; ingen fysisk test er påstått.')

PAGES_TOTAL = len(pages) + 1
C = canvas.Canvas(str(PATH), pagesize=(W, H), pageCompression=1)
C.setTitle('A1 - Byggjesteg R02: Arduino IDE, ESP32-CAM og mekanisk montering')
C.setAuthor('FormNerd / Iver Raknes Finne')
layout = []


def para(value, x, top, width, kind='body'):
    p = Paragraph(value, styles[kind])
    _, height = p.wrap(width, 700)
    p.drawOn(C, x, top - height)
    return top - height


def rect(x, y, w, h, fill=LIGHT, radius=8, stroke=False):
    C.setFillColor(fill)
    C.setStrokeColor(INK)
    C.roundRect(x, y, w, h, radius, fill=1, stroke=int(stroke))


def arrow(x1, y1, x2, y2):
    import math
    C.setStrokeColor(ACCENT)
    C.setFillColor(ACCENT)
    C.setLineWidth(3)
    C.line(x1, y1, x2, y2)
    a = math.atan2(y2-y1, x2-x1)
    p = C.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2-12*math.cos(a-0.4), y2-12*math.sin(a-0.4))
    p.lineTo(x2-12*math.cos(a+0.4), y2-12*math.sin(a+0.4))
    p.close()
    C.drawPath(p, fill=1, stroke=0)


def label(value, x, y, size=13, bold=False, color=INK):
    C.setFillColor(color)
    C.setFont('GuideBold' if bold else 'Guide', size)
    C.drawString(x, y, value)


def screen(title):
    rect(52, 160, 487, 300, colors.white, 10, True)
    rect(53, 423, 485, 36, LIGHT, 9)
    label(title, 69, 436, 13, True)
    C.setStrokeColor(INK)
    C.setLineWidth(1.2)
    C.line(245, 160, 230, 135)
    C.line(345, 160, 360, 135)
    C.line(210, 135, 380, 135)


def card(number, title, detail, top, h=66):
    rect(70, top-h, 450, h, LIGHT, 7)
    label(str(number), 84, top-25, 19, True, ACCENT)
    label(title, 113, top-24, 13, True)
    para(detail, 113, top-32, 390, 'small')


def ui(kind):
    if kind == 'ui-install':
        screen('Arduino IDE / Boards Manager')
        card(1, 'Preferences / Settings', 'Additional Boards Manager URLs', 412, 55)
        label('https://espressif.github.io/arduino-esp32/', 78, 335, 10)
        label('package_esp32_index.json', 78, 318, 10, True)
        C.linkURL('https://espressif.github.io/arduino-esp32/package_esp32_index.json', (70,308,520,350), relative=0)
        card(2, 'Boards Manager', 'Søk: esp32', 300, 55)
        card(3, 'esp32 by Espressif Systems', 'Install / noter pakkeversjonen', 234, 55)
    elif kind == 'ui-board':
        screen('Arduino IDE / A1_Bench_Camera')
        card(1, 'File > Open', 'A1_Bench_Camera.ino', 412)
        card(2, 'Tools > Board', 'AI Thinker ESP32-CAM', 335)
        card(3, 'Tools > Port', 'Serieporten som kom til i steg 03', 258)
    elif kind == 'ui-upload':
        screen('Arduino IDE / Verify > Upload')
        card(1, 'Verify > Upload', 'La opplastinga bli ferdig.', 412, 57)
        card(2, 'Ved fast Connecting ...', 'Hald IO0/BOOT > trykk/slepp RST > Upload', 344, 65)
        card(3, 'Slepp IO0 > RST', 'Serial Monitor: 115200 baud', 268, 65)
    elif kind == 'ui-photo':
        rect(130, 132, 285, 345, colors.white, 24, True)
        rect(143, 156, 259, 294, LIGHT, 5)
        label('Wi-Fi: A1-Camera', 161, 418, 13, True)
        label('A1camera2026', 161, 395, 12)
        rect(154, 342, 237, 33, colors.white, 4)
        label('http://192.168.4.1/', 166, 354, 12, True)
        rect(161, 275, 221, 42, INK, 5)
        label('Ta bilete', 227, 290, 14, True, colors.white)
        C.setStrokeColor(GREY)
        C.rect(161, 189, 221, 65, fill=0, stroke=1)
        label('Ditt faktiske kamerabilete', 174, 218, 10)
        label('Last ned siste JPEG', 189, 170, 11, True)
        label('Skjematisk skjermvising', 172, 113, 9, False, GREY)
    elif kind == 'ui-trouble':
        screen('Kontroller siste fungerande steg')
        card('A', 'PC / port / opplasting', 'Steg 03-06', 412)
        card('B', 'Kamera / foto / knapp', 'Steg 07-11', 335)
        card('C', 'Føring / passform / retur', 'Steg 12-24', 258)


def draw_image(name):
    path = FIG / name
    if not path.is_file():
        raise FileNotFoundError(path)
    im = Image.open(path).convert('RGB')
    import numpy as np
    a = np.asarray(im)
    isolated_camera = name == 'm04-camera.png'
    if isolated_camera:
        a = a[:-180]
    mask = np.any(a < 240, axis=2)
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise ValueError('Empty figure: '+name)
    box = (max(0,int(xs.min())-35), max(0,int(ys.min())-35), min(im.width,int(xs.max())+36), min(im.height,int(ys.max())+36))
    cropped = im.crop(box)
    from reportlab.lib.utils import ImageReader
    C.drawImage(ImageReader(cropped), 28, 170 if isolated_camera else 139, width=535, height=311 if isolated_camera else 342, preserveAspectRatio=True, anchor='c')
    if isolated_camera:
        label('UTSNITT AV 03 / KAMERA OG FLEKS ER NOMINELLE', 40, 148, 8, True)
    return {'path':str(path.relative_to(ROOT)), 'source_pixels':list(im.size), 'crop_px':list(box), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def footer(n):
    C.setStrokeColor(colors.HexColor('#ccd0d1'))
    C.setLineWidth(0.5)
    C.line(28, 34, W-28, 34)
    label('FORMNERD / A1 / BYGGJESTEG R02 / 20.10.2026', 28, 20, 7.3, color=GREY)
    C.setFont('Guide', 8)
    C.drawRightString(W-28, 20, f'{n:02d} / {PAGES_TOTAL:02d}')
    C.showPage()


for n, p in enumerate(pages, 1):
    C.bookmarkPage('page'+str(n))
    C.addOutlineEntry(p['number']+' '+p['title'], 'page'+str(n), 0, False)
    label(p['number'], 28, H-63, 35, True)
    title_size = 22
    while pdfmetrics.stringWidth(p['title'],'GuideBold',title_size) > W-154:
        title_size -= 0.5
    label(p['title'], 105, H-53, title_size, True)
    label(p['phase'], 106, H-74, 8, True, GREY)
    C.setStrokeColor(INK)
    C.setLineWidth(1)
    C.line(28,H-91,W-28,H-91)
    if p['figure'].startswith('ui-'):
        ui(p['figure'])
        figmeta = {'vector_diagram':p['figure']}
    else:
        figmeta = draw_image(p['figure'])
    if p['parts']:
        para(p['parts'], 35, 128, 520, 'small')
    right_x = 588
    y = 478
    if p['power']:
        rect(right_x, y-23, 223, 23, LIGHT, 4)
        label(p['power'],right_x+9,y-16,8.5,True)
        y -= 39
    bottoms = []
    for k, (title, body) in enumerate(p['actions'],1):
        C.setFillColor(INK)
        C.circle(right_x+7,y-9,7,fill=1,stroke=0)
        C.setFillColor(colors.white)
        C.setFont('GuideBold',7)
        C.drawCentredString(right_x+7,y-11.5,str(k))
        y = para(escape(title),right_x+22,y,201,'action') - 6
        y = para(escape(body),right_x+22,y,201) - 21
        bottoms.append(y)
    if min(bottoms)<140:
        raise ValueError('Action overflow on '+p['title']+': '+str(bottoms))
    if p['note']:
        note_bottom = para(escape(p['note']),35,108,520,'small')
        if note_bottom<62:
            raise ValueError('Note overflow '+p['title'])
    rect(580,57,234,84,LIGHT,6)
    label('KONTROLL FØR NESTE STEG',590,124,8,True,ACCENT)
    check_bottom = para(escape(p['checkpoint']),590,115,214,'check')
    if check_bottom<62:
        raise ValueError('Checkpoint overflow '+p['title'])
    layout.append({'page':n,'step':p['number'],'title':p['title'],'figure':figmeta,'actions_bottom':min(bottoms),'checkpoint_bottom':check_bottom})
    footer(n)

label('i',28,H-63,35,True)
label('Grunnlag, status og kjelder',105,H-53,22,True)
label('LES DETTE SOM EIN BYGGJEGUIDE FOR PROTOTYPEN',106,H-74,8,True,GREY)
C.setStrokeColor(INK)
C.line(28,H-91,W-28,H-91)
y=476
y=para('Kva som er teikna og prøvd',35,y,350,'action')-9
y=para('Mekanikkteikningane brukar dei faktiske delane i A1-assembly R01. CAD-geometrien er ikkje endra for denne manualen. Elektronikkteikningane er skjematiske og viser ikkje målte kort, flekslengder eller pinnestillingar.',35,y,350)-18
y=para('Programmet som følgjer med',35,y,350,'action')-9
y=para('A1_Bench_Camera er kompilert med Arduino-ESP32 3.3.12 og AI Thinker-profil utan åtvaringar. Ti simulerte logikkprøver og fire nettlesarprøver bestod. Ho brukar GPIO13, eige Wi-Fi og eitt siste JPEG i RAM. Dette er ei benktestskisse; fysisk kamera, nettverk og utløysar er ikkje testa.',35,y,350)-18
y=para('Kva som må prøvast fysisk',35,y,350,'action')-9
y=para('Kort og pluggplass, fleksføring, 09 si fasthalding, brytarhøgd, full retur, printtoleransar, synsfelt og varme. Ingen fysisk montering eller kameratest er påstått utført av denne leveransen.',35,y,350)-18
sources=[
    ('S1','ESP32 i Arduino IDE','https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html'),
    ('S2','ESP32: oppstartsmodus','https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html'),
    ('S3','GPIO og INPUT_PULLUP','https://docs.espressif.com/projects/arduino-esp32/en/latest/api/gpio.html'),
    ('S4','SD_MMC og GPIO13','https://docs.espressif.com/projects/arduino-esp32/en/latest/api/sdmmc.html'),
    ('S5','AI Thinker kamerakart','https://github.com/espressif/arduino-esp32/blob/master/libraries/ESP32/examples/Camera/CameraWebServer/camera_pins.h'),
    ('S6','ESP32-CAM-MB-skjema','https://www.olimex.com/Products/IoT/ESP32/ESP32-CAM/resources/ESP32-CAM-MB-S001.jpg'),
    ('S7','Arduino IDE','https://www.arduino.cc/en/software'),
]
y=476
y=para('Primærkjelder',430,y,375,'action')-14
for ident,title,url in sources:
    y=para(f'<b>{ident}</b>  <link href="{escape(url)}" color="#17191a"><u>{escape(title)}</u></link>',430,y,375,'body')-10
y-=4
y=para('Prosjektgrunnlag',430,y,375,'action')-10
y=para('Utstyret-me-har(1).pdf, 20.10.2026: startsettet er ikkje kartlagt; to CAM/MB-sett var planlagde henta, mottak ikkje stadfesta. A1-assembly R01: bill-of-materials.json, CAD-kjelder og kontrollrapportar. ESP32-CAM V1.0-datablad: berre CAM-kortet har nominelt mål 27 × 40,5 × 4,5 mm.',430,y,375,'small')-18
y=para('Trykt rettleiing: følg stega i rekkjefølgje. PDF: innhaldspanelet har bokmerke for kvart steg, og kjeldenamna ovanfor er klikkbare.',430,y,375,'small')
footer(PAGES_TOTAL)
C.save()
report={'revision':'A1-Byggjesteg-R02','pages':PAGES_TOTAL,'pdf':str(PATH.relative_to(ROOT)),
        'pdf_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),'layout':layout,
        'mechanical_geometry_changed':False,'electronics_drawings_are_schematic':True,
        'physical_build_verified':False,'hardware_test_performed':False,
        'primary_sources':[{'id':i,'title':t,'url':u} for i,t,u in sources]}
(ROOT/'verification/guide-r02.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pdf':str(PATH),'pages':PAGES_TOTAL,'bytes':PATH.stat().st_size},ensure_ascii=False))
