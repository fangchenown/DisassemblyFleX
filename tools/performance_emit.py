"""Exercise the official particle-emitter toggle without keyboard/desktop input."""
import os,argparse
import performance_benchmark as b
def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',default='emit-v1');p.add_argument('--scenes',default='39,40');a=p.parse_args();scenes=list(map(int,a.scenes.split(',')))
    suite=a.suite;b.state=lambda **kw:None;base=b.env_for
    def env(temp,core):
        result=base(temp,core);result['DEMO_EMIT']='1';return result
    b.env_for=env
    receipt=b.ROOT/'jobs'/f'{suite}-controller.json';info=dict(pid=os.getpid(),suite=suite,scenes=scenes,repeats=4,extra_environment={'DEMO_EMIT':'1'},activation='Existing harness calls official InputKeyboardDown(space) before frame 1; no desktop input')
    b.write(receipt,dict(info,status='RUNNING',started=b.now()))
    with b.SystemRequired():
        for repeat in range(4):
            for mode in ['d3d11','d3d12']:
                for scene in scenes:
                    order=['reference','candidate'] if repeat%2==0 else ['candidate','reference']
                    for implementation in order:b.run_one(suite,mode,scene,repeat,implementation,300,60,0,0,order)
    b.write(receipt,dict(info,status='PASS',finished=b.now()));b.event('emit-suite-complete',suite=suite)
if __name__=='__main__':main()
