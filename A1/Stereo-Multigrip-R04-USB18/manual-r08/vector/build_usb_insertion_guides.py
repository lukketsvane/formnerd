from pathlib import Path
import json,math,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
import cadquery as cq
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape
R=Path(__file__).resolve().parents[1]
S=Path(sys.argv[1]).resolve()
F=R/'figures/technical_rear_usb.json'
d=json.loads(F.read_text());p=json.loads((S/'source/parameters.json').read_text())
A=np.array([a['shown_center_mm']+[1] for a in d['anchors'].values()]);B=np.array([a['shown_center_uv'] for a in d['anchors'].values()]);M=np.linalg.lstsq(A,B,rcond=None)[0]
residual=float(np.linalg.norm(A@M-B,axis=1).max());assert residual<1e-6
roll=math.radians(p['module_roll_deg']);rot=np.array([[math.cos(roll),-math.sin(roll),0],[math.sin(roll),math.cos(roll),0],[0,0,1]])
project=lambda q:(np.r_[q,1]@M).tolist()
rows=[]
for side,label in [(-1,'L'),(1,'R')]:
 lx=side*p['baseline']/2;cx=side*(p['baseline']/2-p['lens_offset']);inward=-side;face=cx+inward*(p['camera_pcb_w']/2-1+2.75);z=p['mb_bottom_z']+p['mb_pcb_t']+1.2
 pod=lambda q:rot@(np.array(q)-[lx,0,0])+[lx,0,0]
 mouth=pod([face,0,z]);body=pod([face+inward*p['usb_plug_projection']/2,0,z]);axis=rot@np.array([-inward,0,0]);start=mouth-axis*p['usb_insertion_travel']
 rows.append({'side_from_lens_front':label,'source_usb_socket':f'REF_{label}_USB_socket','source_nominal_plug':f'USB_{label}_plug_body','socket_mouth_center_mm':mouth.tolist(),'socket_mouth_uv':project(mouth),'plug_body_center_mm':body.tolist(),'plug_body_center_uv':project(body),'insertion_unit_vector_mm':axis.tolist(),'approach_travel_mm':p['usb_insertion_travel'],'arrow_start_mm':start.tolist(),'arrow_end_mm':mouth.tolist(),'arrow_start_uv':project(start),'arrow_end_uv':project(mouth),'guide_offset_mm':[0,0,0]})
for row in rows:
 socket_stl=S/'STL'/(row['source_usb_socket']+'.stl');shape=TopoDS_Shape();assert StlAPI_Reader().Read(shape,str(socket_stl));distance=cq.Vertex.makeVertex(*row['socket_mouth_center_mm']).distance(cq.Shape.cast(shape));assert distance<1e-5
 row['mouth_distance_to_exported_socket_STL_mm']=distance;row['socket_STL_sha256']=hashlib.sha256(socket_stl.read_bytes()).hexdigest()
q={'name':'USB insertion axis guides for existing detailed rear_usb figure','source_figure_json':'figures/technical_rear_usb.json','source_figure_json_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'source_files':['source/build_harness.py:pod','source/build_harness.py:USB plug body and continuous insertion keepout','source/build_harness.py:REF_L_USB_socket / REF_R_USB_socket','source/parameters.json'],'coordinate_convention':'Millimetres in R04 assembly coordinates. ImageUV origin bottom-left. L/R viewed from lens front, so positions reverse on the rear view.','projection_affine_mm_homogeneous_to_uv':M.tolist(),'projection_fit_anchors':len(A),'projection_max_uv_residual':residual,'arrows':rows,'qualification':'Nominal socket/plug geometry and verified 20mm approach direction. Arrows indicate straight socket axes, not the physical connector engagement depth. Actual plug size, seating and cable fit are unverified. Existing image remains the seated reference pose; these guides do not depict the plugs as translated or prove physical fit.'}
(R/'vector/usb-insertion-guides.json').write_text(json.dumps(q,indent=2,ensure_ascii=False))
im=Image.open(R/'figures/technical_rear_usb.png').convert('RGB');w,h=im.size;draw=ImageDraw.Draw(im)
for a in rows:
 x,y=np.array(a['arrow_start_uv'])*[w,h];u,v=np.array(a['arrow_end_uv'])*[w,h];y=h-y;v=h-v;delta=np.array([u-x,v-y]);delta/=np.linalg.norm(delta);normal=np.array([-delta[1],delta[0]]);tip=np.array([u,v]);tail=np.array([x,y]);neck=tip-delta*30
 draw.line([tuple(tail),tuple(neck)],fill='white',width=18);draw.line([tuple(tail),tuple(neck)],fill='black',width=9)
 pts=[tuple(tip),tuple(tip-delta*38+normal*14),tuple(tip-delta*38-normal*14)];draw.polygon(pts,fill='black',outline='white',width=4)
 draw.text((x+12,y+8),a['side_from_lens_front'],fill='black')
im.save(R/'vector/usb-insertion-guides-qa.png')
print(json.dumps({'arrows':len(rows),'projection_fit_anchors':len(A),'max_uv_residual':residual,'output':str(R/'vector/usb-insertion-guides.json')}))
