import json,math
from pathlib import Path
import cadquery as cq
import vtk

R=Path(__file__).resolve().parents[1]
REV=R/'review'
COL={'chassis':(.43,.46,.49),'cradle':(.6,.62,.65),'tray':(.72,.74,.76),'keeper':(.64,.66,.69),'lens':(.21,.22,.24),'shutter':(.15,.16,.17),'battery':(.31,.34,.37),'pcb':(.12,.30,.27),'camera':(.07,.08,.09),'coupon':(.72,.74,.75)}
PARTS={p.stem:p for p in (R/'stl').glob('*.stl')}
PARTS.update({p.name[5:-4]:p for p in REV.glob('_ref_*.stl')})

G={
 'P01_carrier_spine':'chassis','P02_powerbank_open_U_cradle':'cradle',
 'P03_L_esp32_edge_sled':'tray','P03_R_esp32_edge_sled':'tray',
 'P04_L_removable_PCB_retainer':'keeper','P04_R_removable_PCB_retainer':'keeper',
 'P05_L_detachable_lens_turret':'lens','P05_R_detachable_lens_turret':'lens',
 'P06_top_shutter_button':'shutter','P07_shutter_retainer_washer':'keeper',
 'T01_USB_wall_fit_coupon':'coupon','T02_tolerance_fit_coupon':'coupon'
}

def scene(w=1600,h=1140):
 ren=vtk.vtkRenderer();ren.SetBackground(1,1,1)
 window=vtk.vtkRenderWindow();window.SetSize(w,h);window.SetMultiSamples(8);window.SetOffScreenRendering(1);window.AddRenderer(ren)
 for pos,intensity in [((180,-260,450),.85),((-280,-160,120),.48),((80,350,190),.38)]:
  light=vtk.vtkLight();light.SetPosition(*pos);light.SetFocalPoint(0,0,0);light.SetIntensity(intensity);ren.AddLight(light)
 return ren,window

def add(scene,name,color=None,opacity=1,translate=(0,0,0),wire=False):
 ren=scene[0]
 file=PARTS[name]
 reader=vtk.vtkSTLReader();reader.SetFileName(str(file));reader.Update()
 normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(reader.GetOutputPort());normals.SplittingOff();normals.ConsistencyOn();normals.AutoOrientNormalsOn();normals.Update()
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort());mapper.ScalarVisibilityOff()
 a=vtk.vtkActor();a.SetMapper(mapper);a.SetPosition(*translate)
 prop=a.GetProperty();prop.SetColor(*COL[color or G.get(name,'tray')]);prop.SetAmbient(.6);prop.SetDiffuse(.46);prop.SetSpecular(.18);prop.SetSpecularPower(46);prop.SetOpacity(opacity)
 if wire:prop.SetRepresentationToWireframe();prop.SetLineWidth(1.0);prop.SetOpacity(.12)
 ren.AddActor(a)
 return a

def save(s,filename,eye=(-190,-240,125),focus=(0,0,0),scale=76):
 ren,win=s
 cam=vtk.vtkCamera();cam.SetPosition(*eye);cam.SetFocalPoint(*focus);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale);ren.SetActiveCamera(cam)
 win.Render()
 capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update()
 writer=vtk.vtkPNGWriter();writer.SetInputConnection(capture.GetOutputPort());writer.SetFileName(str(REV/filename));writer.Write();win.Finalize()
 print('review/'+filename,flush=True)

def add_hardware(s,pcb=True,battery=True,camera=True):
 if battery:add(s,'HW01_Linocell_5000mAh_BANK','battery')
 if pcb:
  for name in ['HW02_L_ESP32CAM_PCB','HW02_R_ESP32CAM_PCB']:add(s,name,'pcb')
 if camera:
  for name in ['HW03_L_OV2640_MODULE_ENVELOPE','HW03_R_OV2640_MODULE_ENVELOPE']:add(s,name,'camera')

def add_mechanics(s,with_lens=True,with_shutter=False):
 for name in G:
  if name.startswith('T'):continue
  if name.startswith('P05') and not with_lens:continue
  if name.startswith(('P06','P07')) and not with_shutter:continue
  add(s,name)

s=scene();add_hardware(s);save(s,'01_nominal_3components.png',scale=66)
s=scene();add_hardware(s);add(s,'P02_powerbank_open_U_cradle');save(s,'02_battery_snug_open_cradle.png',eye=(-200,90,125),focus=(-13,10,0),scale=65)
s=scene();add_hardware(s);add_mechanics(s);save(s,'03_native_cad_assembled_internals.png',eye=(-205,-245,118),focus=(0,-2,0),scale=67)
s=scene();add_hardware(s);add_mechanics(s);save(s,'04_native_cad_front.png',eye=(0,-250,35),focus=(0,-5,0),scale=61)
s=scene();add_hardware(s);add_mechanics(s);save(s,'05_native_cad_open_rear.png',eye=(180,250,125),focus=(0,3,0),scale=69)
s=scene();add(s,'T01_USB_wall_fit_coupon');add(s,'HW01_Linocell_5000mAh_BANK','battery',.8);save(s,'06_usb_wall_cad_detail.png',eye=(-235,-95,75),focus=(-51,12,0),scale=41)
s=scene();add(s,'P01_carrier_spine');add(s,'P02_powerbank_open_U_cradle',translate=(0,0,0))
for n in ['P03_L_esp32_edge_sled','P03_R_esp32_edge_sled']:add(s,n,translate=(0,-25,0))
for n in ['P04_L_removable_PCB_retainer','P04_R_removable_PCB_retainer']:add(s,n,translate=(0,-39,0))
for n in ['P05_L_detachable_lens_turret','P05_R_detachable_lens_turret']:add(s,n,translate=(0,-53,0))
save(s,'07_exploded_native_cad.png',eye=(180,-295,135),focus=(0,-16,0),scale=90)
for name in ['P01_carrier_spine','P02_powerbank_open_U_cradle','P03_L_esp32_edge_sled','P05_L_detachable_lens_turret']:
 s=scene(1400,1050);add(s,name);save(s,'part_'+name+'.png',eye=(150,-170,100),focus=(0,0,0),scale=50 if name not in ['P01_carrier_spine','P02_powerbank_open_U_cradle'] else 65)