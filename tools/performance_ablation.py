"""Pair final candidate with an isolated allocation-policy diagnostic variant."""
import argparse,os
import performance_benchmark as b
def main():
    p=argparse.ArgumentParser();p.add_argument('--variant',choices=['cbpool','heapreuse','cbpool-heapreuse'],required=True);p.add_argument('--suite',required=True);p.add_argument('--scenes',default='0,18,24,47,52');p.add_argument('--repeats',type=int,default=4);p.add_argument('--context',action='store_true');a=p.parse_args()
    b.state=lambda **kw:None
    original_candidate=b.CORES['candidate'];b.CORES['reference']=original_candidate
    b.CORES['candidate']=b.ROOT/'builds'/('ablation-'+a.variant+'-v1')/'NvFlexReleaseD3D_x64.dll'
    if a.context:b.EXE=b.ROOT/'builds/context-proxy-v3/DisassemblyFlexDemo.exe'
    receipt=b.ROOT/'jobs'/f'{a.suite}-controller.json'
    info=dict(pid=os.getpid(),arguments=vars(a),reference_role='unchanged delivered candidate',candidate_role='diagnostic '+a.variant,exe_sha256=b.sha(b.EXE),dlls={k:dict(path=str(v),sha256=b.sha(v)) for k,v in b.CORES.items()})
    b.write(receipt,dict(info,status='RUNNING',started=b.now()))
    with b.SystemRequired():
        for repeat in range(a.repeats):
            for scene in map(int,a.scenes.split(',')):
                order=['reference','candidate'] if repeat%2==0 else ['candidate','reference']
                for implementation in order:b.run_one(a.suite,'d3d12',scene,repeat,implementation,300,60,6 if a.context else 0,0,order)
    b.write(receipt,dict(info,status='PASS',finished=b.now()));b.event('ablation-complete',suite=a.suite,variant=a.variant)
if __name__=='__main__':main()
