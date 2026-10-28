from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz
R=Path(__file__).resolve().parents[1]
OUT=R/'output';OUT.mkdir(exist_ok=True)
PAGES=R/'pages';PAGES.mkdir(exist_ok=True)
for n,f in [('Sans','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(n,str(R/'source/fonts'/f)))
W,H=A4;M=42;CW=W-84;N=17;PN=0;TEXT=[];SCENES=[];USED=set();TITLES=[]
PDF=OUT/'ENTROPI_R04_Monteringsmanual.pdf'
c=canvas.Canvas(str(PDF),pagesize=A4,pageCompression=1,invariant=1)
c.setTitle('ENTROPI R04 USB18 | Monteringsmanual 08');c.setAuthor('Formnerd');c.setSubject('Montering, støttefjerning og funksjonskontroll. Kortinnføringa har eit eige kontrollpunkt.')

def text(x,y,s,size=10,bold=False):
 c.setFillGray(0);c.setFont('Bold' if bold else 'Sans',size);c.drawString(x,y,s)
 TEXT.append({'page':PN,'text':s,'bbox':[x,y-size*.25,x+pdfmetrics.stringWidth(s,'Bold' if bold else 'Sans',size),y+size]})
def center(x,y,s,size=10,bold=False):text(x-pdfmetrics.stringWidth(s,'Bold' if bold else 'Sans',size)/2,y,s,size,bold)
def para(s,x=M,y=100,w=CW,size=10,leading=15,bold=False):
 ls=[];line=''
 for word in s.split():
  cand=(line+' '+word).strip()
  if line and pdfmetrics.stringWidth(cand,'Bold' if bold else 'Sans',size)>w:ls.append(line);line=word
  else:line=cand
 if line:ls.append(line)
 for i,t in enumerate(ls):text(x,y-i*leading,t,size,bold)
 return y-len(ls)*leading

def start(title,step=None,caption=None):
 global PN
 PN+=1;TITLES.append({'page':PN,'title':title,'step':step});c.bookmarkPage(str(PN));c.addOutlineEntry(f'{PN}. {title}',str(PN),0)
 if step is not None:text(M,H-72,str(step),35,True)
 elif PN!=1:text(M,H-72,title,25,True)
 if caption:para(caption,M,H-96,CW,9,13)
 text(M,25,str(PN),7)
 text(W-153,25,'ENTROPI R04 USB18 / 08',6.5)
def end():c.showPage()
def line(a,b,width=.6,gray=0):
 c.setStrokeGray(gray);c.setLineWidth(width);c.line(*a,*b)
def arrow(a,b,width=1.5):
 a=np.array(a,dtype=float);b=np.array(b,dtype=float);v=b-a;L=np.linalg.norm(v)
 if L<10:return
 v/=L;n=np.array([-v[1],v[0]])
 c.setStrokeGray(1);c.setLineWidth(width+2.4);c.line(*a,*(b-v*6));c.setStrokeGray(0);c.setLineWidth(width);c.line(*a,*(b-v*6))
 p=c.beginPath();p.moveTo(*b);p.lineTo(*(b-v*9+n*3.4));p.lineTo(*(b-v*9-n*3.4));p.close();c.setFillGray(0);c.setStrokeGray(1);c.setLineWidth(2);c.drawPath(p,stroke=1,fill=1);c.drawPath(p,stroke=0,fill=1)
def raster(path,rect):
 p=R/path;USED.add(str(p.relative_to(R)));im=Image.open(p);iw,ih=im.size;x,y,w,h=rect;sc=min(w/iw,h/ih);dw=iw*sc;dh=ih*sc;xx=x+(w-dw)/2;yy=y+(h-dh)/2;c.drawImage(str(p),xx,yy,dw,dh)
 return lambda uv:np.array([xx+uv[0]*dw,yy+uv[1]*dh])
def technical(name,rect,arrows=False):
 proj=raster('figures/technical_'+name+'.png',rect);p=R/'figures'/('technical_'+name+'.json');USED.add(str(p.relative_to(R)));d=json.loads(p.read_text());SCENES.append({'page':PN,'scene':name})
 if arrows:
  for a in d['anchors'].values():
   if 'shown_center_uv' not in a:continue
   q=proj(a['shown_center_uv']);z=proj(a['assembled_center_uv']);v=z-q
   if np.linalg.norm(v)>20:arrow(q+v*.32,q+v*.82)
 return proj,d

def vector(name,rect,arrows=False):
 p=R/'vector'/(name+'.json')
 if not p.exists():p=R/'vectors'/(name+'.json')
 USED.add(str(p.relative_to(R)));d=json.loads(p.read_text());x,y,w,h=rect;x0,y0,x1,y1=d['bbox'];sc=min(w/(x1-x0),h/(y1-y0));ox=x+(w-(x1-x0)*sc)/2-x0*sc;oy=y+(h-(y1-y0)*sc)/2-y0*sc
 c.setLineCap(1);c.setLineJoin(1);c.setStrokeGray(0)
 for g in d['groups']:
  c.setLineWidth(.52 if g['kind']=='outline' else .32);p=c.beginPath()
  for i,(a,b) in enumerate(g['xy']):
   if i:p.lineTo(ox+a*sc,oy+b*sc)
   else:p.moveTo(ox+a*sc,oy+b*sc)
  c.drawPath(p)
 proj=lambda xy:np.array([ox+xy[0]*sc,oy+xy[1]*sc]);basis=np.array(d['basis']);p3=lambda xyz:proj((basis@np.array(xyz))[:2])
 if arrows:
  for a in d.get('anchors',{}).values():
   if 'shown_xy' in a and np.linalg.norm(a.get('move_mm',[0,0,0]))>0:
    q=proj(a['shown_xy']);z=proj(a['target_xy']);v=z-q;arrow(q+v*.3,q+v*.82)
 return p3,d

def qty(x,y,count,pid):
 text(x,y,f'{count}×',16);text(x,y-15,pid,8)
def part(name,rect,count,pid):
 x,y,w,h=rect;vector(name,(x,y+42,w,h-42));qty(x+8,y+14,count,pid)
def tag(at,label,delta):
 at=np.array(at);q=at+np.array(delta);line(at,q,.5);text(q[0]+3,q[1]-3,label,10)
def leader(at,to,radius=5.5):
 at=np.array(at);to=np.array(to);delta=to-at;start=at+delta/np.linalg.norm(delta)*radius;c.setStrokeGray(0);c.setLineWidth(.6);p=c.beginPath();p.moveTo(*start);dy=to[1]-start[1];p.curveTo(start[0],start[1]+dy*.55,to[0],to[1]-dy*.30,*to);c.drawPath(p);c.circle(*at,radius,stroke=1,fill=0)
def bubble(name,cx,cy,r,kind=None):
 c.setStrokeGray(0);c.setLineWidth(.7);c.circle(cx,cy,r,stroke=1,fill=0)
 proj,d=vector(name,(cx-r*.71,cy-r*.68,r*1.42,r*1.36))
 if kind=='pin':arrow(proj([0,22,13]),proj([0,6,13]),1.4)
 elif kind=='wedge':arrow(proj([0,-9.8,21]),proj([0,-9.8,9]),1.4)
 return proj,d

def lockpage(step,title,main,pin,wedge,anchor,long=False):
 start(title,step)
 center(160,738,'Pinne først',11);center(433,738,'Kile etterpå',11)
 center(160,716,'4×',12);center(433,716,'4× · '+('16 mm' if long else '9,5 mm'),12)
 bubble(pin,160,590,113,'pin');bubble(wedge,433,590,113,'wedge')
 if main.startswith('technical:'):
  proj,d=technical(main.split(':')[1],(109,110,377,307));at=proj(d['anchors'][anchor]['assembled_center_uv'])
  prefix=anchor.split('_')[0]+'_'
  for key,value in d['anchors'].items():
   if key.startswith(prefix) and key.endswith('_pin'):
    q=proj(value['assembled_center_uv']);c.setStrokeGray(0);c.setLineWidth(.7);c.circle(*q,6,stroke=1,fill=0)
 else:
  proj,d=vector(main,(109,110,377,307));at=proj(d['anchors'][anchor]['center_mm'])
 leader(at,(160,477))
 para('Gjer dette ved alle fire festa. Pinnane glir sidevegs; kilane kjem inn frå linsesida.',M,83,CW,9,13)
 text(M,62,'Delane skal gli utan kraft. Trekkflikane skal vere frie.',9)
 end()

def tick(x,y,s,w=CW):
 c.setStrokeGray(0);c.setLineWidth(.7);c.rect(x,y-1,7,7,stroke=1,fill=0);return para(s,x+17,y,w-17,9.5,14)-15

def profile(name,cx,top,label,length):
 p=R/'vector'/(name+'.json');USED.add(str(p.relative_to(R)));d=json.loads(p.read_text());x0,y0,x1,y1=d['bbox'];sc=72/25.4*2;ox=cx-(x0+x1)*sc/2;oy=top-y1*sc
 c.setStrokeGray(0);c.setLineJoin(1);c.setLineWidth(.6)
 for g in d['groups']:
  p=c.beginPath()
  for i,(a,b) in enumerate(g['xy']):
   if i:p.lineTo(ox+a*sc,oy+b*sc)
   else:p.moveTo(ox+a*sc,oy+b*sc)
  c.drawPath(p)
 yy=oy+y0*sc;xx=cx+32;line((xx,yy),(xx,top),.5);line((xx-3,yy),(xx+3,yy),.5);line((xx-3,top),(xx+3,top),.5)
 text(xx+7,(yy+top)/2-3,length,9);center(cx,top+20,label,10,True)

start('ENTROPI')
text(M,H-94,'ENTROPI',59,True);text(M,H-124,'R04 / USB18',13)
technical('assembled',(24,176,W-48,508))
text(M,93,'Montering',16)
text(M,69,'Prototype · Kontroller kortinnføringa på side 7.',8.5)
end()

start('Hovuddelar',caption='1× av kvar')
part('part_02_multigrip_carrier',(M,412,275,280),1,'02 · Berar')
part('part_03_MB_keeper_left',(350,432,190,260),1,'03 · Bakhaldar L')
part('part_04_MB_keeper_right',(350,128,190,260),1,'04 · Bakhaldar R')
part('part_05_sensor_yoke_left',(M,128,132,250),1,'05 · Bøyle L')
part('part_06_sensor_yoke_right',(197,128,132,250),1,'06 · Bøyle R')
text(M,66,'L og R er sett frå linsesida.',9)
end()

start('Pinnar og kilar')
part('part_20_keeper_L_down_pin',(M,473,240,220),8,'20 / 30 · Pinnar')
part('wedge_short_iso',(335,473,190,220),8,'20 / 30 · Korte kilar, 9,5 mm')
c.setStrokeGray(0);c.setLineWidth(.65);c.roundRect(M,131,CW,292,10,stroke=1,fill=0)
text(M+15,397,'Valfri batteriramme',11)
part('part_01_bank_cradle',(M+14,160,202,202),1,'01')
part('part_20_keeper_L_down_pin',(278,160,124,202),4,'10 · pinne')
part('wedge_long_iso',(429,160,102,202),4,'10 · 16 mm')
text(M,77,'Kamerarigg: 21 printdelar. Med batteriramme: 30.',9.5)
text(M,56,'Alle pinnane har same form. Dei lange kilane høyrer berre til batteriramma.',8)
end()

start('Elektronikk',caption='2× ESP32-CAM + 2× ESP32-CAM-MB + 2× microUSB-kabel')
proj,d=technical('pair_front',(26,333,W-52,370))
center(169,322,'L',15,True);center(430,322,'R',15,True)
center(W/2,292,'Frå linsesida · motsette kort · same 18° vriding',10)
technical('mb_only',(325,101,215,160));text(70,208,'2× microUSB',14)
para('Linseaksane er parallelle. Tilpass biletrotasjon og stereokalibrering til denne orienteringa.',70,174,220,10,15)
text(342,83,'USB-basen under kamerakortet',8)
end()

start('Dette skal stå att',caption='02 · Beraren utan trestøtter')
center(150,725,'Låsefeste og pinnehol',10);center(445,725,'Kortføring og stoppar',10)
bubble('carrier_preserve_fork',150,625,80)
bubble('carrier_preserve_guide',445,625,80)
proj,d=vector('carrier_preserve_front',(M,195,CW,340))
leader(proj(d['anchors']['pin_aperture']['point_mm']),(150,545),7)
leader(proj(d['anchors']['guide_stop']['point_mm']),(445,545),7)
para('Alt som er teikna her, er del av beraren. Bevar også dei tynne staga, skinnene og stopparane.',M,176,CW,10,15,True)
para('Lat printet bli kaldt. Klipp støttegreinene i små bitar og støtt festet medan du tek laus kontaktpunkta. Reins hol og spor.',M,122,CW,9.5,15)
text(M,63,'Ved byte av berre 02: ta vare på resten av delane.',9)
end()

start('Prøv låsen',caption='Utan elektronikk · Ta låsen frå kvarandre igjen før montering')
profile('wedge_short_profile',102,665,'Kamera · 9,5 mm','9,5 mm')
profile('wedge_long_profile',300,665,'Batteriramme · 16 mm','16 mm')
vector('part_20_keeper_L_down_pin',(422,537,123,135));center(484,517,'Same pinne ved alle festa',8)
text(M,477,'Kilane er viste i same målestokk, 2:1.',9)
for cx,label,name,kind in [(119,'1 · Pinne','lock_keeper_pin_stage','pin'),(298,'2 · Kort kile','lock_keeper_wedge_stage','wedge'),(477,'3 · På plass','lock_keeper_seated',None)]:
 center(cx,423,label,10,True);bubble(name,cx,318,77,kind)
para('Prøv éin bakhaldar mot beraren. Pinnen skal gli gjennom begge sidene; kilen skal gli inn i tverrsporet. Ikkje vri eller bruk makt.',M,186,CW,10,15)
para('Ta ut kilen, så pinnen. Fjern bakhaldaren igjen. Begge bakhaldarane skal vere ute før korta blir plasserte.',M,113,CW,9.5,15,True)
end()

start('Kontroller korta')
proj,d=technical('seated',(34,297,W-68,391))
para('Korta skal kome fritt på plass.',M,248,CW,13,18,True)
para('Teikninga viser sluttplasseringa. Rett innføring bakfrå kolliderer i CAD. Ein annan innføringsveg er ikkje verifisert.',M,217,CW,10,15)
para('Hald fram berre når dei faktiske korta kjem fritt på plass. Ikkje press eller bøy dei.',M,155,CW,10,15,True)
tick(M,89,'USB er fråkopla. Berre korta og den reine beraren er lagde fram.')
end()

start('Deloversikt')
proj,d=technical('exploded',(26,163,W-52,541))
for key,pid,edge_uv,label_uv in [
 ('02_multigrip_carrier','02',(0.3401902375,0.6540315105),(0.270,0.750)),
 ('03_MB_keeper_left','03',(0.6173965769,0.8300218419),(0.650,0.910)),
 ('04_MB_keeper_right','04',(0.9290352152,0.4436755571),(0.970,0.465)),
 ('05_sensor_yoke_left','05',(0.2013050278,0.5595060779),(0.130,0.650)),
 ('06_sensor_yoke_right','06',(0.4893798760,0.1720480482),(0.510,0.085))
]:tag(proj(edge_uv),pid,proj(label_uv)-proj(edge_uv))
text(M,83,'Eksploderinga viser delsamanheng, ikkje ein innføringsveg.',9)
end()

start('Bakhaldarar',1)
text(375,H-66,'03 + 04',12);text(375,H-84,'1× av kvar',10);text(M,H-105,'Bakside',9)
technical('keepers_rear',(26,154,W-52,516),True)
para('Set inn begge bakhaldarane medan du støttar korta. Vent med bøylar, pinnar, kilar, kablar og batteriramme.',M,109,CW,10,15)
text(M,67,'Føtene skal støtte MB-korta utan å bøye dei.',9)
end()

lockpage(2,'Lås bakhaldarane','technical:keepers_locked','lock_keeper_pin_stage','lock_keeper_wedge_stage','20_keeper_L_up_pin')

start('Linsebøylar',3)
text(383,H-66,'05 + 06',12);text(383,H-84,'1× av kvar',10)
proj,d=technical('yokes',(20,144,W-40,415),True)
c.setStrokeGray(0);c.setLineWidth(.7);c.circle(430,643,100,stroke=1,fill=0)
technical('sensor_contact',(354,570,152,148))
at=proj(d['anchors']['DETAILED_R_OV2640_square_camera_body']['assembled_center_uv']);leader(at,(430,543),23)
text(54,664,'Linsa og flekskabelen skal vere frie.',10)
text(54,642,'Kontaktflatene kviler på sensorskuldrene.',9)
para('Legg bøylane på dei faste stopparane. Ikkje trekk dei ned med kilane.',M,94,CW,10,15)
text(M,66,'Berar og MB er utelatne i detaljen. Bøylen er løfta for å vise kontakten.',8)
end()

lockpage(4,'Lås linsebøylane','technical:assembled','yoke_pin_stage','yoke_wedge_stage','30_yoke_L_up_pin')

start('USB og test',5)
text(M,H-104,'Bakside',9);text(418,H-66,'2× USB',12)
proj,d=technical('rear_usb',(25,252,W-50,438))
p=R/'vector/usb-insertion-guides.json';USED.add(str(p.relative_to(R)))
for a in json.loads(p.read_text())['arrows']:arrow(proj(a['arrow_start_uv']),proj(a['arrow_end_uv']))
para('Støtt USB-basen. Før kvar plugg rett inn langs pila og hald i plugghuset. Hald kablane fri frå låsar og ramme.',M,198,CW,10,15)
y=150
for s in ['Begge kamera gir stabile bilete.','Rett orientering og venstre/høgre-val.','Ingen kabelpress eller brot ved lett kabelrørsle.']:y=tick(M,y,s)
text(M,57,'Plugg og kabel er nominelle volum. Prøv dei faktiske kablane.',8)
end()

start('Valfri batteriramme',6)
text(388,H-66,'01',12);text(388,H-84,'1×',13)
proj,d=technical('bank_placement',(M,202,CW,486))
a=d['anchors']['01_bank_cradle'];offset=np.array([.05,.28]);arrow(proj(np.array(a['shown_center_uv'])+offset),proj(np.array(a['assembled_center_uv'])+offset))
para('Legg banken i ramma. Før ramma fram frå baksida med kablane frie og alle fire låsane opne.',M,131,CW,10,15)
text(M,88,'Powerbank vist som nominelt volum, 94 × 62 × 15 mm. Prøv faktisk passform.',8.5)
text(M,62,'Utan batteriramme: gå til side 16.',9)
end()

lockpage(7,'Lås batteriramma','technical:bank_locked','frame_pin_stage','lock_frame_wedge_stage','10_frame_1_pin',True)

start('Kontroller')
technical('assembled',(25,302,W-50,426))
y=259
for s in ['8 pinnar + 8 korte kilar. Med batteriramme: 12 pinnar + 12 kilar.','Bøylane ligg på stopparane. Linser, kort og kablar er utan press.','Pluggane sit heilt inne. Trekkflikane er tilgjengelege.','Begge kamera gir stabile bilete etter montering.']:y=tick(M,y,s)
line((M,85),(270,85),.5);line((325,85),(W-M,85),.5);text(M,68,'Dato',8);text(325,68,'Avvik / merknad',8)
end()

start('Opne og kontrollere')
text(M,735,'Kople frå USB. Støtt delane.',11)
proj,d=bubble('lock_keeper_wedge_stage',160,578,109)
arrow(proj([0,-9.8,10]),proj([0,-9.8,23]))
proj,d=bubble('lock_keeper_pin_stage',433,578,109)
arrow(proj([0,6,13]),proj([0,22,13]))
center(160,448,'Kile ut først',10);center(433,448,'Pinne ut etterpå',10)
para('Batteriramme → linsebøylar → bakhaldarar. Støtt elektronikken før bakhaldarane blir løyste.',M,401,CW,10,15)
entries=[('Pinne eller kile stoppar','Reins sporet og rett inn skjøten. Ikkje bruk makt.'),('Bøyle pressar på linsa eller fleks','Stopp og kontroller sensorhøgd og kontaktflater.'),('Kabel blir klemd eller biletet fell ut','Opne ramma og kontroller kabelføring og kontaktar.'),('Kortet kjem ikkje fritt ut','Stopp. Uttrekkingsvegen er heller ikkje verifisert.')]
y=336
for h,t in entries:
 text(M,y,h,10,True);para(t,M,y-19,CW,9,14);y-=55
text(M,89,'R04 USB18 / Utgåve 08 · Modellmål er nominelle.',8)
label='CAD, printfiler og kjeldegrunnlag';text(M,65,label,8);c.linkURL('https://github.com/lukketsvane/formnerd/tree/main/A1/Stereo-Multigrip-R04-USB18',(M,61,M+pdfmetrics.stringWidth(label,'Sans',8),76),relative=0,thickness=0)
end()

assert PN==N
c.save();doc=fitz.open(PDF)
for i,p in enumerate(doc):p.get_pixmap(matrix=fitz.Matrix(2.5,2.5),alpha=False).save(PAGES/f'R04_manual_{i+1:02d}.png')
errors=[r for r in TEXT if r['bbox'][0]<19 or r['bbox'][2]>W-19 or r['bbox'][1]<15 or r['bbox'][3]>H-12]
(R/'layout-checks.json').write_text(json.dumps({'page_count':len(doc),'text_outside_safe_page':errors,'all_text_runs':TEXT},indent=2,ensure_ascii=False))
(R/'contents.json').write_text(json.dumps(TITLES,indent=2,ensure_ascii=False));(R/'used-assets.json').write_text(json.dumps(sorted(USED),indent=2));(R/'scene-manifest.json').write_text(json.dumps(SCENES,indent=2))
print(json.dumps({'pdf':str(PDF),'page_count':len(doc),'bytes':PDF.stat().st_size,'layout_errors':len(errors)}))
if errors:raise ValueError('Text outside page')
