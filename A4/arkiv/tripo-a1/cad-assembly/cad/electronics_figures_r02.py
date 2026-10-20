import html
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review/steps-r02'
OUT.mkdir(parents=True, exist_ok=True)
W, H, SS = 1800, 1300, 2
BLACK = '#17191b'
MID = '#d5d8da'
LIGHT = '#f4f5f5'
GREY = '#aeb4b7'
ORANGE = '#b95c24'


class Figure:
    def __init__(self):
        self.image = Image.new('RGB', (W * SS, H * SS), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="1800" height="1300" fill="white"/>']

    def poly(self, points, fill=LIGHT, stroke=BLACK, width=4):
        p = [(round(x * SS), round(y * SS)) for x, y in points]
        self.draw.polygon(p, fill=fill)
        if stroke:
            self.draw.line(p + [p[0]], fill=stroke, width=round(width * SS), joint='curve')
        coords = ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)
        self.svg.append(f'<polygon points="{coords}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{width}" stroke-linejoin="round"/>')

    def line(self, points, color=BLACK, width=4, dash=False):
        if dash:
            for a, b in zip(points[:-1], points[1:]):
                dist = math.dist(a, b)
                for i in range(0, int(dist), 22):
                    t0, t1 = i / dist, min(i + 11, dist) / dist
                    self.draw.line([(round((a[0] + (b[0] - a[0]) * t) * SS), round((a[1] + (b[1] - a[1]) * t) * SS)) for t in (t0, t1)], fill=color, width=round(width * SS))
        else:
            self.draw.line([(round(x * SS), round(y * SS)) for x, y in points], fill=color, width=round(width * SS), joint='curve')
        coords = ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)
        self.svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"' + (' stroke-dasharray="11 11"' if dash else '') + '/>')

    def rect(self, box, fill=LIGHT, stroke=BLACK, width=4, radius=0):
        p = tuple(round(v * SS) for v in box)
        if radius:
            self.draw.rounded_rectangle(p, radius=radius * SS, fill=fill, outline=stroke, width=round(width * SS))
        else:
            self.draw.rectangle(p, fill=fill, outline=stroke, width=round(width * SS))
        x, y, xx, yy = box
        self.svg.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" rx="{radius}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{width}"/>')

    def ellipse(self, box, fill='white', stroke=BLACK, width=4):
        self.draw.ellipse(tuple(round(v * SS) for v in box), fill=fill, outline=stroke, width=round(width * SS))
        x, y, xx, yy = box
        self.svg.append(f'<ellipse cx="{(x+xx)/2}" cy="{(y+yy)/2}" rx="{(xx-x)/2}" ry="{(yy-y)/2}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{width}"/>')

    def text(self, value, xy, size=36, bold=False, color=BLACK, anchor='la'):
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans' + ('-Bold' if bold else '') + '.ttf', size * SS)
        self.draw.text((round(xy[0] * SS), round(xy[1] * SS)), value, font=font, fill=color, anchor=anchor)
        svg_anchor = {'l': 'start', 'm': 'middle', 'r': 'end'}[anchor[0]]
        ascent, descent = font.getmetrics()
        y = xy[1] + ascent / SS if anchor[1] == 'a' else xy[1]
        self.svg.append(f'<text x="{xy[0]}" y="{y}" fill="{color}" font-family="DejaVu Sans, sans-serif" font-weight="{700 if bold else 400}" font-size="{size}" text-anchor="{svg_anchor}">{html.escape(value)}</text>')

    def arrow(self, a, b, color=BLACK, width=9, head=30):
        self.line([a, b], color=color, width=width)
        d = math.dist(a, b)
        u = ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
        p = (-u[1], u[0])
        self.poly([b, (b[0] - head * u[0] + head * 0.47 * p[0], b[1] - head * u[1] + head * 0.47 * p[1]), (b[0] - head * u[0] - head * 0.47 * p[0], b[1] - head * u[1] - head * 0.47 * p[1])], fill=color, stroke=color, width=1)

    def leader(self, point, elbow, end, label, size=35, anchor='la'):
        self.line([point, elbow, end], width=3)
        self.ellipse((point[0]-5, point[1]-5, point[0]+5, point[1]+5), fill=BLACK, width=1)
        self.text(label, (end[0] + (14 if anchor[0] == 'l' else -14), end[1]-24), size=size, bold=True, anchor=anchor)

    def save(self, name):
        self.image.resize((W, H), Image.Resampling.LANCZOS).save(OUT / (name + '.png'))
        (OUT / (name + '.svg')).write_text('\n'.join(self.svg) + '\n</svg>\n')


