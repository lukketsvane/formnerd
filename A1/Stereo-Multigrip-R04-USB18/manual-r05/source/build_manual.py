from pathlib import Path
import json, math, re, hashlib
import numpy as np
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepLib import BRepLib
from cadquery.occ_impl.exporters.svg import makeSVGedge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parent
for p in ['figures','pages','cache']:(OUT/p).mkdir(exist_ok=True)
P=json.loads((ROOT/'source/parameters.json').read_text())
W,H=A4
FONT=str(Path(__file__).parent/'fonts/DejaVuSans.ttf')
BOLD=str(Path(__file__).parent/'fonts/DejaVuSans-Bold.ttf')
pdfmetrics.registerFont(TTFont('Sans',FONT))
pdfmetrics.registerFont(TTFont('Bold',BOLD))
PRINT={p.stem:cq.importers.importStep(str(p)).val() for p in (ROOT/'STEP').glob('*.step') if re.match(r'^\d\d_',p.name)}
REF={}
def box(w,h,d,x=0,y=0,z=0,r=0):
 q=cq.Workplane('XY').box(w,h,d,centered=(True,True,False)).translate((x,y,z))
 if r:q=q.edges('|Z').fillet(min(r,w/2-.01,h/2-.01))
 return q.val()
def cyl(r,h,x=0,y=0,z=0):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def pod(shape,side):return shape.rotate((side*P['baseline']/2,0,0),(side*P['baseline']/2,0,1),P['module_roll_deg'])
LX=P['baseline']/2;CX=LX-P['lens_offset'];CW=P['camera_pcb_w'];CH=P['camera_pcb_h']
MBZ=P['mb_bottom_z'];MBT=P['mb_pcb_t'];PCBZ=MBZ+MBT+P['socket_height'];PCBT=P['camera_pcb_t'];PCBTOP=PCBZ+PCBT
SHOULDER=PCBTOP+P['sensor_shoulder_above_pcb'];YOKEZ=SHOULDER+P['sensor_pad_t']
BASE=P['rear_lip'];BANKZ=BASE+.2;FRONT=BANKZ+P['bank_d']
REF['REF_power_bank']=box(P['bank_w'],P['bank_h'],P['bank_d'],z=BANKZ,r=4.1)
for side,label in [(-1,'L'),(1,'R')]:
 cx=side*CX;lx=side*LX
 shapes={'MB':box(CW,CH,MBT,cx,0,MBZ,1),'CAM':box(CW,CH,PCBT,cx,0,PCBZ,1),'SD_cage':box(13,14,2.45,lx,0,PCBTOP,.6),'sensor_carrier':box(P['sensor_carrier_w'],P['sensor_carrier_h'],1.25,lx,0,SHOULDER-1.25,.3),'lens_barrel':cyl(P['lens_barrel_d']/2,P['lens_projection'],lx,0,SHOULDER),'lens_glass':cyl(1.7,.15,lx,0,SHOULDER+P['lens_projection']),'flex':box(9,5,.2,lx-side*8.6,0,PCBTOP+2.5),'flex_socket':box(2.4,17,1.8,cx-side*5,0,PCBTOP,.3),'USB_socket':box(5.5,7.5,2.4,cx-side*(CW/2-1),0,MBZ+MBT,.4)}
 for sy in [-1,1]:shapes[f'socket_{sy}']=box(20.4,2.5,P['socket_height'],cx+side*3,sy*10.9,MBZ+MBT,.4)
 for n,s in shapes.items():REF[f'REF_{label}_{n}']=pod(s,side)
 face=cx-side*(CW/2-1+2.75);depth=P['usb_plug_projection'];usbz=MBZ+MBT+1.2
 REF[f'USB_{label}_nominal_body']=pod(box(depth,P['usb_plug_body_w'],P['usb_plug_body_h'],face-side*depth/2,0,usbz-P['usb_plug_body_h']/2,.6),side)
ALL={**PRINT,**REF}
carrier=['02_multigrip_carrier']
keepers=['03_MB_keeper_left','04_MB_keeper_right']
yokes=['05_sensor_yoke_left','06_sensor_yoke_right']
pins=sorted(n for n in PRINT if n.startswith(('20_','30_')) and n.endswith('_pin'))
wedges=sorted(n for n in PRINT if n.startswith(('20_','30_')) and n.endswith('_wedge'))
frame=['01_bank_cradle']
framepins=sorted(n for n in PRINT if n.startswith('10_') and n.endswith('_pin'))
framewedges=sorted(n for n in PRINT if n.startswith('10_') and n.endswith('_wedge'))
electronics=[n for n in REF if n.startswith(('REF_L_','REF_R_'))]
assembled=carrier+keepers+yokes+pins+wedges+electronics
SCENES=[]
def unit(a):
 a=np.array(a,dtype=float);return a/np.linalg.norm(a)
