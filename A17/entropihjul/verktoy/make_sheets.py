import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from comp import over_white

D = '.'
out = sys.argv[1]
names = {1: 'V1 heva knapp', 2: 'V2 låg skive', 3: 'V3 tannhjul', 4: 'V4 original'}
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 26)
except Exception:
    font = ImageFont.load_default()
cw, ch = 724, 543
rows = []
for v in (1, 2, 3, 4):
    ref = Image.open(f'../referansar/konsept-V{v}.png').convert('RGB').resize((cw, ch), Image.LANCZOS)
    ren = Image.fromarray(over_white(f'{D}/out/v{v}.png')).resize((cw, ch), Image.LANCZOS)
    row = Image.new('RGB', (cw * 2, ch), (255, 255, 255))
    row.paste(ref, (0, 0)); row.paste(ren, (cw, 0))
    d = ImageDraw.Draw(row)
    d.text((18, 14), f'{names[v]}  ·  konsept', fill=(120, 120, 120), font=font)
    d.text((cw + 18, 14), f'{names[v]}  ·  CAD-rendring', fill=(120, 120, 120), font=font)
    rows.append(row)
S = Image.new('RGB', (cw * 2, ch * 4), (255, 255, 255))
for i, r in enumerate(rows):
    S.paste(r, (0, i * ch))
S.save(f'{out}/A17-entropihjul-samanlikning.png')
G = Image.new('RGB', (cw * 2, ch * 2), (255, 255, 255))
for i, v in enumerate((1, 2, 3, 4)):
    ren = Image.fromarray(over_white(f'{D}/out/v{v}.png')).resize((cw, ch), Image.LANCZOS)
    G.paste(ren, ((i % 2) * cw, (i // 2) * ch))
    ImageDraw.Draw(G).text(((i % 2) * cw + 18, (i // 2) * ch + 14), names[v], fill=(120, 120, 120), font=font)
G.save(f'{out}/A17-entropihjul-serie.png')
print('sheets written')