def iso(cx=900, cy=500, scale=10):
    return lambda x, y, z: (cx + (x-y) * scale * 0.8660254, cy + (x+y) * scale * 0.5 - z * scale)


def box(f, p, x, y, z, dx, dy, dz, top=LIGHT, side=MID, edge=BLACK, width=3):
    f.poly([p(x,y,z),p(x+dx,y,z),p(x+dx,y,z+dz),p(x,y,z+dz)], fill=side, stroke=edge, width=width)
    f.poly([p(x+dx,y,z),p(x+dx,y+dy,z),p(x+dx,y+dy,z+dz),p(x+dx,y,z+dz)], fill=GREY, stroke=edge, width=width)
    f.poly([p(x,y,z+dz),p(x+dx,y,z+dz),p(x+dx,y+dy,z+dz),p(x,y+dy,z+dz)], fill=top, stroke=edge, width=width)
    f.poly([p(x,y+dy,z),p(x+dx,y+dy,z),p(x+dx,y+dy,z+dz),p(x,y+dy,z+dz)], fill=side, stroke=edge, width=width)


def mb(f, p, z=0):
    box(f,p,0,0,z,32,45,1.6,top='#e6e8e9')
    for x in (2,28):
        box(f,p,x,5,z+1.6,2,25,7,top='#44494c',side='#555b5e')
        for y in range(6,28,3):
            a=p(x+0.4,y,z+8.6)
            b=p(x+1.6,y+1.3,z+8.6)
            f.ellipse((min(a[0],b[0])-4,min(a[1],b[1])-2,max(a[0],b[0])+4,max(a[1],b[1])+2),fill='white',width=1)
    box(f,p,10,36,z+1.6,12,9,4,top='#c7cccf')
    a=p(10.8,45.1,z+2.0);b=p(21.2,45.1,z+4.7)
    f.poly([p(10.8,45.1,z+2),p(21.2,45.1,z+2),p(21.2,45.1,z+4.7),p(10.8,45.1,z+4.7)],fill=BLACK,width=2)
    box(f,p,11,14,z+1.6,10,9,2.4,top='#9ca4a8')
    for x in (9,20):
        box(f,p,x,30,z+1.6,4,4,2.5,top='#dce0e2')
    return p(16,46,z+3.3)


def cam(f,p,z=26,sensor=True):
    for x in (2.7,28.7):
        for y in range(6,28,3):
            box(f,p,x,y,z-5,0.7,0.7,5,top='#9d9682',side='#b9af94',width=1.7)
    box(f,p,2.5,1.5,z,27,40.5,1.6,top='#e9ebec')
    box(f,p,7,5,z+1.6,17,12,1.8,top='#cbd0d3')
    f.line([p(8,8,z+3.5),p(22,8,z+3.5)],width=2)
    f.line([p(8,11,z+3.5),p(22,11,z+3.5)],width=2)
    box(f,p,7,24,z+1.6,17,3,1.5,top='#a6acaf')
    f.poly([p(10,26,z+3.2),p(21,26,z+3.2),p(21,33,z+5),p(10,33,z+5)],fill='#c4b6a6',width=2)
    if sensor:
        box(f,p,10,31,z+4,11,9,2,top='#71787c',side='#9da4a8')
        center=p(15.5,35.5,z+7)
        f.ellipse((center[0]-36,center[1]-25,center[0]+36,center[1]+25),fill='#33383b',width=3)
        f.ellipse((center[0]-19,center[1]-13,center[0]+19,center[1]+13),fill='#747d83',width=2)


