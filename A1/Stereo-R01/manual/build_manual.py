import json
import hashlib
import math
import sys
from pathlib import Path

import fitz
import numpy as np
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from render import load_objects, render, unit


ROOT = Path(__file__).resolve().parent
W, H = 595.276, 841.89
FONT = str(ROOT / 'assets/fonts/DejaVuSans.ttf')
FONT_BOLD = str(ROOT / 'assets/fonts/DejaVuSans-Bold.ttf')
pdfmetrics.registerFont(TTFont('Manual', FONT))
pdfmetrics.registerFont(TTFont('ManualBold', FONT_BOLD))
FIGURE_FILES = set()


def text(c, x, y, value, size=11, bold=False):
    c.setFont('ManualBold' if bold else 'Manual', size)
    c.drawString(x, y, value)


def wrap(c, value, x, y, width, size=10, leading=15):
    words, lines, line = value.split(), [], ''
    for word in words:
        test = (line + ' ' + word).strip()
        if pdfmetrics.stringWidth(test, 'Manual', size) > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    for value in lines:
        text(c, x, y, value, size)
        y -= leading
    return y


def frame(c, number, revision):
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(0.65)
    c.rect(19, 25, W - 38, H - 44)
    text(c, 35, 41, 'FORMNERD', 8)
    c.setFont('Manual', 8)
    c.drawCentredString(W / 2, 41, revision)
    c.drawRightString(W - 35, 41, f'{number:02d}')


def arrow(c, a, b):
    d = np.asarray(b, float) - a
    length = np.linalg.norm(d)
    if length < 10:
        return
    v, n = d / length, np.array([-d[1], d[0]]) / length
    base = np.asarray(b) - v * 9
    points = [np.asarray(a) + n * 2.5, base + n * 2.5, base + n * 6,
              np.asarray(b), base - n * 6, base - n * 2.5, np.asarray(a) - n * 2.5]
    p = c.beginPath()
    p.moveTo(*points[0])
    for point in points[1:]:
        p.lineTo(*point)
    p.close()
    c.setFillColorRGB(1, 1, 1)
    c.setLineWidth(0.8)
    c.drawPath(p, stroke=1, fill=1)
    c.setFillColorRGB(0, 0, 0)


