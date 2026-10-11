"""Audit every captured non-timing output, retaining per-field and repeat differences."""
import argparse,collections,itertools
import numpy as np
from common import *
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--left',required=True);p.add_argument('--right',required=True);a=p.parse_args()
receipts=[r for f in (ROOT/'runs').glob(a.suite+'-*/receipt.json') if (r:=read(f)).get('suite')==a.suite];assert receipts and all(r['status']=='PASS' for r in receipts)
groups=collections.defaultdict(dict);selfs=collections.defaultdict(list)
for r in receipts:
    if r['variant'] in [a.left,a.right]:groups[(r['scene'],r['emit'],r['repeat'])][r['variant']]=r
def fields(path):
    data=path.read_bytes();kind=path.name.split('_')[0]
    if kind=='params':return {'bytes':np.frombuffer(data,dtype='u1')}
    n=int.from_bytes(data[:4],'little',signed=True);assert n>=0
    if kind=='triangles':
        assert len(data)==4+n*24
        return dict(topology=np.frombuffer(data,dtype='<i4',count=n*3,offset=4),triangle_normals=np.frombuffer(data,dtype='<f4',offset=4+n*12))
    values=np.frombuffer(data,dtype='<f4',offset=4)
    width={'rigids':7,'render':20,'diffuse':8}[kind];assert len(values)==n*width;values=values.reshape(n,width)
    if kind=='rigids':return dict(rotations=values[:,:4],translations=values[:,4:])
    if kind=='diffuse':return dict(diffuse_positions=values[:,:4],diffuse_velocities=values[:,4:])
    return {k:values[:,i*4:(i+1)*4] for i,k in enumerate(['normals','smooth_positions','anisotropy1','anisotropy2','anisotropy3'])}
def compare(lp,rp,lh,rh):
    if lh==rh:return dict(byte_identical=True)
    left,right=fields(lp),fields(rp);result=dict(byte_identical=False,fields={})
    for key in left:
        x,y=left[key],right[key];row=dict(shape_equal=x.shape==y.shape)
        if x.shape==y.shape:
            row['byte_identical']=x.tobytes()==y.tobytes()
            if np.issubdtype(x.dtype,np.floating):
                row['left_nonfinite']=int((~np.isfinite(x)).sum());row['right_nonfinite']=int((~np.isfinite(y)).sum());valid=np.isfinite(x)&np.isfinite(y)
                if valid.any():
                    diff=x[valid].astype(float)-y[valid].astype(float);row.update(max_abs=float(np.abs(diff).max()),rms=float(np.sqrt(np.mean(diff*diff))))
            else:row['mismatched_values']=int(np.sum(x!=y))
        result['fields'][key]=row
    return result
rows=[]
for (scene,emit,repeat),arms in sorted(groups.items()):
    if not all(x in arms for x in [a.left,a.right]):continue
    paths={v:ROOT/'runs'/arms[v]['name'] for v in arms};names={v:{name for name in arms[v]['files'] if name.endswith('.bin') and name.startswith(('params_','rigids_','triangles_','render_','diffuse_'))} for v in arms}
    result=dict(scene=scene,emit=emit,repeat=repeat,file_sets_equal=names[a.left]==names[a.right],files=[])
    for name in sorted(names[a.left]&names[a.right]):
        value=compare(paths[a.left]/name,paths[a.right]/name,arms[a.left]['files'][name]['sha256'],arms[a.right]['files'][name]['sha256']);result['files'].append(dict(file=name,**value))
        for v in [a.left,a.right]:selfs[(scene,emit,v,name)].append((repeat,paths[v]/name,arms[v]['files'][name]['sha256']))
    rows.append(result)
within=[]
for (scene,emit,variant,name),samples in selfs.items():
    for x,y in itertools.combinations(sorted(samples),2):within.append(dict(scene=scene,emit=emit,variant=variant,file=name,repeats=[x[0],y[0]],**compare(x[1],y[1],x[2],y[2])))
by_scene=[]
for scene in sorted(set(r['scene'] for r in rows)):
    files=[f for r in rows if r['scene']==scene for f in r['files']];classes=collections.defaultdict(lambda:dict(pairs=0,exact=0))
    for f in files:
        group=classes[f['file'].split('_')[0]];group['pairs']+=1;group['exact']+=f['byte_identical']
    by_scene.append(dict(scene=scene,outputs=dict(classes),all_file_sets_equal=all(r['file_sets_equal'] for r in rows if r['scene']==scene)))
label=a.suite+'__'+a.left+'-vs-'+a.right
write(ROOT/'analysis'/f'{label}-aux-outputs.json',dict(cross=rows,self=within))
write(ROOT/'analysis'/f'{label}-aux-summary.json',dict(suite=a.suite,scenes=by_scene,scope='All captured outputs; equality is bytewise. Differences retained by field and per-arm repeat. Disabled/unrequested output domains can be unspecified; no universal finite/semantic verdict is inferred.'))
print(json.dumps(by_scene,ensure_ascii=False))
