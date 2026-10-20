import importlib.util
import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'review'
spec = importlib.util.spec_from_file_location('a1_export', ROOT / 'cad/export_review.py')
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)
parts = export.load_parts()
by_name = {part['name']: part for part in parts}
views = {}
views['A1-exploded-lines.png'] = export.render([part for part in parts if export.part_role(part['name']) == 'product_part'], 'A1-exploded-lines.png', exploded=True, technical=True)
for name, selected in [('A1-carrier-detail.png', ['03_esp32_carrier', '09_camera_keeper']), ('A1-shutter-detail.png', ['07_shutter', '08_shutter_retainer'])]:
    views[name] = export.render([by_name[key] for key in selected], name, exploded=True, technical=True)
(ROOT / 'verification/manual-renders.json').write_text(json.dumps(views, indent=2) + '\n')

pdfmetrics.registerFont(TTFont('D', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
W, H = landscape(A4)
C = canvas.Canvas(str(REVIEW / 'A1-Montering-R01.pdf'), pagesize=(W, H))
C.setTitle('A1 - Mekanisk assembly R01 og monteringssteg')
C.setAuthor('FormNerd / Iver Raknes Finne')
BODY = ParagraphStyle('body', fontName='D', fontSize=10, leading=15)
SMALL = ParagraphStyle('small', parent=BODY, fontSize=8, leading=11)
BIG = ParagraphStyle('big', parent=BODY, fontName='DB', fontSize=13, leading=17)


def text(value, x, y, width, style=BODY):
    p = Paragraph(value, style)
    _, height = p.wrap(width, H)
    p.drawOn(C, x, y - height)
    return y - height


def header(number, title, sub):
    C.setFillColor(colors.black)
    C.setFont('DB', 30)
    C.drawString(32, H - 54, number)
    C.setFont('DB', 21)
    C.drawString(110, H - 52, title)
    C.setFont('D', 8.5)
    C.drawString(110, H - 73, sub)
    C.setLineWidth(1)
    C.line(32, H - 91, W - 32, H - 91)


def image(name, x=20, y=93, width=510, height=392):
    C.drawImage(str(REVIEW / name), x, y, width=width, height=height, preserveAspectRatio=True, anchor='c', mask='auto')


def item(n, title, body, y, x=550, width=250):
    C.setFillColor(colors.black)
    C.circle(x + 9, y - 10, 9, fill=1, stroke=0)
    C.setFillColor(colors.white)
    C.setFont('DB', 8.5)
    C.drawCentredString(x + 9, y - 13, str(n))
    C.setFillColor(colors.black)
    y = text(title, x + 26, y, width - 26, BIG) - 8
    return text(body, x + 26, y, width - 26) - 23


def footer(page):
    C.setLineWidth(0.4)
    C.setStrokeColor(colors.HexColor('#999999'))
    C.line(32, 37, W - 32, 37)
    C.setFont('D', 7.5)
    C.drawString(32, 23, 'FORMNERD  /  A1-ASSEMBLY-R01  /  20.10.2026')
    C.drawRightString(W - 32, 23, f'{page} / 6')
    C.showPage()


header('A1', 'Mekanisk assembly R01', 'FAKTISKE MODELLDELAR. NOMINELL ESP32-CAM + MB. FYSISK PASSFORM ER IKKJE FRIGJEVEN.')
image('A1-assembled.png')
y = text('Dette er bygd i modellen', 550, 476, 250, BIG) - 12
y = text('01 Ytterskal<br/>02 Krummt baklokk<br/>03 CAM/MB-haldar og framført kamerasete<br/>04 Frontring med bajonett<br/>05 Fire kvartomdreiingslåsar<br/>07 Utløysar med native knappetopp<br/>08 Utløysarkassett<br/>09 Kameraklemme', 550, y, 250) - 18
y = text('11 plastdelar i produktet', 550, y, 250, BIG) - 8
text('I tillegg: 06 låseverktøy og test_lock_socket. Desse er separate test-/verktøydelar.', 550, y, 250)
text('Vald ytterbreidd: 140 mm. Ytterforma er maskinert direkte frå den detaljerte Tripo-meshen. Elektronikk er ikkje teikna inn som om ho var målt.', 48, 85, 470, SMALL)
footer(1)

header('01', 'Print og prøv låsen', 'MONTERINGSREKKJEFØLGJE FOR DEN NOMINELLE MEKANISKE PROTOTYPEN')
image('A1-exploded-lines.png')
y = item(1, 'Prøveprint først', 'Print test_lock_socket og éin 05-lås. Bruk det faktiske filamentet og den faktiske P1S-profilen.', 476)
y = item(2, 'Prøv innføring og dreiing', 'Før låsen inn med øyra i spora. Drei 90°. Han skal halde aksialt og kunne løysast att utan skade.', y)
y = item(3, 'Print delane kvar for seg', 'Bruk dei individuelle 3MF-filene eller platefilene. Samla assembly-3MF er for inspeksjon og skal ikkje printast som eitt massivt objekt.', y)
text('3MF bevarer float64-koordinatar med 17 signifikante siffer. Kontroller lag, støtte og første lag i Bambu Studio før maskinkode.', 48, 85, 470, SMALL)
footer(2)

header('02', 'Klargjer kamerahaldaren', '03 HALDAR  +  09 KLEMME. TEIKNINGA VISER DEI FAKTISKE PRINTDEL​ANE.'.replace('\u200b', ''))
image('A1-carrier-detail.png')
y = item(1, 'Mål det faktiske settet', 'Databladet gir CAM-kortet 27 × 40,5 × 4,5 mm. MB, kontaktstakk og kamerafleks er førebels dimensjonerte som nominell plass.', 476)
y = item(2, 'Tilpass kamerasetet', 'Ført fram til linseområdet, med klemme bak kameramodulen. Kontroller modulmål, flekslengd, orientering og at klemma faktisk held modulen.', y)
y = item(3, 'Set CAM/MB i haldaren', 'Den nominelle stakkplassen er 28 × 48 × 22 mm. Dette er eit førebels mål, ikkje ei stadfesting av dine komponentar.', y)
text('Kameralinsa er føresett framført til Y=28 mm i assembly-koordinatane. Ein 30 mm fri frontring er ikkje dokumentasjon på ei 30 mm optisk linse.', 48, 85, 470, SMALL)
footer(3)

header('03', 'Monter utløysaren', '07 UTLØYSAR  +  08 KASSETT. NOMINELL BRYTAR ER IKKJE STADFESTA EIGD.')
image('A1-shutter-detail.png')
y = item(1, 'Før knappen ned ovanfrå', 'Den printa knappen har stem og fangflens. Behald toppen som følgjer den valde forma.', 476)
y = item(2, 'Skyv kassetten inn bakfrå', 'Den opne gaffelen fangar flensen. Baklokket held kassetten i lengderetninga når huset er lukka.', y)
y = item(3, 'Kontroller brytar og retur', 'Det er modellert eit nominelt 6 × 6 mm brytarsete og 1,2 mm mekanisk slag. Faktisk brytarhøgd, overvandring og returkraft må avklarast.', y)
text('Denne rettleiinga stadfestar rigid geometri og monteringsveg. Elektrisk utløysing og fjør-/brytarretur er ikkje funksjonstesta.', 48, 85, 470, SMALL)
footer(4)

header('04', 'Set saman og lukk huset', 'BAKFRÅ: HALDAR OG KASSETT. FRAMFRÅ: BAJONETTRING. TIL SLUTT: LOKK OG LÅSAR.')
image('A1-exploded-lines.png')
y = item(1, 'Før inn haldaren', 'Set den ferdig kontrollerte kamerainnmaten inn frå baksida. Kontroller at fleks og leidningar går fritt gjennom dei modellerte vegane.', 476)
y = item(2, 'Lås frontringen', 'Før øyra inn i spora og drei 45°. Den frie opninga er 30 mm. Kontroller den faktiske synsvinkelen med kameraet på plass.', y)
y = item(3, 'Lukk baklokket', 'Før tunga inn i huset. Set inn fire låsar og drei kvar lås 90° med verktøy 06. Kontroller at lokket sit jamt og kan opnast att.', y)
text('Mellom skal og lokk: 0,30 mm modellert fuge. Glidesete: 0,30 mm nominell klaring per side. Fysisk toleranse må stadfestast med prøveprint.', 48, 85, 470, SMALL)
footer(5)

header('05', 'Kontroll før sluttprint', 'DIGITALE RESULTAT OG DET SOM STÅR ATT')
report = json.loads((ROOT / 'verification/assembly-independent.json').read_text())
y = 474
left = [
    ('Bestått', 'Alle leverte printdelar er lukka, har positivt volum og éin samanhengande komponent.'),
    ('Bestått', f"{len(report['static_pairs'])} delpar kontrollerte: ingen volumkollisjonar over 0,01 mm³."),
    ('Bestått', f"{len(report['motions'])} rørsleforløp prøvde: lokk, haldar, bajonett, fire låsar, utløysarslag og kassett."),
    ('Bestått', 'Separate 3MF-filer bevarer koordinatar og indeksar ved innlesing. STEP-delar er lesne inn att og kontrollerte.'),
]
for title, detail in left:
    y = text(title, 48, y, 335, BIG) - 5
    y = text(detail, 48, y, 335) - 22
y = text('Må avklarast før fysisk frigjeving', 440, 474, 355, BIG) - 12
y = text('1. Eksakt CAM/MB-variant, samla mål, kontaktplassering og kamerafleks.<br/>2. Faktisk brytar, elektrisk kopling, slag og retur.<br/>3. Straumforsyning. MB-porten er normalt Micro-USB for straum/programmering. USB-C-lading og USB-biletoverføring er ikkje løyste av CAD-en.<br/>4. Fysisk prøveprint, passform, optikk og varme under drift.<br/>5. Prosjektkravet om minst 30 mm linse må vurderast mot faktisk optikk.', 440, y, 355)
text('Format: samla mekanisk assembly i 3MF/GLB. Dei analytiske mekanikkdelane finst i STEP. Dei detaljerte ytterdelane og den native knappetoppen er mesh, ikkje nøyaktige NURBS-/BRep-skal i STEP.', 48, 163, 747, SMALL)
text('Grunnlag: vald Tripo-mesh; Utstyret-me-har(1).pdf (20.10.2026); FormNerd - Prosjektoversikt.pdf, s. 2; Ai-Thinker ESP32-CAM Module V1.0, s. 1-2; Olimex ESP32-CAM-MB-skjema. Rapportar og kontrollsummar følgjer i verification/. Monteringsrørslene er kontrollerte i diskrete posisjonar; fysisk montering er ikkje utført.', 48, 95, 747, SMALL)
footer(6)
C.save()
print(REVIEW / 'A1-Montering-R01.pdf')