def badge(c, x, y, label, r=14):
    c.setFillColorRGB(1, 1, 1)
    c.setLineWidth(0.7)
    c.circle(x, y, r, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont('Manual', 10)
    c.drawCentredString(x, y - 3.4, label)


def figure(c, scene, rect, name, labels=None, arrows=None):
    x, y, w, h = rect
    s = dict(scene)
    s.update(mode='line', size=[2000, max(800, round(2000*h/w))], supersample=1.35, line_width=0.45*2000/w)
    path = ROOT / 'figures' / f'{name}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    scene_path = path.with_suffix('.json')
    scene_path.write_text(json.dumps(s, indent=2))
    metadata = render(s, path, ROOT.parent)
    FIGURE_FILES.update(str(p.relative_to(ROOT.parent)) for p in [path, scene_path, path.with_suffix('.anchors.json')])
    c.drawImage(ImageReader(str(path)), x, y, w, h, mask='auto')
    def screen(p):
        return np.array([x + p[0] / s['size'][0] * w, y + h - p[1] / s['size'][1] * h])
    for label in labels or []:
        info = metadata['anchors'][label['id']]
        pixel = info['center']
        if 'anchor_fraction' in label:
            bounds = np.asarray(info['bounds'])
            pixel = bounds[0] + np.asarray(label['anchor_fraction']) * (bounds[1] - bounds[0])
        anchor = screen(pixel)
        center = anchor + np.asarray(label['offset']) if 'offset' in label else (x + label['position'][0] * w, y + label['position'][1] * h)
        c.setLineWidth(0.65)
        c.line(*center, *anchor)
        c.circle(*anchor, 1.7, fill=1, stroke=0)
        badge(c, *center, label['text'])
    if arrows:
        objects = load_objects(s, ROOT.parent)
        direction = unit(s.get('camera', {}).get('direction', [-1, -2, 1]))
        up = unit(s.get('camera', {}).get('up', [0, 0, 1]))
        right = unit(np.cross(up, direction))
        up = unit(np.cross(direction, right))
        basis = np.column_stack([right, up, direction])
        vs = [m.vertices @ basis for _, m, _ in objects]
        lo, hi = np.min([v.min(0) for v in vs], 0), np.max([v.max(0) for v in vs], 0)
        center = (hi + lo) / 2
        scale = min(s['size'][0]*(1-2*s.get('margin', 0.085))/(hi[0]-lo[0]), s['size'][1]*(1-2*s.get('margin', 0.085))/(hi[1]-lo[1]))
        def project(p):
            p = np.asarray(p) @ basis - center
            return screen([p[0]*scale+s['size'][0]/2, s['size'][1]/2-p[1]*scale])
        for movement in arrows:
            arrow(c, project(movement['from']), project(movement['to']))


def make(plan):
    sources = set()
    def collect(value):
        if isinstance(value, dict):
            if 'objects' in value:
                sources.update(o['path'] for o in value['objects'])
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
    collect(plan)
    def fingerprints():
        return {p: hashlib.sha256((ROOT.parent / p).read_bytes()).hexdigest() for p in sorted(sources)}
    hashes = fingerprints()
    out = ROOT / plan.get('filename', 'FormNerd-Stereo-R01-montering.pdf')
    c = canvas.Canvas(str(out), pagesize=(W, H))
    c.setTitle(plan['title'])
    c.setAuthor('FormNerd')
    for n, p in enumerate(plan['pages'], 1):
        frame(c, n, plan['revision'])
        kind = p.get('type', 'step')
        if kind == 'cover':
            text(c, 38, H-85, 'FORMNERD', 36, True)
            text(c, 40, H-116, p['title'], 18)
            figure(c, p['scene'], (25, 155, W-50, 515), f'{n:02d}-cover')
            text(c, 40, 133, p.get('subtitle', 'Montering av mekanisk prototype'), 12)
            wrap(c, p.get('note', ''), 40, 108, W-80, 9, 13)
        elif kind == 'inventory':
            text(c, 40, H-76, p['title'], 22)
            rows = math.ceil(len(p['items'])/2)
            cell_h = min(190, 605 / max(rows, 1))
            for i, item in enumerate(p['items']):
                col, row = i % 2, i // 2
                x, y = 35+col*263, H-118-(row+1)*cell_h
                figure(c, item['scene'], (x+4,y+33,248,cell_h-43), f'{n:02d}-part-{i+1}')
                badge(c, x+20, y+22, item['id'])
                text(c, x+43, y+18, item['name'], 10)
                c.setFont('Manual', 11)
                c.drawRightString(x+247,y+18,'×'+str(item['quantity']))
                if col == 0:
                    c.setLineWidth(0.35)
                    c.line(35,y-6,W-35,y-6)
            if p.get('note'):
                wrap(c,p['note'],40,85,W-80,9,13)
        else:
            step = p.get('number')
            if step is None:
                text(c,40,H-76,p['title'],23)
            else:
                text(c,38,H-105,str(step),57,True)
                text(c,104,H-77,p['title'],20)
            if p.get('hardware'):
                text(c,104,H-103,p['hardware'],10)
            if p.get('needed'):
                needed = p['needed']
                cell = min(78, 150 / len(needed))
                for k, item in enumerate(needed):
                    yy = H - 44 - (k + 1) * cell
                    c.setLineWidth(0.6)
                    c.rect(W - 151, yy, 112, cell)
                    figure(c, item['scene'], (W - 147, yy + 20, 104, cell - 24), f'{n:02d}-hardware-{k}')
                    text(c, W - 144, yy + 7, item['label'], 8)
                    c.setFont('Manual', 9)
                    c.drawRightString(W - 45, yy + 7, '×' + str(item['quantity']))
            figure(c,p['scene'],(25,187,W-50,450),f'{n:02d}-step',p.get('labels'),p.get('arrows'))
            y=156
            for sentence in p.get('instructions',[]):
                y=wrap(c,sentence,40,y,W-80,11,16)-7
            if p.get('check'):
                c.setLineWidth(0.6)
                c.line(40,91,W-40,91)
                wrap(c,p['check'],40,76,W-80,8.8,12)
        c.showPage()
    c.save()
    doc = fitz.open(out)
    pages = ROOT/'pages'
    pages.mkdir(exist_ok=True)
    for i,page in enumerate(doc):
        page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(pages/f'page-{i+1:02d}.png')
    if fingerprints() != hashes:
        raise RuntimeError('Source geometry changed while manual was rendering')
    audit = {'pages': len(doc), 'source_geometry_sha256': hashes, 'pdf_sha256': hashlib.sha256(out.read_bytes()).hexdigest(), 'figure_files': sorted(FIGURE_FILES), 'geometry_source': 'exported model parts, orthographic projection', 'imagegen_used_for_final_illustrations': False}
    (ROOT / 'render-audit.json').write_text(json.dumps(audit, indent=2))
    print(json.dumps({'pdf':str(out),'pages':len(doc)},indent=2))


if __name__ == '__main__':
    make(json.loads(Path(sys.argv[1]).read_text()))