def laptop(f, x=100, y=430, s=1):
    pp=lambda a,b:(x+a*s,y+b*s)
    f.poly([pp(40,0),pp(510,0),pp(560,350),pp(90,350)],fill='#e3e6e8',width=5)
    f.poly([pp(64,28),pp(488,28),pp(529,305),pp(105,305)],fill='white',width=3)
    f.poly([pp(90,350),pp(560,350),pp(660,450),pp(0,450)],fill='#e3e6e8',width=5)
    f.poly([pp(0,450),pp(660,450),pp(650,467),pp(10,467)],fill='#b4bbbf',width=3)
    for yy in (365,385,405):
        f.line([pp(105,yy),pp(540+(yy-365),yy)],width=2,color='#899296')
    f.poly([pp(250,420),pp(410,420),pp(440,443),pp(225,443)],fill='#c3c9cc',width=2)
    f.text('Arduino IDE',pp(140,80),size=round(37*s),bold=True)
    for i,l in enumerate(['ESP32-CAM','AI Thinker','USB  /  Upload']):
        f.text(l,pp(144,145+i*49),size=round(28*s))
    return pp(650,428)


def wire(f, points, color=BLACK, width=11):
    f.line(points,color='white',width=width+10)
    f.line(points,color=color,width=width)


def button(f,p,z=0):
    for x,y in [(-3,1),(-3,5),(7,1),(7,5)]:
        box(f,p,x,y,z,2,0.8,0.7,top='#9da6ab',side='#aab1b6',width=2)
    box(f,p,0,0,z,6,6,3.5,top='#d7dcdf',side='#aab1b6')
    c=p(3,3,z+4.2)
    f.ellipse((c[0]-32,c[1]-20,c[0]+32,c[1]+20),fill='#5d666b',width=3)
    return [p(-2,1.4,z+.7),p(-2,5.4,z+.7),p(8,1.4,z+.7),p(8,5.4,z+.7)]


