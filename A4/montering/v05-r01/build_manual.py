import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
CAD = ROOT / 'Entropi-CAD-v05'
sys.path.insert(0, str(CAD / 'cad'))
import render_preview as preview

NAMES = {
    '01': 'Ribbebur', '02': 'Chassis', '03': 'Baklokk', '04': 'Korthaldar',
    '05': 'Kortklemme', '06': 'Frontblende', '07': 'Utløysarknapp', '08': 'Sikringspinne',
    '09': 'Øvre hjul', '10': 'I/O-plate', '11': 'Passingskupong', '12': 'Valfri formplugg',
    '13': 'Pluggskive', '14': 'Hjulskive', '15': 'Returfjør', '16': 'Knappetest',
    '17': 'Kameravugge', '18': 'Kameraklemme', '19': 'USB-klemme', '20': 'Serviceplate'
}
FRONT = (-220, -340, 230)
BACK = (-190, 340, 210)
SHUTTER = (-240, 280, 220)


def part(number, offset=(0, 0, 0)):
    return {'id': number, 'offset': list(offset)}


STEPS = [
    {'title': 'Start med delane', 'kind': 'intro', 'eye': FRONT,
     'parts': [part(x) for x in NAMES if x not in ('11', '16')],
     'text': 'Dette er ei mekanisk rettleiing for CAD v05. Alle bileta kjem frå dei faktiske STL-delane.',
     'check': 'Ikkje prent hovuddelane før kupongane er prøvde. Elektronikkmål, faktisk passform og verktøytilkomst er ikkje stadfesta.'},
    {'title': 'Delnummer og skruar', 'kind': 'inventory'},
    {'title': 'Prøv passingane først', 'parts': [part('11', (-20, 0, 0)), part('16', (35, 0, 0))],
     'new': ['11', '16'], 'eye': FRONT, 'motion_ids': [],
     'text': 'Prent 11 og 16 med same filament, dyse og laghøgd som hovuddelane. Prøv M2-hola, PCB-spora, pinnen og fjørprøva.',
     'check': 'Pinnen skal kunne førast inn utan å sprekke holveggen. Kalibrer passinga før vidare utskrift.'},
    {'title': 'Før inn returfjøra', 'parts': [part('01'), part('15', (0, 24, 0))], 'new': ['15'],
     'eye': SHUTTER, 'detail': True, 'cutaway': True,
     'text': 'Før fjør 15 inn bakfrå mot setet i grep 01. Foten skal gå inn i sporet; bladet ligg under knappen.',
     'check': 'Ein eventuell brytar må målast og prøvast i vugga først. Den modellerte brytaren på 6 × 6 mm er ein føresetnad.'},
    {'title': 'Knapp og sikringspinne', 'parts': [part('01'), part('15'), part('07', (0, 0, 16)), part('08', (0, 30, 0))],
     'new': ['07', '08'], 'eye': SHUTTER, 'detail': True, 'cutaway': True,
     'text': 'Før knapp 07 ned ovanfrå. Før pinne 08 inn bakfrå gjennom knappen, med uttrekksfliken vend bakover.',
     'check': 'Prøv 1 mm slag, retur og begge endestoppa. Ikkje tving pinnen eller fjøra.'},
    {'title': 'Lukk serviceluka', 'parts': [part('01'), part('15'), part('07'), part('08'), part('20', (0, 22, 0))],
     'new': ['20'], 'eye': SHUTTER, 'detail': True,
     'screws': '1 × M2 × 6',
     'text': 'Legg serviceplate 20 inn bakfrå etter at knappen er prøvd. Fest med éin skrue.',
     'check': 'Plata skal kunne takast av att for tilgang til pinne, brytar og fjør.'},
    {'title': 'Fest bur til chassis', 'parts': [part('01', (0, -35, 0)), part('02')], 'new': ['01'], 'eye': BACK,
     'screws': '4 × M2 × 10',
     'text': 'Før bur 01 og chassis 02 saman. Skru frå innsida gjennom chassis og inn i dei fire festa på buret.',
     'check': 'Gjer dette før korthaldaren kjem inn. Baklokket og elektronikken skal vere ute.'},
    {'title': 'Bygg kameravugga ute', 'parts': [part('06'), part('17', (0, 0, 18))], 'new': ['17'], 'eye': BACK,
     'screws': '2 × M2 × 6',
     'text': 'Monter vugge 17 på dei to skinnene i blende 06 utanfor huset. Spora gjev aksial justering.',
     'check': 'Mål den faktiske kamerahylsa. Vugga er nominelt laga for Ø8 mm; dette er ikkje ei stadfesting av kameramodulen din.'},
    {'title': 'Legg på kameraklemma', 'parts': [part('06'), part('17'), part('18', (0, 0, 20))], 'new': ['18'], 'eye': BACK,
     'screws': '2 × M2 × 8',
     'text': 'Legg den målte kamerahylsa i vugga og før klemme 18 ned. Juster og stram jamt utan å klemme flekskabelen.',
     'check': 'Elektronikken er ikkje teikna inn her. Utstyrslista oppgir ingen mål eller kontrollert kabelrekkjevidd.'},
    {'title': 'Før inn optikkgruppa', 'parts': [part('01'), part('02'), part('06', (0, -55, 0)), part('17', (0, -55, 0)), part('18', (0, -55, 0))],
     'new': ['06', '17', '18'], 'eye': FRONT, 'screws': '2 × M2 × 8',
     'motion_ids': ['06'], 'label_offsets': {'06': [-26, -23], '17': [-8, 24], '18': [24, 10]},
     'text': 'Før heile gruppa inn gjennom fronten. Fest blenda bakfrå i dei to øyra i kragen.',
     'check': 'Før flekskabelen fritt bakover. Kontroller at den verkelege kabelen rekk fram utan skarp bøying.'},
    {'title': 'Valfri rein formmodell', 'parts': [part('06'), part('12', (0, -28, 0)), part('13', (0, 20, 0))],
     'new': ['12', '13'], 'eye': FRONT, 'screws': '1 × M2 × 4', 'optional': True,
     'text': 'For ein rein formmodell: før plugg 12 inn framfrå og fest skive 13 bak blenda. Dette er ei eiga grein av monteringa.',
     'check': 'Plugg 12 er ikkje optikk. Del 12 og 13 skal vere ute ved bruk av faktisk kamera.'},
    {'title': 'Monter det øvre hjulet', 'parts': [part('02'), part('09', (0, 0, 24)), part('14', (0, 0, -24))],
     'new': ['09', '14'], 'eye': BACK, 'screws': '1 × M2 × 6',
     'text': 'Før hjul 09 ned gjennom toppen. Før skive 14 opp frå innsida og fest henne på akslingen.',
     'check': 'Hjulet er ein mekanisk formdetalj. Prøv verktøytilkomst før vidare montering; lang skrutrekkjar er ikkje verifisert.'},
    {'title': 'Fest den tomme I/O-plata', 'parts': [part('02'), part('10', (0, 60, 0))], 'new': ['10'], 'eye': BACK,
     'screws': '2 × M2 × 6',
     'text': 'Før tom plate 10 inn gjennom bakopninga og skru henne til sidefesta. Kort og klemme 19 skal enno vere ute.',
     'check': 'Denne rekkjefølgja held skruehola frie. Innføringa og verktøytilkomsten må prøvast fysisk.'},
    {'title': 'USB-feste er førebels', 'parts': [part('10'), part('19', (0, 0, 18))], 'new': ['19'], 'eye': BACK,
     'screws': '2 × M2 × 6', 'optional': True,
     'text': 'Vugga er dimensjonert for eit separat kort på 14 × 16 × 1,6 mm. Utstyrslista stadfestar ikkje eit slikt kort.',
     'check': 'Ikkje rekna dette som ein kontrollert USB-C-adapter for ESP32-CAM-MB. Mål port, plugg, kort og kabel før del 19 blir brukt.'},
    {'title': 'Bygg korthaldaren ute', 'parts': [part('04'), part('05', (0, 0, 25))], 'new': ['05'], 'eye': BACK,
     'screws': '2 × M2 × 6',
     'text': 'Før det målte ESP32-kortet inn i spora på haldar 04. Legg toppklemme 05 på og fest henne utanfor huset.',
     'check': 'Det nominelle kortmålet er 27 × 40,5 mm. Komponenthøgd, MB-volum og kontaktplassering må samanliknast med dei faktiske delane.'},
    {'title': 'Før inn korthaldaren', 'parts': [part('01'), part('02'), part('06'), part('17'), part('18'), part('09'), part('14'), part('10'), part('04', (0, 75, 0)), part('05', (0, 75, 0))],
     'new': ['04', '05'], 'eye': BACK, 'screws': '4 × M2 × 10',
     'motion_ids': ['04'], 'label_offsets': {'04': [-20, -18], '05': [18, 18]},
     'text': 'Før haldargruppa inn bakfrå og skru henne til dei fire stolpane. Hald kablar utanfor skruebanane.',
     'check': 'Prøv først at faktisk kort og MB-programmerar kan koplast frå og takast ut gjennom bakopninga.'},
    {'title': 'Prøv før du lukkar', 'parts': [part(x) for x in NAMES if x not in ('03', '11', '12', '13', '16', '19')],
     'eye': BACK,
     'text': 'Prøv knappen, kontakten, kabelslakken og elektronikken medan baksida er open. Sjekk at ingen komponent ligg mot skruetuppane.',
     'check': 'Denne rettleiinga dokumenterer mekanisk rekkjefølgje. Ho stadfestar ikkje kopling frå Arduino til ESP32, straumforsyning eller fungerande biletoverføring.'},
    {'title': 'Baklokket kjem sist', 'parts': [part(x) for x in NAMES if x not in ('03', '11', '12', '13', '16', '19')] + [part('03', (0, 60, 0))],
     'new': ['03'], 'eye': BACK, 'screws': '4 × M2 × 8',
     'text': 'Legg kablane fritt innanfor kanten. Før baklokk 03 inn framover og fest dei fire skruane jamt.',
     'check': 'Stopp dersom lokket pressar på kabel, kort eller kontakt. Ikkje bruk skruane til å tvinge delane saman.'},
    {'title': 'Kva som faktisk er kontrollert', 'kind': 'status', 'eye': FRONT,
     'parts': [part(x) for x in NAMES if x not in ('11', '12', '13', '16', '19')],
     'text': 'Geometrirapportane kontrollerer native solid, lukka nett, kollisjon, fem uttaksbaner, nominelt knappeslag og forenkla skruevolum.',
     'check': 'Fysisk maskinvarepassing, gjengestyrke, vanleg verktøytilkomst, fjørlevetid, optikk og elektronikkfunksjon er ikkje verifiserte.'}
]


