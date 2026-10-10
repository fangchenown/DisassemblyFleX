"""Pin the existing official-scene headless harness into this independent task."""
import hashlib,re,shutil
from pathlib import Path
from ledger import PROJECT,write_json,event
WS=PROJECT.parent
source=WS/'Build/OpenFlexAlpha82c-20260928/bin'
dest=PROJECT/'tests/demo';dest.mkdir(exist_ok=True)
records=[]
for name in ['headless.cpp','render_stubs.cpp','api_shim.cpp','DiagnosticProbe.h']:
    original=(source/name).read_bytes();text=original.decode('utf-8')
    if name=='headless.cpp':
        start=text.index('void ApplyDiagnosticParameters(){')
        end=text.index('void Snapshot(int frame){',start)
        text=text[:start]+'void ApplyDiagnosticParameters() {} // Original scene parameters are preserved.\n'+text[end:]
        old='openMode=std::string(argv[3])!="nv" && std::string(argv[3])!="cuda";'
        assert old in text;text=text.replace(old,'openMode=false; // Both oracle and reconstruction expose NvFlex API names.')
        old='desc.computeType=std::string(argv[3])=="vk"?(NvFlexComputeType)3:(std::string(argv[3])=="cuda"?eNvFlexCUDA:eNvFlexD3D11);'
        assert old in text;text=text.replace(old,'desc.computeType=std::string(argv[3])=="d3d12"?eNvFlexD3D12:eNvFlexD3D11;')
        # Explicit opt-out of vendor extensions is only a separate oracle mode;
        # reference/candidate runs must use the identical flag.
        text=text.replace('desc.deviceIndex=0;desc.enableExtensions=true;','desc.deviceIndex=0;desc.enableExtensions=std::string(argv[3])!="d3d11-generic";')
    if name=='DiagnosticProbe.h':
        text=text.replace('probePrewait=strcmp(probeExperiment,"prewait")==0;','probePrewait=false;')
        text=text.replace('probeNoUpload=strcmp(probeExperiment,"no_upload")==0;','probeNoUpload=false;')
        text=text.replace('probeResident=strcmp(probeExperiment,"resident")==0;','probeResident=false;')
        text=text.replace('probeCopies=getenv("DEMO_COPY_PROBE")!=nullptr;','probeCopies=false;')
    target=dest/name
    if target.exists():raise RuntimeError('Already imported '+str(target))
    target.write_text(text,encoding='utf-8')
    records.append({'file':name,'input':str(source/name),'input_sha256':hashlib.sha256(original).hexdigest(),'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
power=WS/'Build/OpenFlexAlpha82c-20260928/tools/benchmark_power.py'
shutil.copyfile(power,PROJECT/'tools/locksafe_power.py')
records.append({'file':'locksafe_power.py','input':str(power),'input_sha256':hashlib.sha256(power.read_bytes()).hexdigest()})
for directory in ('demo','core','include'):
    for p in sorted((WS/'FleX'/directory).rglob('*')):
        if p.is_file() and p.suffix in ('.cpp','.h'):
            records.append({'official_input':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
write_json(PROJECT/'reference/demo_provenance.json',{'records':records,'scope':'Official scene registry/Init/Update code with renderer stubs and full-frequency headless entry; diagnostic parameter and upload-skip controls disabled.'})
event('headless-demo-imported','已固定官方场景无窗口驱动，禁止输入参数改写和跳帧/跳上传诊断。',files=len(records))
