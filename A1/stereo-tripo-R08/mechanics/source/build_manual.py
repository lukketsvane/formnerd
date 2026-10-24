from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image,ImageOps

R=Path(__file__).resolve().parents[1]
D=R/'manual';FIG=D/'figures';D.mkdir(parents=True,exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT));pdfmetrics.registerFont(TTFont('DejaVuB',BOLD))
W,H=A4
OUT=D/'ENTROPI_R08_innmat_monteringsrettleiing.pdf'
c=canvas.Canvas(str(OUT),pagesize=A4)
c.setTitle('ENTROPI R08: Mekanisk innmat, monteringsrettleiing')
c.setAuthor('FormNerd')

PAGES=[
 ('R08 · MEKANISK INNMAT','Frå komponentar til demonterbare haldarar', '11_assembled_internals.png', 'To ESP32-CAM, éin 5000 mAh powerbank. Ytterforma frå Tripo er ikkje produsert.', 'Digital konstruksjon. Ikkje klar for hovudprint eller elektrisk tilkopling.'),
 ('DELOVERSIKT','10 konstruksjonsdelar + 2 prøvedelar', '11_assembled_internals.png', 'P01 chassis ×1, P02 batteriramme ×1, P03 kamerahaldar ×2, P04 låseramme ×2, P05 linsekrage ×2, P06 knapp ×1, P07 knappeskive ×1.', 'Prøvar: T01 USB-hol ×1, T02 toleransekupong ×1. ESP32-CAM-MB inngår ikkje i ferdig innmat.'),
 ('01 · PASSFORM','Prent og prøv desse først', '01_fit_coupons.png', 'Prent T01 og T02 i same filament og laghøgd som hovuddelane. Prøv kortkant, linseopning og skruepassform.', 'Ikkje gå vidare dersom den faktiske USB- eller PCB-geometrien avvik frå dei nominelle måla.'),
 ('02 · BATTERI','Set powerbanken ned i U-ramma', '02_battery_insert.png', 'Plasser Linocell 94 × 62 × 15 mm med USB-A og USB-C vendt mot den opne kortsida av ramma.', 'Batteriet skal kunne lyftast ut att. I sluttproduktet må baklokket halde det på plass.'),
 ('03 · VENSTRE KORT','Før ESP32-CAM inn i P03-L', '03_slide_left_PCB.png', 'Skyv kortet i dei to kantførarane. Hald kameralinse, SD-spor og komponentar frie.', 'Kontroller kortbreidd 27 mm og lengd 40,5 mm mot din faktiske modul.'),
 ('04 · HØGRE KORT','Gjenta med det andre kamerakortet', '04_slide_right_PCB.png', 'Monter det andre identiske ESP32-CAM-kortet i P03-R, med same orientering og frontretning.', 'Lik retning på dei to sensorane er nødvendig for stereopar.'),
 ('05 · LÅSERAMMER','Fest P04 på begge korta', '05_attach_retainer.png', 'Legg låseramma framfor kortet, innrett dei to sidehola og bruk nominelt M2 × 8, to skruar per kort.', 'Kontroller at inga skrue eller plastflate pressar mot komponentar eller flekskabel.'),
 ('06 · CHASSIS','Fest dei to korthaldarane på P01', '06_sleds_into_spine.png', 'Innrett fire hol per haldar med chassisskinnene. Prøv nominelt M2 × 6, åtte skruar totalt.', 'Stram berre etter passformprøve. Pilothola er modellert Ø1,55 mm, ikkje metrisk gjenga.'),
 ('07 · BATTERIPLAN','Baksidepakken blir ein eigen del', '07_outer_chassis.png', 'P02 ligg bak korthaldarane og har ei open side mot den planlagde USB-veggen. P01 og P02 får sine endelege feste frå ytterskalet.', 'Ytterskal og bakdeksel manglar i denne revisjonen, så desse delane er enno ikkje låste saman.'),
 ('08 · OPTIKK','To separate linsekragar', '08_lens_turrets.png', 'P05-L og P05-R er separate prentdelar. Nominell indre opning er Ø9,1 mm.', 'Sensorane er føresett sideforskyvde 10 mm frå PCB-senter. Faktisk flekslengd og optisk akse må prøvast.'),
 ('09 · USB-VEGG','Ingen portbrønn. Berre hol.', '10_USB_cutout.png', 'Portenden på powerbanken er lagt 0,45 mm frå nominell innervegg. T01 viser berre to hol gjennom 2,6 mm plast.', 'USB-A- og USB-C-posisjonane er førebelse. Intern straumfordeling er ikkje montert eller testa.'),
 ('10 · UTLØYSAR','Prøv P06 med P07', '09_button_mechanism.png', 'P06 har ein separat knappestamme og P07 ei sikringsskive. Begge må tilpassast det godkjende ytterskalet.', 'Elektrisk mikrobrytar, tilbakestilling og slaglengd er ikkje ferdig verifiserte.'),
 ('11 · KONTROLL','Monter utan lim før endeleg skal', '11_assembled_internals.png', 'Kontroller avstandar, klaringar, tilgang gjennom bakopning og mogleg uttak av begge kretskorta.', 'R08 er innmat under utvikling. Tripo-skall, straumkopling, sensorfleks, slicing og fysisk prøve står att.'),
]