def make():
    f=Figure();p=iso(1000,770,11)
    mb(f,p)
    for x,y in [(3,6),(29,6),(3,27),(29,27)]:
        f.line([p(x,y,9),p(x,y,33)],color='#737d82',width=2.5,dash=True)
    cam(f,p,z=42)
    f.arrow((1450,430),(1450,830),width=11,head=40)
    f.leader(p(3,3,44),(660,290),(450,290),'E1  ESP32-CAM',size=38,anchor='ra')
    f.leader(p(1,31,2),(590,1010),(330,1010),'E2  MB',size=38,anchor='ra')
    f.leader(p(16,45,4),(905,1170),(1120,1170),'Micro-USB',size=34)
    f.text('2 × 8', (1470,620), size=35, bold=True)
    f.save('e01-stack')

    f=Figure();port=laptop(f,70,345,.95);p=iso(1400,620,8.8)
    target=mb(f,p);cam(f,p,z=10)
    wire(f,[port,(850,810),(1000,1040),(1190,1030),(target[0],target[1]+25),(target[0],target[1])])
    f.rect((target[0]-18,target[1]-5,target[0]+22,target[1]+39),fill='#e4e7e8',width=3,radius=5)
    f.text('USB-datakabel',(825,1100),size=36,bold=True,anchor='ma')
    f.arrow((810,480),(1100,480),head=36,width=9)
    f.text('Upload',(955,420),size=39,bold=True,anchor='ma')
    f.text('E1 + E2',(1470,960),size=38,bold=True,anchor='ma')
    f.save('e02-usb')

    f=Figure()
    f.rect((1000,230,1510,900),fill='#e7eaec',radius=40,width=6)
    f.rect((1050,295,1460,470),fill='white',radius=14,width=4)
    f.text('Ω',(1255,307),size=88,bold=True,anchor='ma')
    f.text('kontinuitet',(1255,421),size=27,anchor='ma')
    f.ellipse((1150,540,1360,750),fill='#c6cdd1',width=5)
    f.line([(1255,645),(1325,580)],width=15)
    f.ellipse((1070,810,1120,860),fill=BLACK,width=3)
    f.ellipse((1370,810,1420,860),fill=ORANGE,width=3)
    f.text('COM',(1095,870),size=24,bold=True,anchor='ma')
    f.text('Ω',(1395,870),size=24,bold=True,anchor='ma')
    p=iso(460,745,30);pins=button(f,p)
    wire(f,[(1095,835),(1040,1060),(770,1100),(640,1020),pins[1]],width=9)
    wire(f,[(1395,835),(1430,1100),(1050,1170),(780,1020),pins[2]],color=ORANGE,width=9)
    for i,(px,py) in enumerate(pins):
        off=[(-75,-35),(-80,28),(55,-30),(60,32)][i]
        f.text(str(i+1),(px+off[0],py+off[1]),size=36,bold=True)
    f.text('E3',(455,590),size=42,bold=True,anchor='ma')
    f.text('Mål før kopling',(1255,140),size=43,bold=True,anchor='ma')
    f.save('e03-switch-test')

    f=Figure()
    f.rect((170,270,655,1010),fill=LIGHT,radius=24,width=5)
    f.text('ESP32-CAM',(412,310),size=40,bold=True,anchor='ma')
    f.text('3,3 V',(410,415),size=38,bold=True,anchor='ma')
    f.line([(410,475),(410,510)],width=5)
    f.line([(410,510),(390,530),(430,550),(390,570),(430,590),(390,610),(410,630)],width=4)
    f.line([(410,630),(410,710),(670,710)],width=5)
    f.ellipse((401,701,419,719),fill=BLACK,width=1)
    f.line([(300,710),(410,710)],width=4)
    f.text('GPIO13',(185,733),size=35,bold=True)
    f.text('INPUT_PULLUP',(412,880),size=29,bold=True,anchor='ma')
    f.line([(670,710),(1000,710)],color=ORANGE,width=8)
    for x in (1000,1250):
        f.ellipse((x-12,698,x+12,722),fill='white',width=5)
    f.line([(1012,703),(1230,590)],width=8)
    f.line([(1110,550),(1110,630)],width=5)
    f.line([(1075,550),(1145,550)],width=6)
    f.text('E3  NO',(1115,450),size=40,bold=True,anchor='ma')
    f.line([(1262,710),(1520,710),(1520,865)],width=8)
    for yy,span in [(865,65),(890,43),(915,22)]:
        f.line([(1520-span,yy),(1520+span,yy)],width=5)
    f.text('GND',(1520,960),size=38,bold=True,anchor='ma')
    f.text('Ingen microSD',(1090,1060),size=35,bold=True,anchor='ma')
    f.save('e04-schematic')

    f=Figure()
    f.rect((160,220,800,1010),fill=LIGHT,radius=24,width=5)
    f.text('ESP32-CAM',(480,270),size=44,bold=True,anchor='ma')
    for y,label,col in [(535,'GPIO13',ORANGE),(825,'GND',BLACK)]:
        f.rect((300,y-55,710,y+55),fill='white',radius=12,width=4)
        f.text(label,(450,y-27),size=40,bold=True,anchor='ma')
        f.ellipse((645,y-17,679,y+17),fill=col,width=2)
    p=iso(1350,720,31);pins=button(f,p)
    wire(f,[(662,535),(940,535),(1050,700),pins[1]],color=ORANGE,width=10)
    wire(f,[(662,825),(940,825),(1110,930),pins[3]],width=10)
    f.text('A',(pins[1][0]-60,pins[1][1]-80),size=38,bold=True,color=ORANGE)
    f.text('B',(pins[3][0]+30,pins[3][1]+10),size=38,bold=True)
    f.text('E3',(1350,530),size=44,bold=True,anchor='ma')
    f.text('A ≠ B',(1350,1000),size=45,bold=True,anchor='ma')
    f.text('Funksjon, ikkje fysisk pinneplassering',(875,1150),size=30,anchor='ma')
    f.save('e05-wiring')

    f=Figure();port=laptop(f,80,335,.88);p=iso(1350,620,8.5)
    target=mb(f,p);cam(f,p,z=10)
    wire(f,[port,(820,850),(920,1030),(1120,1040),(target[0],target[1]+25),target],width=10)
    f.rect((target[0]-18,target[1]-5,target[0]+22,target[1]+38),fill='#e4e7e8',width=3,radius=5)
    f.text('USB',(890,1080),size=35,bold=True,anchor='ma')
    f.rect((720,100,1090,610),fill='#e7eaec',radius=36,width=5)
    f.rect((745,150,1065,550),fill='white',radius=12,width=3)
    f.text('Wi-Fi',(905,190),size=42,bold=True,anchor='ma')
    f.rect((785,300,1025,460),fill='#e0e4e6',radius=8,width=3)
    f.poly([(800,445),(860,355),(920,430),(950,390),(1010,445)],fill='#b4bdc3',width=2)
    f.ellipse((960,325,990,355),fill='white',width=2)
    f.ellipse((884,565,926,595),fill='white',width=2)
    f.arrow((1260,400),(1135,345),head=30,width=7)
    f.text('Første bilete',(905,60),size=40,bold=True,anchor='ma')
    f.save('e06-bench')

    f=Figure();p=iso(900,700,12)
    box(f,p,-10,-3,0,36,36,1.6,top='#e7eaeb')
    box(f,p,-6,15,1.6,24,4,2.8,top='#b9c1c5')
    f.poly([p(-4,18,4.5),p(16,18,4.5),p(16,27,7),p(16,36,16),p(-4,36,16),p(-4,27,7)],fill='#c9bcae',width=3)
    for x in (-1,2,5,8,11,14):
        f.line([p(x,18,4.7),p(x,27,7.2),p(x,36,16.2)],color='#a4937e',width=1.5)
    box(f,p,-7,34,15,26,21,2.5,top='#a5adb2')
    c=p(6,44.5,19)
    f.ellipse((c[0]-82,c[1]-54,c[0]+82,c[1]+54),fill='#333a3e',width=5)
    f.ellipse((c[0]-44,c[1]-29,c[0]+44,c[1]+29),fill='#8c999f',width=3)
    f.leader(p(-5,16,4),(720,330),(390,330),'FFC',size=44,anchor='ra')
    f.leader(p(15,29,10),(1160,560),(1410,560),'Mjuk boge',size=37)
    f.leader(c,(570,1050),(380,1050),'OV2640',size=40,anchor='ra')
    f.save('e07-flex')

    f=Figure();p=iso(1100,490,12.5)
    mb(f,p);cam(f,p,z=10)
    box(f,p,11.5,53,1.8,9,4,2.6,top='#dce1e4',side='#b8c0c5')
    box(f,p,10,57,.8,12,10,5,top='#e4e8ea',side='#c2c9cd')
    cable=p(16,67,3.3)
    wire(f,[cable,p(16,76,3.3),(400,1140),(260,1140)],width=14)
    f.arrow(p(31,49,9),p(31,65,9),head=38,width=10)
    f.text('USB FRÅ',(900,150),size=57,bold=True,anchor='ma')
    f.text('E1 + E2',(1380,830),size=39,bold=True,anchor='ma')
    f.save('e08-disconnect')


if __name__ == '__main__':
    make()
    print(OUT)
