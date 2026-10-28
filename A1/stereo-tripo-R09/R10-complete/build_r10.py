import json
import hashlib
from pathlib import Path
import numpy as np
import trimesh
import cadquery as cq
from scipy.ndimage import gaussian_filter, distance_transform_edt, binary_fill_holes
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
R09 = HERE.parent
PARTS = HERE / "parts"
QA = HERE / "qa"
REVIEW = HERE / "review"
for folder in (PARTS, QA, REVIEW):
    folder.mkdir(parents=True, exist_ok=True)
PITCH = 0.52
BATTERY_CENTER_X = 3.6
STEREO_X = (-38.163, 38.163)
EARS = [(-18, -27), (-18, 27), (35, -27), (35, 27)]
SPLIT_Z = -1.2
WALL = 2.8

def box(w, h, d, x, y, z):
    return cq.Workplane("XY").box(w, h, d).translate((x, y, z)).val()

def cyl(r, x, y, z0, z1):
    return cq.Solid.makeCylinder(r, z1-z0, cq.Vector(x,y,z0), cq.Vector(0,0,1))

def fuse(items):
    r = items[0]
    for v in items[1:]:
        r = r.fuse(v)
    return r.clean()

def export_cad(name, shape):
    if not shape.isValid() or len(shape.Solids()) != 1 or shape.Volume() <= 1:
        raise RuntimeError("CAD solid invalid: " + name)
    cq.exporters.export(shape, str(PARTS / (name + ".step")))
    cq.exporters.export(shape, str(PARTS / (name + ".stl")), tolerance=0.08, angularTolerance=0.16)
    mesh = trimesh.load(PARTS/(name+".stl"),force="mesh")
    if not mesh.is_watertight:
        raise RuntimeError("STL not watertight: " + name)
    return {"volume_mm3": round(shape.Volume(),1), "bounds_mm":np.round(mesh.bounds,2).tolist(),"watertight":True}

rail_center_x = -0.9
battery_elements = [
    box(89, 2.0, 6.6, rail_center_x, -32.7, 2.1),
    box(89, 2.0, 6.6, rail_center_x, 32.7, 2.1),
    box(2.0, 66.0, 5.2, -44.8, 0.0, 1.5)
]
for x,y in EARS:
    battery_elements.append(cyl(3.75,x,y,-1.2,.25))
    battery_elements.append(box(7.0,9.0,1.45,x,-30 if y<0 else 30,-.475))
battery_holder=fuse(battery_elements)
for x,y in EARS:
    battery_holder=battery_holder.cut(cyl(1.7,x,y,-2,2))
battery_holder=battery_holder.clean()
part_qa={"H12_R10_centered_Linocell_U_cage":export_cad("H12_R10_centered_Linocell_U_cage",battery_holder)}

original_npz = np.load(R09 / "cad" / "outer_volume_grid.npz")
original = original_npz["occupancy"][:,:,::-1].astype(bool)
orig = np.array(original_npz["origin"],dtype=float)
native_nz = original.shape[2]
padxy,padfront,padrear = 12,29,10
original = np.pad(original, ((padxy,padxy),(padxy,padxy),(padfront,padrear)), constant_values=False)
origin = np.array([orig[0]-padxy*PITCH, orig[1]-padxy*PITCH, -orig[2]-(native_nz-1)*PITCH-padfront*PITCH])
nx,ny,nz = original.shape
xx = origin[0]+np.arange(nx)*PITCH
yy = origin[1]+np.arange(ny)*PITCH
zz = origin[2]+np.arange(nz)*PITCH
X=xx[:,None]
Y=yy[None,:]
Z=zz[None,None,:]

def xy_round_rect(cx,cy,w,h,r):
    ax=np.abs(X-cx)-(w/2-r)
    ay=np.abs(Y-cy)-(h/2-r)
    d=np.hypot(np.maximum(ax,0),np.maximum(ay,0))+np.minimum(np.maximum(ax,ay),0)-r
    return d<=0

def block(cx,cy,w,h,r,z0,z1):
    return xy_round_rect(cx,cy,w,h,r)[:,:,None] & (Z>=z0)&(Z<=z1)

