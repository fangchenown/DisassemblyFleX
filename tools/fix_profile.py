"""Shared Context CPU profiler for original / old reconstruction / repaired DLL."""
import os
import fix_benchmark as fix
def main():
    b=fix.configure('final-v2');b.EXE=fix.task.WS/'Build/DisassemblyFleXPerformance-20261010/builds/context-proxy-v3/DisassemblyFlexDemo.exe'
    suite='context-v2';receipt=b.ROOT/'jobs'/f'{suite}-controller.json';info=dict(pid=os.getpid(),exe=str(b.EXE),exe_sha256=b.sha(b.EXE),scenes=[0,18,47,50,52,57],repeats=3)
    b.write(receipt,dict(info,status='RUNNING',started=b.now()))
    with b.SystemRequired():
        for repeat in range(3):
            for scene in info['scenes']:
                order=['reference','legacy','candidate'];order=order[repeat:]+order[:repeat]
                for impl in order:b.run_one(suite,'d3d12',scene,repeat,impl,180,60,6,0,order)
    b.write(receipt,dict(info,status='PASS',finished=b.now()));b.event('fix-profile-complete',suite=suite)
if __name__=='__main__':main()