def img_cover(fn,x,y,w,h):
 path=FIG/fn
 with Image.open(path) as im:
  iw,ih=im.size
 scale=min(w/iw,h/ih);nw,nh=iw*scale,ih*scale
 c.drawImage(str(path),x+(w-nw)/2,y+(h-nh)/2,width=nw,height=nh,mask='auto')

def wrap(text,maxpts=505,size=10.4):
 words=text.split();lines=[];buf=''
 for token in words:
  trial=(buf+' '+token).strip()
  if pdfmetrics.stringWidth(trial,'DejaVu',size)>maxpts and buf:
   lines.append(buf);buf=token
  else:buf=trial
 if buf:lines.append(buf)
 return lines

def textblock(s,x,y,size=10.7,leading=17,maxwidth=499,color=(.16,.16,.16)):
 c.setFont('DejaVu',size);c.setFillColorRGB(*color)
 for line in wrap(s,maxwidth,size):c.drawString(x,y,line);y-=leading
 return y

for idx,(over,title,image_name,action,note) in enumerate(PAGES):
 c.setFillColorRGB(.08,.08,.08);c.setFont('DejaVuB',10);c.drawString(44,H-43,'ENTROPI  /  FOR M N E R D')
 c.setFont('DejaVu',8.2);c.drawRightString(W-44,H-43,'R08  ·  PROTOTYPE')
 c.setLineWidth(.8);c.line(44,H-54,W-44,H-54)
 c.setFont('DejaVu',11);c.setFillColorRGB(.42,.42,.42);c.drawString(44,H-91,over)
 c.setFont('DejaVuB',19.2 if len(title)<39 else 17.0);c.setFillColorRGB(.08,.08,.08);c.drawString(44,H-124,title)
 img_cover(image_name,38,202,W-76,468)
 arrows={4:[(420,525,420,407)],5:[(420,525,420,407)],6:[(420,390,354,438)]}
 if idx in arrows:
  import math
  for x0,y0,x1,y1 in arrows[idx]:
   c.saveState();c.setStrokeColorRGB(.14,.14,.14);c.setLineWidth(1.35);c.setDash(4,3);c.line(x0,y0,x1,y1);c.setDash();angle=math.atan2(y1-y0,x1-x0);d=11
   pa=(x1-d*math.cos(angle-.38),y1-d*math.sin(angle-.38));pb=(x1-d*math.cos(angle+.38),y1-d*math.sin(angle+.38));c.line(x1,y1,*pa);c.line(x1,y1,*pb);c.restoreState()
 c.setLineWidth(.7);c.line(44,192,W-44,192)
 y=textblock(action,44,173,size=10.1,leading=16,maxwidth=W-88)
 y=textblock(note,44,y-13,size=9.1,leading=15,maxwidth=W-88,color=(.39,.39,.39))
 c.setStrokeColorRGB(.37,.37,.37);c.setLineWidth(.5);c.line(44,54,W-44,54)
 c.setFont('DejaVu',8);c.setFillColorRGB(.36,.36,.36)
 c.drawString(44,38,'TEKNISK PRØVE  /  nominelle mål i mm')
 c.drawRightString(W-44,38,f'{idx+1} / {len(PAGES)}')
 c.showPage()
c.save()
print(str(OUT),len(PAGES),'pages')