"""Run inherited ABI/physics oracles with all new outputs and ledger events isolated."""
import argparse,sys,ctypes
from common import *
from locksafe_power import SystemRequired
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--name',required=True);p.add_argument('--radix-reference-build');a=p.parse_args();meta=read(ROOT/'evidence'/f'{a.build}-build.json');build=Path(meta['dll']).parent;candidate=Path(meta['dll']);reference=Path(read(ROOT/'evidence/baselines.json')['nv']['core']['path'])
    assert sha(WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll')==sha(reference)
    out=ROOT/'runs'/a.name;out.mkdir(exist_ok=False);env=clean_env(ROOT/'temp'/a.name,dict(DISASSEMBLYFLEX_LEDGER=LEDGER,DISASSEMBLYFLEX_OUTPUT=ROOT));env['PATH']=str(build)+os.pathsep+str(WS/'FleX/bin/win64')+os.pathsep+env['PATH']
    ctypes.WinDLL('kernel32').SetErrorMode(0x0001|0x0002|0x8000)
    jobs=[]
    for name,script in [('basic','abi_oracle.py'),('buffers','library_buffer_oracle.py'),('params','params_oracle.py'),('lifecycle','lifecycle_oracle.py'),('geometry','geometry_api_oracle.py'),('diagnostics','diagnostic_oracle.py')]:
        jobs.append((name,[sys.executable,'-B',PROJECT/'tests'/script,candidate,out/(name+'.json')],name!='buffers'))
    for name,exe,tail in [('context11','DisassemblyContextOracle.exe',[]),('context12','DisassemblyContextOracle.exe',['d3d12']),('radix','DisassemblyRadixOracle.exe',[]),('callbacks','DisassemblyCallbackOracle.exe',[]),('interop11','DisassemblyInteropOracle.exe',[]),('pool12','DisassemblyD3D12PoolOracle.exe',[])]:
        gate_reference=Path(read(ROOT/'evidence'/f'{a.radix_reference_build}-build.json')['dll']) if name=='radix' and a.radix_reference_build else reference
        jobs.append((name,[build/exe,gate_reference,candidate,out/(name+'.json'),*tail],True))
    write(out/'reference-scope.json',dict(default_reference=str(reference),radix_reference_build=a.radix_reference_build,reason='Explicit frozen DF radix control for the extended D3D12 private-interface oracle; original NVIDIA self-control fails this fixture. Other gates retain NVIDIA reference.' if a.radix_reference_build else 'Original NVIDIA reference for all inherited gates.'))
    params=ROOT/'runs/baseline-pilot-d11-v1-s47-e0-r0-nv/params.bin'
    jobs.append(('kernel-params',[build/'DisassemblyKernelParamsOracle.exe',reference,params,out/'kernel-params.json'],True))
    selected='separated4,solid64,fluid64,plane16,large1025,fluid64_nv,solid64_nv,springs32,springs80_nv,springs1025,inflatable4,inflatable4_nv,rigid8,rigid8_nv,rigid64_nv,rigid160_nv,plastic64,plastic64_nv,sphere64,capsule64,box64_nv,spheres1300_nv,convex64,mesh64,mesh1800_nv,sdf64,sdf64_nv,external_render,external_async,d3d12_fluid64,d3d12_fluid64_nv,outputs_1,outputs_2'
    jobs.append(('particles',[sys.executable,'-B',PROJECT/'tests/particle_step_oracle.py',candidate,out/'particles',selected],True))
    results=[];cp=ROOT/'jobs'/f'{a.name}-controller.json';write(cp,dict(status='RUNNING',pid=os.getpid(),kind='oracle-suite',started=now()))
    with SystemRequired():
        for name,args,outer_lock in jobs:
            start=time.perf_counter();log=out/(name+'.log')
            with (gpu_lock() if outer_lock else contextlib.nullcontext()),log.open('wb') as fd:
                process=subprocess.Popen(list(map(str,args)),env=env,cwd=WS,stdout=fd,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                state(active_jobs=[dict(name=a.name+'/'+name,pid=process.pid,controller_pid=os.getpid(),log=str(log))])
                try:code=process.wait(timeout=240)
                except subprocess.TimeoutExpired:process.kill();process.wait();code=-999
            results.append(dict(gate=name,exit_code=code,status='PASS' if code==0 else 'FAIL',seconds=time.perf_counter()-start,log=str(log)));write(out/'results.json',results);event('oracle-finish',suite=a.name,**results[-1]);print(name,code,flush=True)
    status='PASS' if all(x['exit_code']==0 for x in results) else 'COMPLETE_WITH_FAILURES'
    write(cp,dict(status=status,pid=os.getpid(),kind='oracle-suite',finished=now(),results=str(out/'results.json')));state(active_jobs=[]);event('oracle-suite-complete',suite=a.name,status=status)
    if status!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
