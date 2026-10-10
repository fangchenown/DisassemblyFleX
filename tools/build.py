"""Reproducible source snapshot + contained hidden command-line build."""
import argparse,hashlib,json,os,shutil,subprocess,uuid
from pathlib import Path
from ledger import add_job,remove_job,PROJECT,LEDGER,OUTPUT,write_json,event,checkpoint,now
WS=PROJECT.parent
VC=Path(r'F:\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC\14.44.35207')
SDK=Path(r'C:\Program Files (x86)\Windows Kits\10')
def environment(temp):
    env=os.environ.copy()
    for k in ('TEMP','TMP','TMPDIR'):env[k]=str(temp)
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['PATH']=str(VC/'bin/Hostx64/x64')+os.pathsep+str(SDK/'bin/10.0.26100.0/x64')+os.pathsep+env['PATH']
    env['INCLUDE']=';'.join(str(x) for x in [VC/'include',*[SDK/'Include/10.0.26100.0'/x for x in ('ucrt','shared','um','winrt')]])
    env['LIB']=';'.join(str(x) for x in [VC/'lib/x64',SDK/'Lib/10.0.26100.0/ucrt/x64',SDK/'Lib/10.0.26100.0/um/x64'])
    return env
def run(command,log,env,job):
    with log.open('wb') as output:
        process=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,env=env,cwd=OUTPUT,creationflags=subprocess.CREATE_NO_WINDOW)
        write_json(OUTPUT/'jobs'/f'{job}.json',{'job':job,'pid':process.pid,'command':list(map(str,command)),'log':str(log),'status':'RUNNING','started':now()})
        code=process.wait()
    write_json(OUTPUT/'jobs'/f'{job}.json',{'job':job,'pid':process.pid,'command':list(map(str,command)),'log':str(log),'status':'PASS' if code==0 else 'FAIL','exit_code':code,'finished':now()})
    if code:raise RuntimeError(str(log)+' exit '+str(code))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--name',required=True);parser.add_argument('--shader-compiler');parser.add_argument('--shader-fp-policy',choices=['default','precise','frontend','float_frontend'],default='frontend');parser.add_argument('--shader-schedule',choices=['fxc','preserved'],default='preserved');parser.add_argument('--relaxed-shaders',default='');args=parser.parse_args()
    name=args.name
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in name):raise ValueError(name)
    snapshot=OUTPUT/'source-snapshots'/name;binary=OUTPUT/'builds'/name
    for p in (snapshot,binary):
        p.resolve().relative_to((WS/'Build').resolve())
        if p.exists():raise RuntimeError('Immutable run path exists: '+str(p))
        p.mkdir(parents=True)
    hashes={}
    for top in ['include','src','shaders','cmake','reference','tools','tests']:
        shutil.copytree(PROJECT/top,snapshot/top,ignore=shutil.ignore_patterns('__pycache__','*.pyc'),dirs_exist_ok=True)
    shutil.copyfile(PROJECT/'CMakeLists.txt',snapshot/'CMakeLists.txt')
    for p in sorted(snapshot.rglob('*')):
        if p.is_file():hashes[p.relative_to(snapshot).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    write_json(snapshot/'source_manifest.json',hashes)
    temp=OUTPUT/'temp'/f'{name}-{uuid.uuid4().hex}';temp.mkdir()
    env=environment(temp)
    cmake=shutil.which('cmake');pwsh=shutil.which('pwsh') or 'powershell.exe'
    generator=str(WS/'Build/Toolchains/ninja/1.13.2/ninja.exe')
    quote=lambda s:"'"+str(s).replace("'","''")+"'"
    configure_script=binary/'invoke_configure.ps1'
    configure_arguments=['-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_MAKE_PROGRAM='+generator,'-DDISASSEMBLYFLEX_WORKSPACE='+str(WS)]
    if args.shader_compiler:configure_arguments.append('-DDISASSEMBLYFLEX_SHADER_COMPILER_DLL='+str(Path(args.shader_compiler).resolve()))
    configure_arguments.append('-DDISASSEMBLYFLEX_SHADER_FP_POLICY='+args.shader_fp_policy)
    configure_arguments.append('-DDISASSEMBLYFLEX_SHADER_SCHEDULE='+args.shader_schedule)
    configure_arguments.append('-DDISASSEMBLYFLEX_RELAXED_SHADERS='+args.relaxed_shaders)
    configure_script.write_text('& '+quote(WS/'OpenFleX/tools/Invoke-OpenFlexCMakeConfigure.ps1')+' -SourceDirectory '+quote(snapshot)+' -BinaryDirectory '+quote(binary)+' -CMakePath '+quote(cmake)+' -ConfigureArguments @('+','.join(map(quote,configure_arguments))+')\nexit $LASTEXITCODE\n',encoding='utf-8')
    commands=[('configure',[pwsh,'-NoProfile','-File',str(configure_script)]),
              ('build',[cmake,'--build',str(binary),'--parallel','4'])]
    event('build-start','独立DLL构建 '+name,source_snapshot=str(snapshot),binary_dir=str(binary))
    add_job({'kind':'build','name':name,'controller_pid':os.getpid(),'status_dir':str(OUTPUT/'jobs')})
    try:
        for phase,command in commands:run(command,OUTPUT/'logs'/f'{name}-{phase}.log',env,f'{name}-{phase}')
        path=binary/'NvFlexReleaseD3D_x64.dll';digest=hashlib.sha256(path.read_bytes()).hexdigest()
        receipt={'name':name,'dll':str(path),'sha256':digest,'source_snapshot':str(snapshot),'source_files':len(hashes),'status':'PASS'}
        write_json(OUTPUT/'evidence'/f'{name}-build.json',receipt)
        event('build-complete','独立DLL构建成功；功能是否完整另见API清单与行为门禁。',**receipt)
        print(json.dumps(receipt,indent=2))
    except Exception as exc:
        event('build-failed',str(exc),name=name);raise
    finally:
        remove_job(name)
if __name__=='__main__':main()
