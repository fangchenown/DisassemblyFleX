"""Run separately labelled diagnostic experiments; main measurements stay unchanged."""
import argparse,json,os
import performance_benchmark as b
def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--kind',choices=['context','gpu','api'],required=True);p.add_argument('--scenes',default='0,18,47,52');p.add_argument('--modes',default='d3d11,d3d12');p.add_argument('--repeats',type=int,default=3);a=p.parse_args()
    # The independently running primary suite owns state.json. Diagnostic
    # controllers and all child PIDs are instead discoverable under jobs/.
    b.state=lambda **kw:None
    profile={'context':6,'gpu':1,'api':6}[a.kind]
    if a.kind=='context':b.EXE=b.ROOT/'builds/context-proxy-v3/DisassemblyFlexDemo.exe'
    receipt=b.ROOT/'jobs'/f'{a.suite}-controller.json'
    b.write(receipt,dict(pid=os.getpid(),status='RUNNING',kind=a.kind,arguments=vars(a),exe=str(b.EXE),exe_sha256=b.sha(b.EXE),started=b.now()))
    with b.SystemRequired():
        for repeat in range(a.repeats):
            for mode in a.modes.split(','):
                for scene in map(int,a.scenes.split(',')):
                    order=['reference','candidate'] if repeat%2==0 else ['candidate','reference']
                    for implementation in order:
                        b.run_one(a.suite,mode,scene,repeat,implementation,180,60,profile,0,order)
    b.write(receipt,dict(pid=os.getpid(),status='PASS',kind=a.kind,arguments=vars(a),exe=str(b.EXE),exe_sha256=b.sha(b.EXE),finished=b.now()))
    b.event('diagnostic-suite-complete',suite=a.suite,diagnostic_kind=a.kind)
if __name__=='__main__':main()
