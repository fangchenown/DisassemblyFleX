"""Immutable source builds for DF alpha migration; prior task ledgers are never used."""
import argparse,difflib
from common import *
def register(record):
    path=ROOT/'evidence/variants.json';v=read(path) if path.exists() else {}
    for key,mode in [(record['name'],'df-d3d11'),(record['name']+'-d3d12','df-d3d12')]:
        v[key]=dict(core=record['dll'],ext=record['ext'],core_sha256=record['dll_sha256'],ext_sha256=record['ext_sha256'],mode=mode,environment={},diagnostic_only=any('VALIDATE_BINDINGS=ON' in x for x in record.get('cmake_arguments',[])))
    write(path,v)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--name',required=True);ap.add_argument('--source',default='baseline');ap.add_argument('--core-only',action='store_true');ap.add_argument('--cmake-arg',action='append',default=[]);a=ap.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.name);assert not any(read(p).get('status')=='RUNNING' for p in (ROOT/'jobs').glob('*-controller.json'))
    origin=ROOT/'baseline/source' if a.source=='baseline' else PROJECT if a.source=='current' else Path(a.source).resolve()
    assert origin==PROJECT or ROOT.resolve() in origin.resolve().parents
    snapshot=ROOT/'sources'/a.name;binary=ROOT/'builds'/a.name;receipt=ROOT/'evidence'/f'{a.name}-build.json'
    if receipt.exists():
        record=read(receipt);assert record['status']=='PASS' and sha(record['dll'])==record['dll_sha256'];assert record.get('cmake_arguments',[])==a.cmake_arg,'Existing build has different compiler options';register(record);print('Verified existing build',a.name);return
    if not (snapshot/'CMakeLists.txt').exists():
        snapshot.mkdir(exist_ok=True)
        for name in ['include','src','shaders','cmake','reference','tools','tests']:
            if (origin/name).is_dir():shutil.copytree(longpath(origin/name),longpath(snapshot/name),ignore=shutil.ignore_patterns('__pycache__','*.pyc'),dirs_exist_ok=True)
        shutil.copy2(origin/'CMakeLists.txt',snapshot/'CMakeLists.txt')
    manifest={p.relative_to(snapshot).as_posix():sha(p) for p in snapshot.rglob('*') if p.is_file()}
    write(ROOT/'evidence'/f'{a.name}-source.json',dict(origin=str(origin),snapshot=str(snapshot),files=manifest))
    cmake=shutil.which('cmake');ninja=WS/'Build/Toolchains/ninja/1.13.2/ninja.exe';env=build_env(ROOT/'temp'/a.name)
    command([cmake,'-S',snapshot,'-B',binary,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_BUILD_TYPE=Release','-DDISASSEMBLYFLEX_WORKSPACE='+str(WS),'-DDISASSEMBLYFLEX_BUILD_DEMO=OFF','-DDISASSEMBLYFLEX_SHADER_SCHEDULE=preserved','-DDISASSEMBLYFLEX_SHADER_FP_POLICY=frontend',*a.cmake_arg],a.name+'-configure',env)
    targets=['NvFlexReconstructed']
    if not a.core_only:targets+=['DisassemblyContextOracle','DisassemblyD3D12PoolOracle','DisassemblyD3D12NativeProbe','DisassemblyCallbackOracle','DisassemblyInteropOracle','DisassemblyRadixOracle','DisassemblyKernelParamsOracle']
    if not a.core_only and (snapshot/'tests/spring_extent_oracle.cpp').exists():targets.append('DisassemblySpringExtentOracle')
    if not a.core_only and (snapshot/'tests/plane_kernel_oracle.cpp').exists():targets.append('DisassemblyPlaneKernelOracle')
    if not a.core_only and (snapshot/'tests/neighbor_kernel_oracle.cpp').exists():targets.append('DisassemblyNeighborKernelOracle')
    if not a.core_only and (snapshot/'tests/radix_extended_oracle.cpp').exists():targets.append('DisassemblyRadixExtendedOracle')
    command([cmake,'--build',binary,'--parallel','4','--target',*targets],a.name+'-compile',env)
    dll=binary/'NvFlexReleaseD3D_x64.dll';ext=Path(read(ROOT/'evidence/baselines.json')['df']['ext']['path']);shutil.copy2(ext,binary/ext.name)
    result=dict(name=a.name,status='PASS',source=str(snapshot),source_manifest=str(ROOT/'evidence'/f'{a.name}-source.json'),dll=str(dll),dll_sha256=sha(dll),ext=str(binary/ext.name),ext_sha256=sha(ext),compiler=str(VC),sdk=SDKVER,targets=targets,cmake_arguments=a.cmake_arg,shader_manifest=str(binary/'generated/shader_manifest.json'),time=now())
    write(receipt,result);register(result);event('build-complete',**result);print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