def drawing(name,names,camera=(1.2,.8,2),moves=None):
 moves=moves or {}
 spec={'name':name,'parts':names,'camera':list(camera),'translations_mm':moves,'geometry_revision':'R04 USB18','hidden_edges':False}
 SCENES.append(spec)
 key=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:16]
 cache=OUT/'cache'/f'{name}-{key}.json'
 if cache.exists():return json.loads(cache.read_text())
 f=unit(camera);right=unit(np.cross([0,1,0],f));up=unit(np.cross(f,right))
 shapes=[ALL[n].translate(tuple(moves.get(n,[0,0,0]))) for n in names]
 compound=cq.Compound.makeCompound(shapes)
 alg=HLRBRep_Algo();alg.Add(compound.wrapped)
 ax=gp_Ax2(gp_Pnt(),gp_Dir(*f),gp_Dir(*right))
 alg.Projector(HLRAlgo_Projector(ax));alg.Update();alg.Hide()
 h=HLRBRep_HLRToShape(alg)
 groups=[]
 for k,obj in [('edge',h.VCompound()),('edge',h.Rg1LineVCompound()),('outline',h.OutLineVCompound())]:
  if obj.IsNull():continue
  BRepLib.BuildCurves3d_s(obj,1e-6)
  shape=cq.Shape.cast(obj)
  for e in shape.Edges():
   s=makeSVGedge(e)
   if s:
    coords=np.array([float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',s)]).reshape(-1,2)
    groups.append({'kind':k,'xy':coords.tolist()})
 pts=np.concatenate([np.array(g['xy']) for g in groups])
 data={'groups':groups,'bbox':[*pts.min(0),*pts.max(0)],'basis':[right.tolist(),up.tolist(),f.tolist()]}
 cache.write_text(json.dumps(data,separators=(',',':')))
 save_figure_svg(name,data)
 print(name,len(groups),flush=True)
 return data
def save_figure_svg(name,data):
 x0,y0,x1,y1=data['bbox'];pad=3
 paths=[]
 for g in data['groups']:
  coords=g['xy'];d='M'+' L'.join(f'{x:.5f},{-y:.5f}' for x,y in coords)
  paths.append(f'<path d="{d}" stroke-width="{.22 if g["kind"]=="outline" else .14}"/>')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-pad} {-y1-pad} {x1-x0+2*pad} {y1-y0+2*pad}"><rect x="{x0-pad}" y="{-y1-pad}" width="{x1-x0+2*pad}" height="{y1-y0+2*pad}" fill="white"/><g fill="none" stroke="black" stroke-linejoin="round" stroke-linecap="round">'+''.join(paths)+'</g></svg>'
 (OUT/'figures'/f'{name}.svg').write_text(svg)
def text(c,x,y,s,size=11,bold=False):
 c.setFont('Bold' if bold else 'Sans',size);c.setFillColorRGB(0,0,0);c.drawString(x,y,s)
def lines(c,x,y,strings,size=11,leading=17,bold=False):
 for i,s in enumerate(strings):text(c,x,y-i*leading,s,size,bold)
def header(c,page,title,sub=None):
 text(c,42,H-42,'ENTROPI',11,True);text(c,W-113,H-42,'R04 / USB18',8)
 c.setLineWidth(.6);c.line(42,H-55,W-42,H-55)
 text(c,42,H-105,f'{page:02d}',38,True);text(c,115,H-98,title,21,True)
 if sub:text(c,115,H-122,sub,10)
 footer(c,page)
def footer(c,page):
 c.setLineWidth(.5);c.line(42,43,W-42,43)
 text(c,42,28,'R04 · Monteringsutkast · Innføring av kamerakorta må avklarast',7)
 text(c,W-56,28,str(page),8,True)
def figure(c,data,rect,line=.75):
 x,y,w,h=rect;x0,y0,x1,y1=data['bbox'];scale=min(w/(x1-x0),h/(y1-y0));ox=x+(w-(x1-x0)*scale)/2-x0*scale;oy=y+(h-(y1-y0)*scale)/2-y0*scale
 c.setLineCap(1);c.setLineJoin(1);c.setStrokeColorRGB(0,0,0)
 for g in data['groups']:
  c.setLineWidth(line*(1.35 if g['kind']=='outline' else 1))
  p=c.beginPath()
  for i,(a,b) in enumerate(g['xy']):
   if i==0:p.moveTo(ox+a*scale,oy+b*scale)
   else:p.lineTo(ox+a*scale,oy+b*scale)
  c.drawPath(p)
 basis=np.array(data['basis'])
 def project(p):
  q=basis@np.array(p);return np.array([ox+q[0]*scale,oy+q[1]*scale])
 return project
def arrow(c,a,b,width=1.5,dashed=False):
 a=np.array(a,dtype=float);b=np.array(b,dtype=float);v=b-a;v/=np.linalg.norm(v);n=np.array([-v[1],v[0]])
 c.setLineWidth(width);c.setStrokeColorRGB(0,0,0)
 if dashed:c.setDash(4,3)
 c.line(*a,*(b-v*7));c.setDash()
 p=c.beginPath();p.moveTo(*b);p.lineTo(*(b-v*9+n*3.8));p.lineTo(*(b-v*9-n*3.8));p.close();c.setFillColorRGB(0,0,0);c.drawPath(p,stroke=0,fill=1)
def label(c,at,s,dx=35,dy=25):
 at=np.array(at);end=at+np.array([dx,dy]);c.setLineWidth(.55);c.line(*at,*end);c.circle(*at,1.8,fill=1,stroke=0)
 text(c,end[0]+(4 if dx>=0 else -22),end[1]-3,s,10,True)
def card(c,data,rect,title,detail):
 x,y,w,h=rect;figure(c,data,(x+5,y+37,w-10,h-42),.7);text(c,x,y+18,title,10,True);text(c,x,y+3,detail,8)
def note(c,title,body,y=110):
 c.setLineWidth(1.5);c.line(42,y+37,42,y-3);text(c,55,y+22,title,11,True);lines(c,55,y+4,body,9,14)
pdf=OUT/'ENTROPI_R04_Monteringsutkast.pdf'
c=canvas.Canvas(str(pdf),pagesize=A4,pageCompression=1)
c.setTitle('ENTROPI R04 USB18 · Monteringsutkast')
c.setAuthor('Formnerd')
cover=drawing('01_assembled',assembled,camera=(1.0,.65,2.5))
text(c,42,H-57,'ENTROPI',31,True);text(c,44,H-83,'R04 / USB18',12)
text(c,42,H-135,'MONTERINGSUTKAST',19,True)
figure(c,cover,(43,211,W-86,401),.86)
lines(c,42,166,['Tre nye hovuddelar. Åtte korte låsekilar.','Dei andre delane blir brukte om att frå R03.'],12,20)
lines(c,42,102,['18° kameravinkel · Parallelle linseaksar','Innføringa av kamerakorta er ikkje avklart. Sjå side 3.'],9,15)
footer(c,1);c.showPage()
header(c,2,'Finn delane','Byt kamerakilane. Ta vare på T-pinnane frå R03.')
items=[('02_multigrip_carrier','02 · Kameraberar','1 × ny'),('03_MB_keeper_left','03 · Bakhaldar venstre','1 × ny'),('04_MB_keeper_right','04 · Bakhaldar høgre','1 × ny')]
for i,(n,title,detail) in enumerate(items):card(c,drawing('part_'+n,[n]),(42+i*174,482,156,175),title,detail)
card(c,drawing('part_short_wedge',[wedges[0]],camera=(1,.7,2)),(42,317,156,140),'20 / 30 · Kort kile','8 × nye · 9,5 mm lange')
text(c,232,422,'FRÅ R03',12,True)
lines(c,232,398,['2 × linsebøyle: 05 og 06','8 × kamera-T-pinne: 20 / 30','1 × batteriramme: 01','4 × ramme-T-pinne: 10','4 × lang rammekile: 10'],10,22)
card(c,drawing('part_yoke',[yokes[0]]),(42,126,156,156),'05 / 06 · Linsebøyle','2 × bruk om att')
card(c,drawing('part_pin',[pins[0]]),(218,126,156,156),'T-pinne','8 til kamera + 4 til ramme')
card(c,drawing('part_long_wedge',[framewedges[0]]),(394,126,156,156),'10 · Lang kile','4 × bruk om att · 16 mm')
lines(c,42,88,['Fjern støtter frå dei nye delane, også inne i hol og kanalar.','Kople frå USB før du flyttar elektronikken. Bruk ikkje makt.'],9,15)
c.showPage()
header(c,3,'Plassering av kameraa','Sluttplassering i CAD. Innføringsvegen er ikkje avklart.')
d=drawing('03_camera_placement',carrier+electronics,camera=(1.0,.65,2.5))
p=figure(c,d,(45,232,W-90,414),.76)
note(c,'Ikkje press korta gjennom ramma.', ['Rett innføring bakfrå kolliderer i CAD. Ei skånsam innføring','må avklarast før resten av dette utkastet kan brukast.'],142)
lines(c,42,95,['Teikninga viser sluttposisjonane, ikkje ein kontrollert innføringsveg.','Elektronikken er vist som nominelle volum utan små loddekomponentar.'],8.5,15)
c.showPage()
header(c,4,'Set inn bakhaldarane','03 + 04 · Før dei inn bakfrå medan ramma er open.')
moves={n:[0,0,-50] for n in keepers}
d=drawing('04_keeper_insertion',carrier+electronics+keepers,camera=(1.5,.85,1.5),moves=moves)
p=figure(c,d,(43,209,W-86,445),.75)
for n in keepers:
 q=ALL[n].Center();arrow(c,p([q.x,q.y,q.z-43]),p([q.x,q.y,q.z-9]))
note(c,'La føtene støtte MB-kortet.', ['Bakhaldarane skal inn utan å bøye kort eller pinnar.','Vent med kablar og batteriramme til kameraa er sikra.'],115)
c.showPage()
header(c,5,'Legg på linsebøylane','05 + 06 · Bruk dei eksisterande delane frå R03.')
moves={n:[0,0,45] for n in yokes}
d=drawing('05_yoke_insertion',carrier+keepers+electronics+yokes,camera=(1.25,.8,2.0),moves=moves)
p=figure(c,d,(43,209,W-86,445),.76)
for side in [-1,1]:arrow(c,p([side*LX,0,YOKEZ+35]),p([side*LX,0,YOKEZ+7]))
note(c,'Linsa og bandkabelen skal vere frie.', ['Bøylen kviler på dei faste stopparane. Dei små kontaktflatene','skal treffe sensorskuldrene, aldri presse på sjølve linsa.'],115)
c.showPage()
header(c,6,'Skyv inn T-pinnane','8 × eksisterande kamera-T-pinne · To per festegruppe.')
vec=np.array([math.cos(math.radians(18)),math.sin(math.radians(18)),0])
moves={n:(-vec*19).tolist() for n in pins}
d=drawing('06_pin_insertion',carrier+keepers+yokes+electronics+pins,camera=(.7,.8,2.4),moves=moves)
p=figure(c,d,(43,239,W-86,410),.76)
for n in pins:
 q=np.array(ALL[n].Center().toTuple());arrow(c,p(q-vec*17),p(q-vec*3),1.1)
note(c,'Sikre bakhaldarane før du slepper korta.', ['Skyv pinnane sidevegs gjennom gaffel og tunge.','Kilesporet skal vere synleg på motsett side. Ingen vriding.'],128)
text(c,42,70,'Dei fire ytre rammepinnane blir monterte til slutt.',9)
c.showPage()
header(c,7,'Lås med korte kilar','8 × nye kamerakilar · Bruk dei korte, ikkje R03-kilane.')
moves={n:[0,0,27] for n in wedges}
d=drawing('07_wedge_insertion',assembled,camera=(.9,.75,2.5),moves=moves)
p=figure(c,d,(43,220,W-86,435),.75)
for n in wedges:
 q=np.array(ALL[n].Center().toTuple());arrow(c,p(q+[0,0,23]),p(q+[0,0,5]),1.05)
note(c,'Før kilane inn frå framsida.', ['Kilen går gjennom sporet i T-pinnen. Trekkfliken blir ståande fri.','Stopp dersom det bind. Ei kile skal ikkje presse på elektronikken.'],115)
c.showPage()
header(c,8,'Kople til USB','Begge pluggane skal gå heilt inn utan sidepress.')
plugs=['USB_L_nominal_body','USB_R_nominal_body']
moves={}
for side,label in [(-1,'L'),(1,'R')]:moves[f'USB_{label}_nominal_body']=(-side*vec*8).tolist()
d=drawing('08_USB_insertion',assembled+plugs,camera=(.5,1.15,-2.6),moves=moves)
p=figure(c,d,(43,245,W-86,397),.8)
for side,label in [(-1,'L'),(1,'R')]:
 q=np.array(REF[f'USB_{label}_nominal_body'].Center().toTuple());arrow(c,p(q-side*vec*13),p(q-side*vec*2),1.5)
note(c,'Sjå frå baksida.', ['La kablane gå ut gjennom dei opne servicevegane.','Kontroller bilete frå begge kamera før batteriramma blir sett på.'],135)
lines(c,42,86,['Teikna pluggvolum: 24 × 16 × 10 mm, førebelse mål.','Prøv dei faktiske pluggane og kabelbøyane. Ikkje tving dei inn.'],8.5,14)
c.showPage()
header(c,9,'Set på batteriramma','Valfritt bakstykke · Bruk den eksisterande R03-ramma.')
names=assembled+frame+['REF_power_bank']
moves={n:[0,0,-40] for n in frame+['REF_power_bank']}
d=drawing('09_rear_frame',names,camera=(1.4,.8,1.7),moves=moves)
p=figure(c,d,(43,260,W-86,382),.75)
arrow(c,p([0,-29,-12]),p([0,-29,15]),1.5)
note(c,'Hald dei fire ytre låsane opne.', ['Legg powerbanken i bakramma. Før ramma fram mot kameraberaren.','Alle fire gaflane og tungene skal liggje plant før du set inn pinnane.'],139)
text(c,42,75,'Kontroller at USB-kablane følgjer dei opne servicevegane.',9)
c.showPage()
header(c,10,'Lås bakramma','4 × T-pinne + 4 × lange kilar frå R03.')
names=assembled+frame+framepins+framewedges+['REF_power_bank']
moves={n:[-22,0,0] for n in framepins}
moves.update({n:[0,0,22] for n in framewedges})
d=drawing('10_frame_locks',names,camera=(1.1,.9,1.8),moves=moves)
p=figure(c,d,(43,270,W-86,371),.72)
for n in framepins:
 q=np.array(ALL[n].Center().toTuple());arrow(c,p(q+[-20,0,0]),p(q+[-3,0,0]),1.1)
for n in framewedges:
 q=np.array(ALL[n].Center().toTuple());arrow(c,p(q+[0,0,19]),p(q+[0,0,4]),1.1)
text(c,42,232,'Først pinnane sidevegs. Deretter dei lange kilane frå framsida.',10)
text(c,42,178,'KONTROLLER TIL SLUTT',11,True)
for i,s in enumerate(['Ingen kabel eller pinne er klemd.','Begge USB-pluggane sit heilt inne.','Begge kamera gir bilete. Tilpass biletrotasjon og stereokalibrering.']):
 y=151-i*22;c.setLineWidth(.8);c.rect(43,y-2,8,8);text(c,61,y,s,9)
text(c,42,64,'Dette er eit monteringsutkast. Innføring av kamerakorta må avklarast først.',8)
c.showPage();c.save()
(OUT/'scene-manifest.json').write_text(json.dumps({'geometry_revision':'R04 USB18','render_revision':'manual-r05','parts_new':carrier+keepers+wedges,'parts_reused':yokes+pins+frame+framepins+framewedges,'electronics':'Analytic nominal geometry reproduced from R04 build_harness.py; tiny header pins omitted in drawings for clarity.','scenes':SCENES},indent=2,ensure_ascii=False))
doc=fitz.open(pdf)
for i,page in enumerate(doc):
 pix=page.get_pixmap(matrix=fitz.Matrix(2.5,2.5),alpha=False)
 pix.save(OUT/'pages'/f'R04_montering_{i+1:02d}.png')
 (OUT/'pages'/f'R04_montering_{i+1:02d}.svg').write_text(page.get_svg_image(text_as_path=True))
(OUT/'README.md').write_text('''# ENTROPI R04 USB18: monteringsutkast\n\nTi separate A4-sider med vektorteikningar frå STEP-solidane i R04. Skjulte kantar er fjerna med OpenCascade HLR. Elektronikkvoluma er rekonstruerte med dei same parametrane som byggjekjelda; små kontaktpinnar er utelatne frå teikningane for lesbarheit. Geometrien og printfila er uendra.\n\nKøyr `python source/build_manual.py` frå denne mappa. Krav: Python 3, CadQuery 2.7, NumPy, ReportLab og PyMuPDF. Kjelde-STEP og parameter ligg i foreldremappa. `scene-manifest.json` bind kvar figur til del-ID, kamera og eksplodering. PDF og separate SVG/PNG-sider blir bygde frå same kjelde.\n\nInnføringa av kamerakorta er ikkje avklart. Ein kontrollert rett innføringsveg bakfrå gav kollisjon mot kameraberaren. Side 3 viser difor sluttplassering utan rørslepiler. Resten av sidefølgja er eit monteringsutkast, ikkje ei ferdig fysisk verifisert byggjerettleiing. Bakhaldarinnføringa og fleire endelege posisjonar er digitalt kontrollerte. Faktisk passform på den nye utskrifta, pluggane og kabelbøyane er ikkje stadfesta.\n''')
print(str(pdf),flush=True)