bank=block(BATTERY_CENTER_X,0,94,62,5.3,.4,15.4)
left=block(-26.5,4,40.5,27,1.2,-24.65,-4.15)
right=block(26.5,4,40.5,27,1.2,-24.65,-4.15)
hardware=bank|left|right
holder_shapes = {
    "H11_existing":R09 / "harness" / "stl" / "H11_dual_ESP32CAM_MB_harness.stl",
    "H12_relocated":PARTS / "H12_R10_centered_Linocell_U_cage.stl"
}
holder_occ=np.zeros_like(original)
for name,filename in holder_shapes.items():
    mesh=trimesh.load(filename,force="mesh")
    vx=mesh.voxelized(PITCH).fill()
    inds=np.rint((vx.points-origin)/PITCH).astype(np.int32)
    inds=inds[((inds>=0)&(inds<np.array(original.shape))).all(axis=1)]
    holder_occ[inds[:,0],inds[:,1],inds[:,2]]=True
    print("HOLDER",name,"voxels",len(inds),flush=True)

project=original.any(axis=2)
nearest=distance_transform_edt(~project,return_indices=True)[1]
first=original.argmax(axis=2)
last=nz-1-original[:,:,::-1].argmax(axis=2)
front0=origin[2]+first*PITCH
back0=origin[2]+last*PITCH
front0[~project]=front0[tuple(nearest[:,~project])]
back0[~project]=back0[tuple(nearest[:,~project])]
front0=gaussian_filter(front0,sigma=2.7)
back0=gaussian_filter(back0,sigma=2.7)
board_xy=(left|right).any(axis=2)
bank_xy=bank.any(axis=2)
holder_xy=holder_occ.any(axis=2)
dist_boards=distance_transform_edt(~board_xy)*PITCH
dist_bank=distance_transform_edt(~bank_xy)*PITCH
front=np.minimum(front0, -27.6+0.52*dist_boards)
back=np.maximum(back0,18.3-0.42*dist_bank)
front=gaussian_filter(front,sigma=2.0)
back=gaussian_filter(back,sigma=2.0)
front[board_xy]=np.minimum(front[board_xy],-27.55)
back[bank_xy]=np.maximum(back[bank_xy],18.3)
outline=project| (distance_transform_edt(~(board_xy|bank_xy|holder_xy))*PITCH<=3.0)
outline=gaussian_filter(outline.astype(np.float32),sigma=1.65)>.38
outline=binary_fill_holes(outline)
solid=outline[:,:,None]&(Z>=front[:,:,None])&(Z<=back[:,:,None])
needed=distance_transform_edt(~(hardware|holder_occ),sampling=PITCH)<=WALL
solid=(gaussian_filter(solid.astype(np.float32),sigma=.8)>.44)|needed
inner=distance_transform_edt(solid,sampling=PITCH)>WALL
shell=solid&~inner
shell=shell&~(distance_transform_edt(~(hardware|holder_occ),sampling=PITCH)<.9)
print("VOLUME",int(solid.sum()),int(shell.sum()),"shell-hardware",int(np.count_nonzero(shell&hardware)),"shell-holders",int(np.count_nonzero(shell&holder_occ)),flush=True)

for cx in STEREO_X:
    lens_cut=((X-cx)**2+(Y-4)**2<=4.65**2)[:,:,None] & (Z<=-17.0)
    shell &= ~lens_cut
usb_c=(X>=49.6)[:,:,None]&(np.abs(Y-11.0)<=5.2)[:,:,None]&(np.abs(Z-7.7)<=2.4)
usb_a=(X>=49.6)[:,:,None]&(np.abs(Y+10.7)<=7.2)[:,:,None]&(np.abs(Z-7.7)<=3.85)
shell &= ~(usb_c|usb_a)
button_cut=((X[:,:,None]+36.0)**2+(Z+6.0)**2<=5.35**2)&(Y[:,:,None]>=28.0)
shell &= ~button_cut
screw_holes=np.zeros_like(shell)
for x,y in EARS:
    screw_holes|=((X-x)**2+(Y-y)**2<=1.8**2)[:,:,None] & (Z>=-16.0)&(Z<=24.0)
shell &= ~screw_holes
front_half=shell&(Z<=SPLIT_Z)
rear_half=shell&(Z>SPLIT_Z)

