# usage: cut_sheets.py <batch-json>  ; batch = [[upload_path, [[sex,age,look]x4]], ...]
import sys, json, os
from PIL import Image
import numpy as np
G=os.environ.get('G','/tmp/faces')
reg_path=G+'/data/resident_faces.json'
reg=json.load(open(reg_path)) if os.path.exists(reg_path) else []
batch=json.load(open(sys.argv[1]))
def runs(mask):
    out=[];start=None
    for i,v in enumerate(mask):
        if v and start is None: start=i
        if not v and start is not None: out.append((start,i)); start=None
    if start is not None: out.append((start,len(mask)))
    return out
for path, people in batch:
    if any(r['src']==os.path.basename(path) for r in reg): continue
    im=Image.open(path).convert('RGB'); W,H=im.size; a=np.asarray(im).astype(int)
    light=(a.min(axis=2)>200)
    cols=[c for c in runs(light.mean(axis=0)<0.5) if c[1]-c[0]>W*0.3]
    rows=[r for r in runs(light.mean(axis=1)<0.5) if r[1]-r[0]>H*0.3]
    if len(cols)!=2 or len(rows)!=2:   # no white gutter: split in the middle
        cols=[(0,W//2),(W//2,W)]; rows=[(0,H//2),(H//2,H)]
    k=0
    for r in rows:
        for c in cols:
            cell=im.crop((c[0]+3,r[0]+3,c[1]-3,r[1]-3)); w,h=cell.size; s=min(w,h)
            cell=cell.crop(((w-s)//2,(h-s)//2,(w-s)//2+s,(h-s)//2+s)).resize((512,512),Image.LANCZOS)
            fid='r%04d'%(len(reg)+1)
            cell.save(f'{G}/assets/residents/{fid}.jpg',quality=88)
            sex,age,look=people[k]
            reg.append({'id':fid,'sex':sex,'age':age,'look':look,'src':os.path.basename(path)}); k+=1
json.dump(reg,open(reg_path,'w'),ensure_ascii=False,indent=0)
print(len(reg))