def flat_colors(normals, base, view, right, vertical):
    return np.tile(np.array(base[:3]), (len(normals), 1))


def outlined_raster():
    code = preview.RASTER.replace('float factor=1-std::clamp(0.8f*occlusion/36,0.0f,0.28f);', 'float factor=1.0f;')
    outline = r'''
    std::vector<uint8_t> lined = pixels;
    for (uint32_t y=1; y<h-1; ++y) {
      for (uint32_t x=1; x<w-1; ++x) {
        size_t i=size_t(y)*w+x;
        if (!std::isfinite(depth[i])) continue;
        bool edge=false;
        for (int dy=-1; dy<=1; ++dy) {
          for (int dx=-1; dx<=1; ++dx) {
            if (!dx && !dy) continue;
            size_t j=size_t(int(y)+dy)*w+int(x)+dx;
            if (!std::isfinite(depth[j]) || std::abs(depth[i]-depth[j])>1.0f) edge=true;
            float dot=0, ai=0, aj=0;
            for (int k=0;k<3;++k) { dot+=normals[i*3+k]*normals[j*3+k]; ai+=normals[i*3+k]*normals[i*3+k]; aj+=normals[j*3+k]*normals[j*3+k]; }
            if (ai>0 && aj>0 && dot/std::sqrt(ai*aj)<0.75f) edge=true;
          }
        }
        if (edge) for(int k=0;k<3;++k) lined[i*3+k]=pixels[i*3]<235 ? 25 : 115;
      }
    }
    pixels.swap(lined);
'''
    return code.replace('    std::ofstream out(argv[2], std::ios::binary);', outline + '\n    std::ofstream out(argv[2], std::ios::binary);')


