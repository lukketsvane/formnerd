import json
from pathlib import Path
import numpy as np
import cadquery as cq
import trimesh

HERE=Path(__file__).resolve().parent
PARTS=HERE/"parts"
QA=HERE/"qa"
d=np.load(HERE/"R10_voxel_check.npz")
front,rear=d["front"],d["rear"]
origin,pitch=d["origin"],float(d["pitch"])
zs=origin[2]+np.arange(front.shape[2])*pitch
ear_positions=[(-18,-27),(-18,27),(35,-27),(35,27)]
report={}
def ring(x,y,zmin,zmax):
    a=cq.Solid.makeCylinder(3.4,zmax-zmin,cq.Vector(x,y,zmin),cq.Vector(0,0,1))
    b=cq.Solid.makeCylinder(1.75,zmax-zmin+1,cq.Vector(x,y,zmin-.5),cq.Vector(0,0,1))
    return a.cut(b).clean()
def save(name,shape):
    if not shape.isValid() or len(shape.Solids())!=1:
        raise RuntimeError("INVALID STEP "+name)
    cq.exporters.export(shape,str(PARTS/(name+".step")))
    cq.exporters.export(shape,str(PARTS/(name+".stl")),tolerance=.05,angularTolerance=.12)
    m=trimesh.load(PARTS/(name+".stl"),force="mesh")
    if not m.is_watertight or m.volume<=0:
        raise RuntimeError("INVALID STL "+name)
    return {"z_length_mm":round(shape.BoundingBox().zlen,2),"volume_mm3":round(shape.Volume(),2)}
for i,(x,y) in enumerate(ear_positions,1):
    idx=int(round((x+4.0-origin[0])/pitch));idy=int(round((y-origin[1])/pitch))
    fidx=np.where(front[idx,idy])[0]
    ridx=np.where(rear[idx,idy])[0]
    if not len(fidx) or not len(ridx):
        raise RuntimeError("No shell geometry near ear "+str((x,y)))
    first_z=zs[fidx.min()]
    last_z=zs[ridx.max()]
    front_start=round(first_z+4.0,2)
    front_end=-4.05
    rear_start=.30
    rear_end=round(last_z-4.0,2)
    if front_end-front_start < 2 or rear_end-rear_start < 2:
        raise RuntimeError("Ear unsupported: "+str((x,y,front_start,rear_end)))
    left_name=f"P05F{i}_M3_front_spacer"
    back_name=f"P05R{i}_M3_rear_spacer"
    report[left_name]={"ear_mm":[x,y],**save(left_name,ring(x,y,front_start,front_end))}
    report[back_name]={"ear_mm":[x,y],**save(back_name,ring(x,y,rear_start,rear_end))}
coupon=cq.Workplane("YZ").box(42,20,2.6).edges("|X").fillet(2).translate((0,0,7.7)).val()
usb_c=cq.Workplane("XY").box(5,10.4,4.8).translate((0,11,7.7)).val()
usb_a=cq.Workplane("XY").box(5,14.4,7.7).translate((0,-10.7,7.7)).val()
coupon=coupon.cut(usb_c).cut(usb_a).clean()
report["T13_USB_wall_coupon"]={"measure_positions_before_print":True,**save("T13_USB_wall_coupon",coupon)}
(QA/"fitting_spacers.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("FITTINGS_READY",len(report),json.dumps(report),flush=True)
