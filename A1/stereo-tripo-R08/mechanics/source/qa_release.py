import json, hashlib, glob
from pathlib import Path
import trimesh
R=Path(__file__).resolve().parents[1]
parts=[]
for file in sorted((R/'stl').glob('*.stl')):
 mesh=trimesh.load_mesh(file)
 parts.append({'part':file.stem,'watertight':bool(mesh.is_watertight),'is_volume':bool(mesh.is_volume),'triangles':len(mesh.faces),'volume_mm3':round(mesh.volume,1),'bbox_mm':[round(i,2) for i in mesh.extents]})
collision=json.load(open(R/'verification'/'digital_collision_report.json'))
printplates=json.load(open(R/'verification'/'print_plates.json'))
report={'revision':'R08-MECH-01','parts_total':len(parts),'production_parts':sum(not i['part'].startswith('T') for i in parts),'calibration_parts':sum(i['part'].startswith('T') for i in parts),'parts':parts,'watertight_all':all(i['watertight'] for i in parts),'volumes_positive':all(i['is_volume'] for i in parts),'nominal_collision_free':bool(collision['passed']),'unintended_intersections':collision['unintended_intersections'],'print_plates':{p:{'objects':data['objects'],'within_250mm':data['bed_extent_ok'],'contains_gcode':data['gcode_included']} for p,data in printplates.items()},'tripo_h31_result':None,'production_outer_shell':False,'physical_fit_test':False,'optical_flex_test':False,'electrical_power_test':False,'bambu_slicing_complete':False,'manual_pages':13}
report['passed_as_mechanical_prototype']=report['watertight_all'] and report['nominal_collision_free'] and all(x['within_250mm'] for x in report['print_plates'].values())
(R/'verification'/'release_report.json').write_text(json.dumps(report,indent=2))
print('PASS_MECH_DIGITAL',report['passed_as_mechanical_prototype'],'TRIPO_MASTER',report['tripo_h31_result'],'PRODUCTION_RELEASE',False)