def meshify(occ,name):
    iso=gaussian_filter(np.pad(occ.astype(np.float32),2),sigma=.48)
    v,f,_,_=marching_cubes(iso,.47,spacing=(PITCH,PITCH,PITCH))
    v+=origin-2*PITCH
    mesh=trimesh.Trimesh(vertices=v,faces=f,process=True)
    mesh.fix_normals()
    mesh.export(PARTS/(name+".stl"))
    if not mesh.is_watertight or mesh.volume<=0:
        raise RuntimeError("Shell invalid: "+name)
    return mesh

front_mesh=meshify(front_half,"P01_R10_Tripo_front_shell")
rear_mesh=meshify(rear_half,"P02_R10_Tripo_rear_shell")
for name,mesh in [("P01_R10_Tripo_front_shell",front_mesh),("P02_R10_Tripo_rear_shell",rear_mesh)]:
    part_qa[name]={"watertight":mesh.is_watertight,"volume_mm3":round(mesh.volume,1),"faces":len(mesh.faces),"bounds_mm":np.round(mesh.bounds,2).tolist(),"format":"mesh STL, not NURBS"}

for side,cx in (("L",STEREO_X[0]),("R",STEREO_X[1])):
    ix=np.argmin(abs(xx-cx));iy=np.argmin(abs(yy-4))
    front_at=float(front[ix,iy])
    shank=cyl(4.30,cx,4,front_at-.1,front_at+2.8).cut(cyl(3.7,cx,4,front_at-1,front_at+4))
    flange=cyl(7.25,cx,4,front_at-1.8,front_at+.05).cut(cyl(3.7,cx,4,front_at-2,front_at+4))
    part_qa["P03_R10_lens_bezel_"+side]=export_cad("P03_R10_lens_bezel_"+side,shank.fuse(flange).clean())

button = cq.Solid.makeCylinder(4.85,2.0,cq.Vector(-36,35,-6),cq.Vector(0,1,0)).fuse(
    cq.Solid.makeCylinder(3.0,6.5,cq.Vector(-36,28.5,-6),cq.Vector(0,1,0))).clean()
part_qa["P04_R10_trigger_cap"]=export_cad("P04_R10_trigger_cap",button)

qa={
 "revision":"ENTROPI-STEREO-R10-development",
 "source":"R09 Tripo H3.1 master via previously verified silhouette voxel reconstruction",
 "master_sha256":hashlib.sha256((R09/"tripo"/"ENTROPI_R09_H31_master.glb").read_bytes()).hexdigest(),
 "units":"mm","pitch_mm":PITCH,"surface_source":"outer_volume_grid.npz",
 "battery_mm":[94,62,15],"battery_center_x_mm":BATTERY_CENTER_X,
 "bank_right_port_face_x_mm":BATTERY_CENTER_X+47,
 "nominal_inner_usb_wall_x_mm":BATTERY_CENTER_X+47+.45,
 "board_stereo_baseline_mm":76.326,"MB_depth_assumed_mm":20.5,
 "parts":part_qa,
 "test_shell_hardware_voxel_overlap":int(np.count_nonzero(shell&hardware)),
 "test_shell_harness_voxel_overlap":int(np.count_nonzero(shell&holder_occ)),
 "printable_geometry_only":True,
 "caveats":["lens-focal-axis-to-Tripo-surface not physically validated","USB-A/C Y and Z positions nominal, not measured","outer shell and front graphics approximate Tripo form, not class-A NURBS","0.52 mm voxel resolution cannot certify 0.45 mm connector clearance","screw channels nominal and not physically tested","shell fit with H11/H12 and cable routing needs physical test","no electrical assembly tested"]
}
(QA/"R10_geometry_report.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False),encoding="utf-8")
np.savez_compressed(HERE/"R10_voxel_check.npz",shell=shell,front=front_half,rear=rear_half,hardware=hardware,holder=holder_occ,origin=origin,pitch=PITCH)
print("R10_READY",json.dumps({"parts":list(part_qa),"faces":[len(front_mesh.faces),len(rear_mesh.faces)],"shell_hardware_overlap":qa["test_shell_hardware_voxel_overlap"],"shell_harness_overlap":qa["test_shell_harness_voxel_overlap"]}),flush=True)
