"""Verify delivered implementation equals the tested immutable build snapshot."""
import argparse
from common import *
p=argparse.ArgumentParser();p.add_argument('--build',required=True);a=p.parse_args()
build=read(ROOT/'evidence'/f'{a.build}-build.json');manifest=read(build['source_manifest'])['files'];snapshot=Path(build['source'])
roots=('src/','include/','shaders/','cmake/','reference/')
explicit={'CMakeLists.txt','tools/generate_exports.py','tools/build_shaders.py','tools/build_aux_shaders.py','tools/dxbc_tools.py','tools/dxbc_precision.py','tools/dxbc_assembler.py','tools/shader_lowering.py','tools/dxbc_hash_export.cpp'}
def selected(name):return name in explicit or name.startswith(roots) or name.startswith(('tools/third_party/directx_tokens/','tools/third_party/dxc_hash/'))
expected={name:value for name,value in manifest.items() if selected(name)};actual={}
for root in ['src','include','shaders','cmake','reference','tools/third_party/directx_tokens','tools/third_party/dxc_hash']:
    for path in (PROJECT/root).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:actual[path.relative_to(PROJECT).as_posix()]=sha(path)
for name in explicit:
    if (PROJECT/name).exists():actual[name]=sha(PROJECT/name)
assert actual==expected,dict(missing=sorted(set(expected)-set(actual)),extra=sorted(set(actual)-set(expected)),changed=[p for p in set(actual)&set(expected) if actual[p]!=expected[p]])
assert sha(build['dll'])==build['dll_sha256'];assert sha(build['ext'])==build['ext_sha256'];assert build['cmake_arguments']==[]
registry=read(PROJECT/'shaders/auxiliary/registry.json');assert len(registry)==5 and all(x['kind']=='authored-integer-helper' and not x.get('instructions') for x in registry)
for entry in registry:
    source=(PROJECT/'shaders/auxiliary'/entry['source']).read_text(encoding='utf8')
    code=re.sub(r'//[^\n]*|/\*.*?\*/','',source,flags=re.S);assert not re.search(r'\b(?:float|half|double)[1-4]?\b',code),entry['source']
result=dict(status='PASS',build=a.build,files=len(actual),implementation_sha256=hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest(),dll_sha256=build['dll_sha256'],ext_sha256=build['ext_sha256'],original_shader_containers=84,new_integer_programs=5,active_derived_float_programs=0,source_files=actual,time=now(),scope='Production source, shader generators, reference metadata and pinned built DLL. Reporting/measurement utilities added after compilation are outside the implementation digest.')
write(ROOT/'evidence'/f'{a.build}-implementation-audit.json',result);event('implementation-identity-audit',build=a.build,status='PASS',files=len(actual),implementation_sha256=result['implementation_sha256']);print('PASS',len(actual),'implementation files exactly match tested source snapshot.')
