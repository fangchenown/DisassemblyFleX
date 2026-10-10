"""Serial, lock-screen-safe official scene comparison with immutable receipts."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from ledger import write_json,event,add_job,remove_job,now
PROJECT=Path(__file__).resolve().parents[1];ROOT=PROJECT.parent/'Build/DisassemblyFleX-20261009'
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--name',required=True);p.add_argument('--scenes',required=True);p.add_argument('--frames',type=int,default=30);p.add_argument('--mode',default='d3d11');p.add_argument('--repeat-reference',action='store_true');a=p.parse_args()
    out=ROOT/'evidence'/a.name;out.mkdir(parents=True,exist_ok=False);results=[]
    receipt=out/'job.json';job={'name':a.name,'kind':'demo-suite','controller_pid':os.getpid(),'build':a.build,'mode':a.mode,'started':now(),'status':'RUNNING','results':str(out/'results.json')}
    write_json(receipt,job);add_job({**job,'receipt':str(receipt)})
    try:
        for scene in map(int,a.scenes.split(',')):
            row={'scene':scene,'runs':{}};print('scene',scene,flush=True)
            for implementation in ['reference','candidate']:
                name=f'{a.name}-{implementation}-{scene}';cmd=[sys.executable,str(PROJECT/'tools/run_demo.py'),'--build',a.build,'--implementation','reference' if a.repeat_reference else implementation,'--scene',str(scene),'--frames',str(a.frames),'--name',name,'--mode',a.mode]
                with (out/f'{name}.log').open('wb') as log:
                    result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                row['runs'][implementation]={'name':name,'exit_code':result.returncode,'loaded_implementation':'reference' if a.repeat_reference else implementation}
            if all(r['exit_code']==0 for r in row['runs'].values()):
                roots={k:ROOT/'demo-runs'/v['name'] for k,v in row['runs'].items()};reference=roots['reference'];candidate=roots['candidate']
                names=sorted(set(x.name for x in reference.glob('*.bin'))|set(x.name for x in candidate.glob('*.bin')))
                row['files']=names;row['mismatches']=[name for name in names if not (reference/name).exists() or not (candidate/name).exists() or (reference/name).read_bytes()!=(candidate/name).read_bytes()];row['equal']=not row['mismatches']
            else:row['equal']=False
            results.append(row);write_json(out/'results.json',results);print(json.dumps({k:row[k] for k in ['scene','equal','mismatches'] if k in row}),flush=True)
        job.update(status='FINISHED',finished=now(),passed=sum(x['equal'] for x in results),total=len(results));write_json(receipt,job)
        event('demo-suite','官方FlexDemo场景对照，逐字节比较所有bin采集',evidence=str(out/'results.json'),passed=sum(x['equal'] for x in results),total=len(results))
        if not all(x['equal'] for x in results):raise SystemExit(1)
    finally:remove_job(a.name)
if __name__=='__main__':main()
