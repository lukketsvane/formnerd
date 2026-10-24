import json, math
from pathlib import Path
import numpy as np
import trimesh
from trimesh.exchange.threemf import export_3MF
R=Path(__file__).resolve().parents[1]
STL=R/'stl'; OUT=R/'print'
plates={
 '01_fit_tests':['T01_USB_wall_fit_coupon','T02_tolerance_fit_coupon'],
 '02_structural_parts':['P01_carrier_spine','P02_powerbank_open_U_cradle'],
 '03_cameras_and_controls':['P03_L_esp32_edge_sled','P03_R_esp32_edge_sled','P04_L_removable_PCB_retainer','P04_R_removable_PCB_retainer','P05_L_detachable_lens_turret','P05_R_detachable_lens_turret','P06_top_shutter_button','P07_shutter_retainer_washer']
}
results={}
for plate,names in plates.items():
 scene=trimesh.Scene(); cursor=[10.0,12.0]; rowh=0.0; placed=[]
 for name in names:
  mesh=trimesh.load_mesh(STL/(name+'.stl')).copy()
  assert mesh.is_watertight and mesh.is_volume,name
  if name=='P06_top_shutter_button':mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
  elif name=='T01_USB_wall_fit_coupon':mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
  else:mesh.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2,[1,0,0]))
  mesh.apply_translation([-mesh.bounds[0][0],-mesh.bounds[0][1],-mesh.bounds[0][2]])
  bbox=mesh.extents.copy()
  if cursor[0]+bbox[0]>245:
   cursor[0]=10.0;cursor[1]+=rowh+10.0;rowh=0.0
  mesh.apply_translation([cursor[0],cursor[1],0])
  assert all(mesh.bounds[1][i]<=250 for i in [0,1]),(plate,name,mesh.bounds)
  scene.add_geometry(mesh,geom_name=name,node_name=name)
  placed.append({'part':name,'position_mm':[round(cursor[0],2),round(cursor[1],2)],'bbox_xyz_mm':[round(i,2) for i in bbox]})
  cursor[0]+=bbox[0]+10.0;rowh=max(rowh,bbox[1])
 for a in range(len(scene.geometry)):
  A=scene.geometry[names[a]]
  for b in range(a+1,len(names)):
   B=scene.geometry[names[b]]
   assert not (np.all(A.bounds[0][:2]<B.bounds[1][:2]) and np.all(B.bounds[0][:2]<A.bounds[1][:2])),(names[a],names[b])
 data=export_3MF(scene)
 path=OUT/(plate+'.3mf');path.write_bytes(data)
 t=trimesh.load(path,force='scene');assert len(t.geometry)==len(names),(path,len(t.geometry),len(names))
 results[plate]={'file':str(path.name),'parts':placed,'objects':len(t.geometry),'bed_extent_ok':True,'gcode_included':False,'slicer_verification':False}
 print(plate,len(names),'objects',len(data),'bytes',flush=True)
with open(R/'verification'/'print_plates.json','w') as f:json.dump(results,f,indent=2)