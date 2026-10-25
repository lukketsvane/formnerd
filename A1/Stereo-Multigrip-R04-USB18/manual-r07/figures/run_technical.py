import argparse,json,subprocess
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser()
p.add_argument('--blender',required=True)
p.add_argument('--blend',required=True)
p.add_argument('--r04-source')
p.add_argument('--scenes',nargs='+',default=['assembled','exploded','seated','keepers_rear','yokes','rear_usb','pair_front','board_stack','cam_only','mb_only'])
a=p.parse_args()
out=Path(__file__).resolve().parent
for scene in a.scenes:
 with (out/f'technical-{scene}.log').open('w') as log:
  subprocess.run([a.blender,'-b','-t','8','--python',str(out/'render_technical.py'),'--','--blend',a.blend,'--output',str(out/f'technical_{scene}.png'),'--scene',scene,'--width','3000','--samples','8']+(['--r04-source',a.r04_source] if a.r04_source else []),stdout=log,stderr=subprocess.STDOUT,check=True)
 im=Image.open(out/f'technical_{scene}.png').convert('RGB')
 temp=out/f'technical_{scene}.rgb.png'
 im.save(temp)
 temp.replace(out/f'technical_{scene}.png')
 print('COMPLETE',scene,flush=True)
