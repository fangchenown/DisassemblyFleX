"""Run independent API/context gates against an immutable candidate build."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from ledger import add_job,remove_job,event,now,write_json
PROJECT=Path(__file__).resolve().parents[1];WS=PROJECT.parent;ROOT=WS/'Build/DisassemblyFleX-20261009'
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--name',required=True);a=p.parse_args();build=ROOT/'builds'/a.build;candidate=build/'NvFlexReleaseD3D_x64.dll';reference=WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll';out=ROOT/'evidence'/a.name;out.mkdir(exist_ok=False)
    jobs=[]
    for name,script in [('basic','abi_oracle.py'),('buffers','library_buffer_oracle.py'),('params','params_oracle.py'),('lifecycle','lifecycle_oracle.py'),('geometry','geometry_api_oracle.py'),('diagnostics','diagnostic_oracle.py')]:jobs.append((name,[sys.executable,str(PROJECT/'tests'/script),str(candidate),str(out/(name+'.json'))],name!='buffers'))
    for name,exe,tail in [('context11','DisassemblyContextOracle.exe',[]),('context12','DisassemblyContextOracle.exe',['d3d12']),('radix','DisassemblyRadixOracle.exe',[]),('callbacks','DisassemblyCallbackOracle.exe',[]),('interop11','DisassemblyInteropOracle.exe',[])]:jobs.append((name,[str(build/exe),str(reference),str(candidate),str(out/(name+'.json'))]+tail,True))
    jobs.append(('kernel-params',[str(build/'DisassemblyKernelParamsOracle.exe'),str(reference),str(ROOT/'demo-runs/reference-scene47-30-v1/params.bin'),str(out/'kernel-params.json')],True))
    selected='separated4,solid64,fluid64,plane16,large1025,fluid64_nv,solid64_nv,springs32,springs80_nv,springs1025,inflatable4,inflatable4_nv,rigid8,rigid8_nv,rigid64_nv,rigid160_nv,plastic64,plastic64_nv,sphere64,capsule64,box64_nv,spheres1300_nv,convex64,mesh64,mesh1800_nv,sdf64,sdf64_nv,external_render,external_async,d3d12_fluid64,d3d12_fluid64_nv,outputs_1,outputs_2'
    jobs.append(('particles',[sys.executable,str(PROJECT/'tests/particle_step_oracle.py'),str(candidate),str(out/'particles'),selected],True))
    results=[];receipt=out/'job.json';job={'name':a.name,'kind':'regression-suite','build':a.build,'controller_pid':os.getpid(),'started':now(),'status':'RUNNING'};write_json(receipt,job);add_job({**job,'receipt':str(receipt)})
    try:
        for name,command,wrapper in jobs:
            if wrapper:command=[sys.executable,str(PROJECT/'tools/gpu_test.py'),'--name',a.name+'-'+name,'--timeout','180','--']+command
            print(name,flush=True)
            with (out/(name+'.log')).open('wb') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            results.append({'gate':name,'exit_code':result.returncode,'passed':result.returncode==0});write_json(out/'results.json',results);print(name,result.returncode,flush=True)
        job.update(status='PASS' if all(r['passed'] for r in results) else 'FAIL',finished=now());write_json(receipt,job);event('regression-suite','ABI/资源/参数/上下文/几何/回调/互操作/粒子综合回归',status=job['status'],evidence=str(out/'results.json'))
        if job['status']!='PASS':raise SystemExit(1)
    finally:remove_job(a.name)
if __name__=='__main__':main()
