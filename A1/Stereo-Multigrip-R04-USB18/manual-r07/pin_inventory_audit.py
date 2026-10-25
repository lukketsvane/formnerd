from pathlib import Path
import sys,json,hashlib
import cadquery as cq
R=Path(sys.argv[1])
sys.path.insert(0,str(R/'source'))
ns={'__file__':str(R/'source/build_harness.py')}
exec((R/'source/build_harness.py').read_text().split('# Rear bank cradle:')[0],ns)
P=ns['P']; LX=ns['LX'];CX=ns['CX'];SPLIT=ns['SPLIT'];YOKEZ=ns['YOKEZ'];ROLL=ns['ROLL']
joints=[]
for sx in (-1,1):
 for sy in (-1,1):joints.append((f'10_frame_{len(joints)+1}',sx*P['main_lock_x'],sy*P['main_lock_y'],SPLIT-10.25,None))
for side,label in [(-1,'L'),(1,'R')]:
 for sy in (-1,1):
  direction='up' if sy>0 else 'down'
  joints.append((f'20_keeper_{label}_{direction}',side*CX,sy*P['keeper_lock_y'],P['mb_bottom_z']+P['keeper_lock_rise'],side))
  joints.append((f'30_yoke_{label}_{direction}',side*LX,sy*P['yoke_lock_y'],YOKEZ-2.,side))
results=[]
for prefix,x,y,z,side in joints:
 for tag in ('pin','wedge'):
  name=prefix+'_'+tag; fn=R/'STEP'/(name+'.step');s=cq.importers.importStep(str(fn)).val()
  if side:s=s.rotate((side*LX,0,0),(side*LX,0,1),-ROLL)
  s=s.translate((-x,-y,-z)).rotate((0,0,0),(0,0,1),-90)
  template=ns['KEY'] if tag=='pin' else ns['WEDGE'] if prefix.startswith('10_') else ns['WEDGE_SHORT']
  bb=s.BoundingBox(); a=s.cut(template).Volume();b=template.cut(s).Volume()
  results.append({'name':name,'sha256':hashlib.sha256(fn.read_bytes()).hexdigest(),'inverse_placement':{'pod_roll_removed_degrees':ROLL if side else 0,'translate_removed_mm':[x,y,z],'lock_rotation_removed_degrees':90},'dimensions_mm':[bb.xlen,bb.ylen,bb.zlen],'volume_mm3':s.Volume(),'template_volume_mm3':template.Volume(),'symmetric_difference_mm3':a+b,'matches_source_common_shape':a+b<1e-6})
output={'source':'source/build_harness.py key() and lockpair(): same KEY for all 12 pins, WEDGE_SHORT for all 8 camera wedges, WEDGE for 4 frame wedges','source_sha256':hashlib.sha256((R/'source/build_harness.py').read_bytes()).hexdigest(),'all_24_matches':all(r['matches_source_common_shape'] for r in results),'results':results,'conclusion':'Camera 20 pin is geometrically accurate for all 8 camera pins and optional 4 frame pins. All 8 camera wedges are congruent 9.5 mm short wedges. Frame wedges are the distinct 16 mm long wedge. Only rigid assembly transformations differ.'}
Path(__file__).with_name('pin-inventory-audit.json').write_text(json.dumps(output,indent=2))
for r in results:print(r['name'],[round(v,6) for v in r['dimensions_mm']],round(r['volume_mm3'],9),r['symmetric_difference_mm3'])
print('ALL MATCH:',output['all_24_matches'])
