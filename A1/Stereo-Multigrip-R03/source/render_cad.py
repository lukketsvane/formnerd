#!/usr/bin/env python3
"""Deterministic, headless STL assembly preview renderer (NumPy/Pillow).
Scene: list of {"stl": path, "color": [r,g,b,a], "translation": [x,y,z]}.
Also accepts {"items": [...]} and path/file aliases. Z faces the lens, Y is up.
"""
import argparse, json, struct, pathlib, math
import numpy as np
from PIL import Image, ImageFilter


def read_stl(path):
    data=pathlib.Path(path).read_bytes()
    if len(data)>=84:
        n=struct.unpack_from('<I',data,80)[0]
        if 84+50*n==len(data):
            dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
            return np.frombuffer(data,dtype=dt,count=n,offset=84)['v'].astype(np.float64)
    verts=[]
    for line in data.decode('ascii',errors='ignore').splitlines():
        tok=line.strip().split()
        if tok and tok[0]=='vertex': verts.append([float(x) for x in tok[1:4]])
    a=np.array(verts,dtype=np.float64)
    if len(a)%3: raise ValueError('Bad STL vertex count: '+str(path))
    return a.reshape(-1,3,3)


def unit(v):
    a=np.asarray(v,dtype=float)
    return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-15)


def smooth_normals(tris):
    fn=unit(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]))
    _,inv=np.unique(np.round(tris.reshape(-1,3),5),axis=0,return_inverse=True)
    order=np.argsort(inv,kind='stable')
    split=np.r_[0,np.flatnonzero(np.diff(inv[order]))+1,len(order)]
    vn=np.empty((len(order),3),dtype=np.float64)
    for a,b in zip(split[:-1],split[1:]):
        indices=order[a:b]; ns=fn[indices//3]
        # Crease-preserving averaging, with equal weighting of incident faces.
        cos=ns @ ns.T
        weights=(cos>0.72).astype(float)
        vn[indices]=unit(weights @ ns)
    return fn,vn.reshape(-1,3,3)


def colour(c):
    if isinstance(c,str):
        h=c.lstrip('#'); c=[int(h[i:i+2],16) for i in (0,2,4)]+[255]
    a=np.array(c or [0.7,0.72,0.74,1.0],dtype=float)
    if len(a)==3:a=np.r_[a,1 if a.max()<=1 else 255]
    if a[:3].max()>1:a[:3]/=255
    if a[3]>1:a[3]/=255
    return a


def render(scene,out,view='iso',width=1600,height=1200,ss=2):
    base=pathlib.Path(scene).resolve().parent
    obj=json.loads(pathlib.Path(scene).read_text())
    cfg=obj if isinstance(obj,dict) else {}
    items=cfg.get('items',cfg.get('objects',[])) if isinstance(obj,dict) else obj
    meshes=[]
    for item in items:
        p=item.get('stl',item.get('path',item.get('file')))
        if not p: raise ValueError('Each scene item needs an stl path')
        p=pathlib.Path(p); p=p if p.is_absolute() else base/p
        tri=read_stl(p)
        # Optional row-major 4x4 transform, then world-space translation.
        if 'transform' in item:
            m=np.array(item['transform'],float).reshape(4,4)
            tri=(np.c_[tri.reshape(-1,3),np.ones(tri.size//3)]@m.T)[:,:3].reshape(-1,3,3)
        tri += np.array(item.get('translation',item.get('translate',[0,0,0])))
        fn,vn=smooth_normals(tri)
        meshes.append((tri,fn,vn,colour(item.get('color',item.get('colour')))))
    if not meshes:raise ValueError('Empty scene')
    cameras={'iso':[1.0,0.68,1.7],'front':[0,0,1],'rear':[-1.0,0.5,-1.7]}
    forward=unit(cfg.get('camera',cameras[view]))
    right=unit(np.cross([0,1,0],forward)); up=unit(np.cross(forward,right))
    basis=np.array([right,up,forward]).T
    allverts=np.concatenate([a.reshape(-1,3) for a,_,_,_ in meshes])
    pts=allverts@basis
    lo=pts.min(0); hi=pts.max(0); mid=(lo+hi)/2
    W,H=width*ss,height*ss
    scale=min(W*.86/max(hi[0]-lo[0],1e-6),H*.82/max(hi[1]-lo[1],1e-6))
    zbuf=np.full((H,W),-np.inf,dtype=np.float32)
    rgb=np.ones((H,W,3),dtype=np.float32)
    mask=np.zeros((H,W),dtype=np.uint8)
    # Distant diffuse studio sources and a small, neutral specular highlight.
    key=unit([-0.55,0.9,1.8]); fill=unit([1.2,0.2,0.7]); rim=unit([0.1,1,-1.2])
    half=unit(key+forward)
    faces=0
    for tri,fn,vn,c in meshes:
        p=tri@basis
        p[:,:,0]=(p[:,:,0]-mid[0])*scale+W/2
        p[:,:,1]=H*.49-(p[:,:,1]-mid[1])*scale
        # Front-facing triangles; STL solids must be outward-oriented.
        visible=np.einsum('ij,j->i',fn,forward)>-1e-7
        shade=.43+.48*np.maximum(0,vn@key)+.16*np.maximum(0,vn@fill)+.09*np.maximum(0,vn@rim)
        spec=.10*np.maximum(0,vn@half)**40
        shade=np.clip(shade,.36,1.16)
        colors=np.clip(c[:3][None,None,:]*shade[:,:,None]+spec[:,:,None],0,1)
        for q,cols in zip(p[visible],colors[visible]):
            xmin=max(0,int(math.floor(q[:,0].min()))); xmax=min(W-1,int(math.ceil(q[:,0].max())))
            ymin=max(0,int(math.floor(q[:,1].min()))); ymax=min(H-1,int(math.ceil(q[:,1].max())))
            if xmin>xmax or ymin>ymax:continue
            x0,y0,z0=q[0];x1,y1,z1=q[1];x2,y2,z2=q[2]
            den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
            if abs(den)<1e-9:continue
            xx=np.arange(xmin,xmax+1,dtype=np.float32)[None,:]+.5
            yy=np.arange(ymin,ymax+1,dtype=np.float32)[:,None]+.5
            b0=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
            b1=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den
            b2=1-b0-b1
            dep=b0*z0+b1*z1+b2*z2
            region=zbuf[ymin:ymax+1,xmin:xmax+1]
            hit=(b0>=-1e-6)&(b1>=-1e-6)&(b2>=-1e-6)&(dep>region)
            if not hit.any():continue
            region[hit]=dep[hit]
            target=rgb[ymin:ymax+1,xmin:xmax+1]
            pix=b0[:,:,None]*cols[0]+b1[:,:,None]*cols[1]+b2[:,:,None]*cols[2]
            # Alpha optional; conservative opaque depth ordering for engineering previews.
            if c[3]<1:pix=1-c[3]+pix*c[3]
            target[hit]=pix[hit]
            mask[ymin:ymax+1,xmin:xmax+1][hit]=255
            faces+=1
    # Subtle image-space cavity accents at depth discontinuities, never drawn over air.
    valid=mask>0
    depth=np.where(valid,zbuf,0)
    occl=np.zeros((H,W),dtype=np.float32)
    dlim=max((hi[2]-lo[2])*.006,0.08)
    for dy,dx in ((0,2*ss),(0,-2*ss),(2*ss,0),(-2*ss,0)):
        n=np.roll(depth,(dy,dx),(0,1)); good=np.roll(valid,(dy,dx),(0,1))&valid
        occl+=good*((n-depth)>dlim)
    rgb*= (1-.025*occl)[:,:,None]
    im=Image.fromarray(np.uint8(np.clip(rgb,0,1)*255),'RGB')
    # Barely visible soft halo provides object separation on white without adding geometry.
    m=Image.fromarray(mask,'L')
    shadow=m.filter(ImageFilter.GaussianBlur(9*ss))
    sh=np.asarray(shadow,dtype=np.float32)/255*.045
    bg=np.repeat((255*(1-sh))[:,:,None],3,axis=2).astype(np.uint8)
    bg[valid]=np.asarray(im)[valid]
    image=Image.fromarray(bg,'RGB').resize((width,height),Image.Resampling.LANCZOS)
    pathlib.Path(out).parent.mkdir(parents=True,exist_ok=True)
    image.save(out)
    print(json.dumps({'output':str(pathlib.Path(out).resolve()),'meshes':len(meshes),'triangles':sum(len(t) for t,_,_,_ in meshes),'visible_triangles':faces,'width':width,'height':height,'view':view}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--scene',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--view',choices=['iso','front','rear'],default='iso');ap.add_argument('--width',type=int,default=1600);ap.add_argument('--height',type=int,default=1200);ap.add_argument('--ss',type=int,default=2)
    a=ap.parse_args();render(a.scene,a.output,a.view,a.width,a.height,a.ss)
