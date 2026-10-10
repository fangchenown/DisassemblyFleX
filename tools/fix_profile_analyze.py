import csv,collections,statistics,json
import fix_task as task
from fix_analyze import load
from performance_benchmark import write
def main():
    runs,_=load('context-v2');groups=collections.defaultdict(list)
    for j in runs:
        root=task.ROOT/'runs'/j['name'];data={};frames=j['frames']-j['warmup']
        for filename,key,value in [('context-cpu.csv','method','total_ms'),('cpu-phases.csv','phase','wall_ms'),('api.csv','name','ms')]:
            rows=collections.defaultdict(lambda:{'calls':0,'ms':0})
            for row in csv.DictReader((root/filename).open()):
                if 'frame' in row and int(row['frame'])<=j['warmup']:continue
                rows[row[key]]['calls']+=int(row.get('calls',1));rows[row[key]]['ms']+=float(row[value])
            data[filename]={name:{'calls_per_frame':x['calls']/frames,'ms_per_frame':x['ms']/frames} for name,x in rows.items()}
        data['complete_ms']=j['metrics']['complete_ms']['mean'];groups[j['scene'],j['implementation']].append(data)
    result=[]
    for (scene,impl),rr in sorted(groups.items()):
        item=dict(scene=scene,implementation=impl,repeats=len(rr),complete_ms=statistics.mean(r['complete_ms'] for r in rr))
        for filename in ['context-cpu.csv','cpu-phases.csv','api.csv']:
            keys=set().union(*(set(r[filename]) for r in rr));item[filename]={key:{metric:statistics.mean(r[filename].get(key,{}).get(metric,0) for r in rr) for metric in ['calls_per_frame','ms_per_frame']} for key in keys}
        result.append(item)
    write(task.ROOT/'analysis/context-v2.json',result);print('Context diagnostic groups',len(result))
if __name__=='__main__':main()
