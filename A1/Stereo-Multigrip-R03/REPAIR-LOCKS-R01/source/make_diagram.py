"""Technical assembly position sheet, derived from R03 parameters."""
from pathlib import Path
import json, math
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT.parent/"source"/"parameters.json").read_text())
W,H=1400,930
im=Image.new("RGB",(W,H),"white");d=ImageDraw.Draw(im)
fontpath=r"C:\Windows\Fonts\segoeui.ttf"
boldpath=r"C:\Windows\Fonts\segoeuib.ttf"
def F(sz,b=False):return ImageFont.truetype(boldpath if b else fontpath,sz)
ink="#111111"; grey="#798188"; highlight="#E85737"; lite="#DEE2E4"
d.text((70,40),"R03    /    PLASSERING AV HOVUDLÅSANE",font=F(34,True),fill=ink)
d.text((70,95),"Ortogonalt riss frå linsesida    |    mål i mm",font=F(22),fill=grey)
ox,oy,s=435,465,6.1
def pt(x,y):return ox+x*s,oy-y*s
def rect(x0,y0,x1,y1,outline=ink,width=4,radius=14):
 u,v=pt(x0,y1);a,b=pt(x1,y0)
 d.rounded_rectangle((u,v,a,b),radius=radius,outline=outline,width=width)
# Main cradle, perimeter and camera carrier are shown schematically.
rect(-52.3,-34.8,52.3,34.8,ink,4,24)
rect(-47,-31,47,31,lite,2,18)
for side in (-1,1):
 cx=side*(P["baseline"]/2-P["lens_offset"])
 cy=0;angle=math.radians(P["module_roll_deg"])
 corners=[]
 for dx,dy in [(-20.25,-13.5),(20.25,-13.5),(20.25,13.5),(-20.25,13.5)]:
  corners.append(pt(cx+dx*math.cos(angle)-dy*math.sin(angle),cy+dx*math.sin(angle)+dy*math.cos(angle)))
 d.line(corners+[corners[0]],fill=lite,width=5,joint="curve")
 lx=side*P["baseline"]/2; px,py=pt(lx,0)
 d.ellipse((px-35,py-35,px+35,py+35),outline=grey,width=3)
 d.ellipse((px-18,py-18,px+18,py+18),outline=lite,width=4)
# Each of the 4 outer frame locks is a symmetric joint.
labels=[(-1,1,1),(1,1,2),(-1,-1,3),(1,-1,4)]
for sx,sy,num in labels:
 x,y=sx*P["main_lock_x"],sy*P["main_lock_y"]
 px,py=pt(x,y)
 d.rounded_rectangle((px-33,py-22,px+33,py+22),radius=8,fill="white",outline=highlight,width=5)
 d.ellipse((px-7,py-7,px+7,py+7),fill=highlight)
 tx=px-29;ty=py + (-57 if sy==1 else 28)
 d.text((tx,ty),f"LÅS {num}",font=F(19,True),fill=highlight)
# Dimensions and feature legend
d.text((70,775),"FIRE YTRE LÅSAR     •     IKKJE HOL FOR KAMERAOPTIKK",font=F(19,True),fill=ink)
d.text((70,815),"Koordinatar: X = ±28,0    /    Y = ±36,4. ",font=F(18),fill=grey)
d.text((70,851),"Låsane er like. Både pinnar og kilar må monterast.",font=F(18),fill=grey)
# Vertical divider
d.line((870,140,870,855),fill=lite,width=3)
d.text((915,175),"MONTERING",font=F(27,True),fill=ink)
for y,n,heading,lines in [
 (250,"01","FØY SAMAN",["Bakre og fremre ramme.","Alle fire tappar i gaffelspora."]),
 (415,"02","SKYV INN PINNEN",["Éin T-pinne gjennom kvart","vassrett låsehol. T-hovud","på innføringssida."]),
 (630,"03","SET INN KILEN",["Éin kile frå linsesida ned","i holrommet ved enden av pinnen.","Trekkfliken må vere tilgjengeleg."])]:
 d.ellipse((915,y,975,y+60),outline=highlight,width=4)
 d.text((927,y+13),n,font=F(21,True),fill=highlight)
 d.text((993,y+0),heading,font=F(21,True),fill=ink)
 for i,l in enumerate(lines):d.text((993,y+45+i*29),l,font=F(18),fill=ink)
d.text((915,850),"Ikkje slå, lim eller tving.",font=F(20,True),fill=highlight)
out=ROOT/"MAIN-LOCK-POSITIONS.png"
im.save(out,optimize=True)
print("ILLUSTRATION",out,out.stat().st_size)