def select_mesh(mesh, detail=False, cutaway=False):
    points, faces, normals = mesh
    if not detail:
        return points.copy(), faces.copy(), normals.copy()
    vertices = vtk.vtkPoints()
    vertices.SetData(numpy_to_vtk(points, deep=True))
    cells = vtk.vtkCellArray()
    packed = np.column_stack((np.full(len(faces), 3), faces)).astype(np.int64)
    cells.SetCells(len(faces), numpy_to_vtkIdTypeArray(packed.ravel(), deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(vertices)
    poly.SetPolys(cells)
    clean = vtk.vtkCleanPolyData()
    clean.SetInputData(poly)
    planes = vtk.vtkPlaneCollection()
    bounds = ((-68 if cutaway else -82, -54), (-15, 28), (69, 93))
    for axis, pair in enumerate(bounds):
        for edge, sign in zip(pair, (1, -1)):
            plane = vtk.vtkPlane()
            origin, normal = np.zeros(3), np.zeros(3)
            origin[axis], normal[axis] = edge, sign
            plane.SetOrigin(*origin)
            plane.SetNormal(*normal)
            planes.AddItem(plane)
    clip = vtk.vtkClipClosedSurface()
    clip.SetInputConnection(clean.GetOutputPort())
    clip.SetClippingPlanes(planes)
    clip.GenerateFacesOn()
    clip.TriangulationErrorDisplayOn()
    triangles = vtk.vtkTriangleFilter()
    triangles.SetInputConnection(clip.GetOutputPort())
    vectors = vtk.vtkPolyDataNormals()
    vectors.SetInputConnection(triangles.GetOutputPort())
    vectors.SetFeatureAngle(48)
    vectors.SplittingOn()
    vectors.ConsistencyOn()
    vectors.AutoOrientNormalsOn()
    vectors.Update()
    clipped = vectors.GetOutput()
    result_points = vtk_to_numpy(clipped.GetPoints().GetData()).astype(float)
    result_faces = vtk_to_numpy(clipped.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
    result_normals = vtk_to_numpy(clipped.GetPointData().GetNormals()).astype(float)
    return result_points, result_faces, result_normals


def render_step(step, meshes, number, raster, work, reuse=False):
    width, height = 1400, 1000
    objects = []
    new = step.get('new', [])
    for item in step['parts']:
        number_id = item['id']
        mesh = select_mesh(meshes[number_id], step.get('detail', False) and number_id == '01', step.get('cutaway', False) and number_id == '01')
        objects.append({'mesh': mesh, 'explode': item['offset'], 'color': [.83] * 3 if number_id in new else [.98] * 3})
    eye = step.get('eye', FRONT)
    target = (-68, 5, 80) if step.get('detail') else (0, 0, 45)
    forward = preview.unit(np.array(target) - np.array(eye))
    right = preview.unit(np.cross(forward, (0, 0, 1)))
    vertical = preview.unit(np.cross(right, forward))
    projected = np.concatenate([np.column_stack(((p['mesh'][0] + p['explode']) @ right, (p['mesh'][0] + p['explode']) @ vertical)) for p in objects])
    low, high = projected.min(0), projected.max(0)
    center = (low + high) / 2
    scale = min(width * .85 / (high[0] - low[0]), height * .85 / (high[1] - low[1]))
    def project(point):
        return ((np.array([point @ right, point @ vertical]) - center) * scale + np.array([width / 2, height / 2])).tolist()
    arrows = []
    for item in step['parts']:
        if item['id'] not in new:
            continue
        mesh = meshes[item['id']]
        anchor = (mesh[0].min(0) + mesh[0].max(0)) / 2
        offset = np.array(item['offset'])
        arrows.append({'id': item['id'], 'from': project(anchor + offset), 'to': project(anchor), 'moving': bool(np.linalg.norm(offset) > 0)})
    path = OUT / 'figures' / f'{number:02d}.png'
    if reuse and path.exists():
        with Image.open(path) as image:
            image.verify()
    else:
        preview.render(objects, eye, target, path, raster, work, width * 2, height * 2, exploded=True)
    return {'file': str(path.relative_to(OUT)), 'width': width, 'height': height, 'arrows': arrows}


def wrap(text, font, size, width):
    lines, line = [], ''
    for word in text.split():
        candidate = (line + ' ' + word).strip()
        if pdfmetrics.stringWidth(candidate, font, size) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def paragraph(c, text, x, y, width, size=11.5, leading=17, color=colors.black):
    c.setFillColor(color)
    c.setFont('Text', size)
    for line in wrap(text, 'Text', size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def arrow(c, start, end):
    a, b = np.array(start), np.array(end)
    vector = b - a
    length = np.linalg.norm(vector)
    if length < 12:
        return
    direction = vector / length
    side = np.array([-direction[1], direction[0]])
    a += direction * min(12, length * .18)
    b -= direction * min(12, length * .18)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.5)
    c.line(*a, *b)
    p = c.beginPath()
    p.moveTo(*b)
    p.lineTo(*(b - direction * 8 + side * 3.8))
    p.lineTo(*(b - direction * 8 - side * 3.8))
    p.close()
    c.setFillColor(colors.black)
    c.drawPath(p, fill=1, stroke=0)


def inventory(c):
    y = 704
    c.setFont('Strong', 11)
    c.drawString(44, y, 'NR.')
    c.drawString(92, y, 'PRENTA DEL')
    c.drawString(362, y, 'BRUK')
    y -= 14
    for number, name in NAMES.items():
        c.setStrokeColor(colors.HexColor('#DADADA'))
        c.line(44, y, 550, y)
        y -= 19
        c.setFont('Strong', 11)
        c.drawString(44, y, number)
        c.setFont('Text', 11)
        c.drawString(92, y, name)
        role = 'Test først' if number in ('11', '16') else 'Valfri formmodell' if number in ('12', '13') else 'Førebels USB-grensesnitt' if number == '19' else 'Samanstilling'
        c.setFont('Text', 9)
        c.drawString(362, y, role)
        y -= 8
    y -= 17
    c.setFont('Strong', 12)
    c.drawString(44, y, 'SKRUAR I DEN NOMINELLE MODELLEN')
    paragraph(c, 'M2 × 4: 1 stk     M2 × 6: 10 stk     M2 × 8: 8 stk     M2 × 10: 8 stk', 44, y - 24, 506, 10.5)
    paragraph(c, '27 totalt med formplugg. Kameravarianten utan 12 og 13 brukar 26. Faktiske skruar, hovudmål, verktøy og passing i plast må prøvast.', 44, y - 49, 506, 10.5)


def build_pdf(figures):
    font = Path('/usr/share/fonts/truetype/dejavu')
    pdfmetrics.registerFont(TTFont('Text', str(font / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('Strong', str(font / 'DejaVuSans-Bold.ttf')))
    target = OUT / 'Entropi-v05-Montering-R01.pdf'
    c = canvas.Canvas(str(target), pagesize=A4, pageCompression=1)
    c.setTitle('Entropi v05 - stegvis mekanisk montering')
    c.setAuthor('FormNerd')
    for index, step in enumerate(STEPS):
        w, h = A4
        c.setFillColor(colors.black)
        c.setFont('Strong', 10)
        c.drawString(44, 806, 'ENTROPI / CAD V05')
        c.setFont('Text', 9)
        c.drawRightString(w - 44, 806, 'MEKANISK MONTERING · R01')
        c.setFont('Strong', 25)
        c.drawString(44, 765, step['title'])
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(44, 744, w - 44, 744)
        if step.get('kind') == 'inventory':
            inventory(c)
        else:
            if step.get('optional'):
                c.setFont('Strong', 9)
                c.drawString(44, 722, 'VALFRITT / FØRESET MÅLT MASKINVARE')
            fig = figures[index]
            x, y, iw, ih = 30, 302, w - 60, (w - 60) * fig['height'] / fig['width']
            c.drawImage(ImageReader(str(OUT / fig['file'])), x, y, iw, ih)
            for item in fig['arrows']:
                start = (x + item['from'][0] / fig['width'] * iw, y + item['from'][1] / fig['height'] * ih)
                end = (x + item['to'][0] / fig['width'] * iw, y + item['to'][1] / fig['height'] * ih)
                if item['moving'] and item['id'] in step.get('motion_ids', step.get('new', [])):
                    arrow(c, start, end)
                label_offset = step.get('label_offsets', {}).get(item['id'], [0, 0])
                label = (start[0] + label_offset[0], start[1] + label_offset[1])
                if any(label_offset):
                    c.setStrokeColor(colors.black)
                    c.setLineWidth(.65)
                    c.line(*label, *start)
                c.setFillColor(colors.white)
                c.setStrokeColor(colors.black)
                c.setLineWidth(.8)
                c.circle(label[0], label[1], 9.2, stroke=1, fill=1)
                c.setFillColor(colors.black)
                c.setFont('Strong', 8)
                c.drawCentredString(label[0], label[1] - 3, item['id'])
            if step.get('cutaway'):
                c.setFont('Text', 8)
                c.setFillColor(colors.HexColor('#555555'))
                c.drawString(44, 299, 'Snitt i 01 viser innsida. Snittet er berre ei visning, ikkje eit produksjonskutt.')
            part_ids = ', '.join(dict.fromkeys(p['id'] for p in step['parts']))
            c.setFillColor(colors.black)
            c.setFont('Strong', 9)
            c.drawString(44, 270, 'DELAR  ' + part_ids)
            if step.get('screws'):
                c.drawRightString(w - 44, 270, step['screws'])
            paragraph(c, step['text'], 44, 238, w - 88, 12, 18)
            c.setStrokeColor(colors.HexColor('#BBBBBB'))
            c.line(44, 151, w - 44, 151)
            c.setFont('Strong', 9)
            c.drawString(44, 132, 'KONTROLLER')
            paragraph(c, step['check'], 44, 113, w - 88, 10.5, 15)
        c.setStrokeColor(colors.HexColor('#BBBBBB'))
        c.line(44, 44, w - 44, 44)
        c.setFillColor(colors.HexColor('#555555'))
        c.setFont('Text', 8)
        c.drawString(44, 28, 'Faktisk CAD-geometri. Mål i mm. Fysisk maskinvarepassing er ikkje verifisert.')
        c.drawRightString(w - 44, 28, f'{index + 1:02d} / {len(STEPS):02d}')
        c.showPage()
    c.save()
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reuse-figures', action='store_true')
    parser.add_argument('--refresh-figures', nargs='*', type=int, default=[])
    args = parser.parse_args()
    (OUT / 'figures').mkdir(parents=True, exist_ok=True)
    (OUT / 'pages').mkdir(exist_ok=True)
    paths = {p.name[:2]: p for p in (CAD / 'parts').glob('*.stl')}
    meshes = {number: preview.load_part(path) for number, path in paths.items()}
    source_hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths.values()}
    preview.colors = flat_colors
    figures = {}
    with tempfile.TemporaryDirectory(prefix='entropi-manual-') as temporary:
        work = Path(temporary)
        source, raster = work / 'outline.cpp', work / 'outline'
        source.write_text(outlined_raster())
        subprocess.run(['g++', '-O3', '-std=c++17', str(source), '-o', str(raster)], check=True)
        for index, step in enumerate(STEPS):
            if step.get('kind') != 'inventory':
                reuse = args.reuse_figures and index + 1 not in args.refresh_figures
                figures[index] = render_step(step, meshes, index + 1, raster, work, reuse)
    pdf = build_pdf(figures)
    with tempfile.TemporaryDirectory(prefix='entropi-pdf-pages-') as temporary:
        temporary_pages = Path(temporary)
        subprocess.run(['pdftoppm', '-r', '110', '-png', str(pdf), str(temporary_pages / 'step')], check=True)
        for source in sorted(temporary_pages.glob('step-*.png')):
            with Image.open(source) as image:
                image.verify()
            target = OUT / 'pages' / source.name
            partial = target.with_suffix('.write.png')
            with partial.open('wb') as stream:
                stream.write(source.read_bytes())
                stream.flush()
                os.fsync(stream.fileno())
            with Image.open(partial) as image:
                image.verify()
            partial.replace(target)
    pages = sorted((OUT / 'pages').glob('step-*.png'))
    if len(pages) != len(STEPS):
        raise ValueError('Page count mismatch')
    for path in pages:
        with Image.open(path) as im:
            im.verify()
    report = {'version': 'v05-r01', 'pdf': pdf.name, 'pages': len(pages), 'geometry_sources_sha256': source_hashes, 'page_pngs': [str(p.relative_to(OUT)) for p in pages], 'actual_CAD_geometry': True, 'hardware_fit_verified': False, 'electrical_wiring_certified': False, 'equipment_evidence': {'title': 'Utstyret me har', 'author': 'Iver Raknes Finne', 'date': '2026-10-20', 'page': 1, 'exact_camera_switch_USB_and_battery_dimensions_provided': False}, 'notes': 'One assembly scene per page; cuts in cage are diagrammatic cutaways only. Nominal hardware is explicitly labelled. Render directions use native assembly coordinates.'}
    (OUT / 'manual_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'pdf': str(pdf), 'pages': len(pages), 'bytes': pdf.stat().st_size}), flush=True)


if __name__ == '__main__':
    main()
