import math
from pathlib import Path
import vtk
R=Path(__file__).resolve().parents[1]
OUT=R/'manual'/'figures';OUT.mkdir(exist_ok=True,parents=True)
STLS={p.stem:p for p in (R/'stl').glob('*.stl')}
STLS.update({p.name[5:-4]:p for p in (R/'review').glob('_ref_HW*.stl')})

def make(w=1400,h=1150):
 ren=vtk.vtkRenderer();ren.SetBackground(1,1,1)
 win=vtk.vtkRenderWindow();win.SetSize(w,h);win.SetMultiSamples(8);win.SetOffScreenRendering(1);win.AddRenderer(ren)
 cam=vtk.vtkCamera();cam.SetPosition(-175,-240,128);cam.SetFocalPoint(0,0,0);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(70);ren.SetActiveCamera(cam)
 light=vtk.vtkLight();light.SetPosition(-160,-280,360);light.SetIntensity(.95);ren.AddLight(light)
 return ren,win,cam

def add(s,name,shift=(0,0,0),grey=.92,black_only=False):
 ren,win,cam=s
 read=vtk.vtkSTLReader();read.SetFileName(str(STLS[name]));read.Update()
 normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(read.GetOutputPort());normals.AutoOrientNormalsOn();normals.ConsistencyOn();normals.SplittingOff();normals.Update()
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
 solid=vtk.vtkActor();solid.SetMapper(mapper);solid.SetPosition(*shift)
 p=solid.GetProperty();p.SetColor(.93,.93,.93) if grey>.87 else p.SetColor(.76,.76,.76);p.SetAmbient(.64);p.SetDiffuse(.38);p.SetSpecular(.03);ren.AddActor(solid)
 outline=vtk.vtkPolyDataSilhouette();outline.SetInputConnection(read.GetOutputPort());outline.SetCamera(cam)
 om=vtk.vtkPolyDataMapper();om.SetInputConnection(outline.GetOutputPort());om.ScalarVisibilityOff();oa=vtk.vtkActor();oa.SetMapper(om);oa.SetPosition(*shift)
 op=oa.GetProperty();op.SetColor(.08,.08,.08);op.SetLineWidth(2.25);op.SetAmbient(1);op.SetDiffuse(0);op.SetLighting(False);ren.AddActor(oa)
 edge=vtk.vtkFeatureEdges();edge.SetInputConnection(read.GetOutputPort());edge.BoundaryEdgesOff();edge.ManifoldEdgesOff();edge.NonManifoldEdgesOff();edge.FeatureEdgesOn();edge.SetFeatureAngle(48)
 em=vtk.vtkPolyDataMapper();em.SetInputConnection(edge.GetOutputPort());em.ScalarVisibilityOff();ea=vtk.vtkActor();ea.SetMapper(em);ea.SetPosition(*shift)
 ep=ea.GetProperty();ep.SetColor(.30,.30,.30);ep.SetLineWidth(1.1);ep.SetLighting(False);ren.AddActor(ea)

def save(s,file,eye,focus,scale):
 ren,win,cam=s;cam.SetPosition(*eye);cam.SetFocalPoint(*focus);cam.SetViewUp(0,0,1);cam.SetParallelScale(scale)
 win.Render();fil=vtk.vtkWindowToImageFilter();fil.SetInput(win);fil.SetInputBufferTypeToRGB();fil.ReadFrontBufferOff();fil.Update()
 wr=vtk.vtkPNGWriter();wr.SetInputConnection(fil.GetOutputPort());wr.SetFileName(str(OUT/file));wr.Write();win.Finalize();print(file,flush=True)

s=make();add(s,'T01_USB_wall_fit_coupon');add(s,'T02_tolerance_fit_coupon',shift=(50,0,0));save(s,'01_fit_coupons.png',(-190,-210,140),(20,0,0),50)
s=make();add(s,'P02_powerbank_open_U_cradle');add(s,'HW01_Linocell_5000mAh_BANK',shift=(0,21,0),grey=.74);save(s,'02_battery_insert.png',(-210,190,140),(-12,12,0),67)
s=make();add(s,'P03_L_esp32_edge_sled');add(s,'HW02_L_ESP32CAM_PCB',shift=(0,0,35),grey=.75);save(s,'03_slide_left_PCB.png',(-130,-200,130),(0,-8,11),52)
s=make();add(s,'P03_R_esp32_edge_sled');add(s,'HW02_R_ESP32CAM_PCB',shift=(0,0,35),grey=.75);save(s,'04_slide_right_PCB.png',(60,-220,130),(43,-8,11),52)
s=make();add(s,'P03_L_esp32_edge_sled');add(s,'P04_L_removable_PCB_retainer',shift=(0,-24,0));save(s,'05_attach_retainer.png',(-120,-220,120),(0,-10,-5),49)
s=make();add(s,'P01_carrier_spine');add(s,'P03_L_esp32_edge_sled',shift=(0,-24,0));add(s,'P03_R_esp32_edge_sled',shift=(0,-24,0));save(s,'06_sleds_into_spine.png',(180,-240,150),(22,-9,-6),70)
s=make();add(s,'P01_carrier_spine');add(s,'P02_powerbank_open_U_cradle');save(s,'07_outer_chassis.png',(170,-200,160),(2,1,0),70)
s=make();add(s,'P05_L_detachable_lens_turret');add(s,'P05_R_detachable_lens_turret');save(s,'08_lens_turrets.png',(175,-220,125),(31,-24,7),35)
s=make();add(s,'P06_top_shutter_button');add(s,'P07_shutter_retainer_washer',shift=(0,0,-13));save(s,'09_button_mechanism.png',(155,-150,110),(-53,-7,27),20)
s=make();add(s,'T01_USB_wall_fit_coupon');add(s,'HW01_Linocell_5000mAh_BANK',grey=.74);save(s,'10_USB_cutout.png',(-240,-130,140),(-48,14,0),54)
s=make()
for name in ['P01_carrier_spine','P02_powerbank_open_U_cradle','P03_L_esp32_edge_sled','P03_R_esp32_edge_sled','P04_L_removable_PCB_retainer','P04_R_removable_PCB_retainer','P05_L_detachable_lens_turret','P05_R_detachable_lens_turret']:add(s,name)
save(s,'11_assembled_internals.png',(-200,-240,130),(0,-2,0),68)