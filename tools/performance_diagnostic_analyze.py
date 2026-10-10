"""Aggregate diagnostic CPU scopes, GPU timers, and allocation-policy experiments."""
import csv,json,statistics,collections
import performance_benchmark as b
def main():
    output={}
    for suite in ['context-v1','gpu-v1','context-heavy-v1','gpu-heavy-v1','pooled-context-v1']:
        groups=collections.defaultdict(list)
        for path in sorted((b.ROOT/'runs').glob(suite+'-*/job.json')):
            j=json.loads(path.read_text(encoding='utf-8'))
            if j['status']!='PASS':continue
            frames=j['frames']-j['warmup'];root=path.parent;data={}
            for file,keycol,valuecol in [('context-cpu.csv','method','total_ms'),('api.csv','name','ms'),('cpu-phases.csv','phase','wall_ms'),('detail.csv','name','ms')]:
                if not (root/file).exists():continue
                accumulated=collections.defaultdict(lambda:dict(calls=0,ms=0))
                for r in csv.DictReader((root/file).open()):
                    if 'frame' in r and int(r['frame'])<=j['warmup']:continue
                    dst=accumulated[r[keycol]];dst['ms']+=float(r[valuecol]);dst['calls']+=int(r.get('calls',1))
                data[file]={k:dict(ms_per_frame=v['ms']/frames,calls_per_frame=v['calls']/frames) for k,v in accumulated.items()}
            data['frame_metrics']={k:v['mean'] for k,v in j['metrics'].items()}
            groups[j['mode'],j['scene'],j['implementation']].append(data)
        result=[]
        for (mode,scene,impl),runs in sorted(groups.items()):
            r=dict(mode=mode,scene=scene,implementation=impl,repeats=len(runs))
            for file in ['context-cpu.csv','api.csv','cpu-phases.csv','detail.csv']:
                keys=set().union(*(set(x.get(file,{})) for x in runs))
                r[file]={k:{v:statistics.mean(x.get(file,{}).get(k,{}).get(v,0) for x in runs) for v in ['ms_per_frame','calls_per_frame']} for k in keys}
            r['frame_metrics']={k:statistics.mean(x['frame_metrics'][k] for x in runs) for k in runs[0]['frame_metrics']}
            result.append(r)
        output[suite]=result
    b.write(b.ROOT/'analysis/diagnostics.json',output)
    for suite,rows in output.items():
        print(suite)
        for r in rows:
            if r['mode']=='d3d12':print(r['scene'],r['implementation'],r['frame_metrics'], sorted(r['context-cpu.csv'].items(),key=lambda x:-x[1]['ms_per_frame'])[:3])
if __name__=='__main__':main()
