import argparse
import concurrent.futures
import json
import subprocess
import threading
import time
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--blender',required=True)
p.add_argument('--ids',default='')
p.add_argument('--workers',type=int,default=2)
p.add_argument('--threads',type=int,default=4)
a=p.parse_args()
plan=json.loads((ROOT/'shot-plan.json').read_text())
selected=a.ids.split(',') if a.ids else [s['id'] for s in plan['shots']]
shots=[next(s for s in plan['shots'] if s['id']==identifier) for identifier in selected]
logs=ROOT/'logs';logs.mkdir(exist_ok=True)
lock=threading.Lock()
progress_file=ROOT/'batch-progress.json'
progress=json.loads(progress_file.read_text()) if progress_file.exists() else {'shots':{},'started':time.time()}

def record(shot,result):
 with lock:
  progress['shots'][shot['id']]=result
  temporary=progress_file.with_suffix('.tmp')
  temporary.write_text(json.dumps(progress,indent=2))
  temporary.replace(progress_file)
  print(json.dumps({'id':shot['id'],'filename':shot['filename'],**result}),flush=True)

def run(shot):
 start=time.time()
 record(shot,{'status':'rendering','started':start})
 cmd=[a.blender,'--background','--threads',str(a.threads),'--python',str(ROOT/'render_mono.py'),'--','--palette',shot['palette'],'--view',shot['view'],'--width',str(shot['width']),'--samples',str(shot['samples'])]
 with (logs/f"{shot['id']}.log").open('w') as log:
  r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 file=ROOT/shot['filename']
 if r.returncode or not file.exists() or file.stat().st_mtime<start:
  record(shot,{'status':'failed','returncode':r.returncode,'elapsed_seconds':round(time.time()-start,2)})
  return False
 im=Image.open(file).convert('RGBA')
 background=Image.new('RGBA',im.size,(255,255,255,255))
 im=Image.alpha_composite(background,im).convert('RGB');im.save(file)
 pixels=np.asarray(im)
 ys,xs=np.where(np.min(pixels,axis=2)<245)
 edges=int(sum(np.any(e<250,axis=-1).sum() for e in [pixels[0],pixels[-1],pixels[:,0],pixels[:,-1]]))
 result={'status':'ready_for_visual_qa','elapsed_seconds':round(time.time()-start,2),'size_bytes':file.stat().st_size,'dimensions':list(im.size),'mode':im.mode,'object_bounds':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],'edge_nonwhite':edges,'intentional_detail_crop':shot['intentional_detail_crop'],'corners':[list(im.getpixel(xy)) for xy in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]]}
 if im.size!=(shot['width'],shot['height']) or (edges and not shot['intentional_detail_crop']):
  result['status']='qa_check_failed'
 record(shot,result)
 return result['status']=='ready_for_visual_qa'

with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
 results=list(pool.map(run,shots))
if not all(results):raise SystemExit(1)
