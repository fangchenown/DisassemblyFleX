"""Compose independently tested branches with explicit, audited three-way merges."""
import argparse
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',required=True);p.add_argument('--components',required=True);p.add_argument('--split-radix-oracle',action='store_true');a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name;assert not dest.exists();shutil.copytree(base,dest)
changed={};records=[]
for name in a.components.split(','):
    source=Path(read(ROOT/'evidence'/f'{name}-build.json')['source']);delta=[]
    paths={p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}|{p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
    for rel in sorted(paths):
        old,new,target=base/rel,source/rel,dest/rel;before=sha(old) if old.exists() else None;after=sha(new) if new.exists() else None
        if before==after:continue
        assert after is not None,'Explicit deletion review required: '+rel
        mode='copy'
        if rel in changed and sha(target)!=after:
            if rel=='shaders/auxiliary/registry.json':
                registry=read(target);by_name={r['name']:r for r in registry}
                for row in read(new):
                    if row['name'] in by_name:assert by_name[row['name']]==row,'Conflicting auxiliary shader '+row['name']
                    else:registry.append(row);by_name[row['name']]=row
                write(target,registry);mode='registry-union-identical-duplicates'
            else:
                assert old.exists(),'Conflicting new files require explicit review: '+rel
                result=subprocess.run(['git','merge-file','--stdout',str(target),str(old),str(new)],env=clean_env(ROOT/'temp/compose'),capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode:
                    diagnostic=ROOT/'evidence'/f'{a.name}-{len(records)}-conflict.txt';diagnostic.write_bytes(result.stdout)
                    raise RuntimeError('Manual source conflict review required: '+rel+'; '+str(diagnostic))
                target.write_bytes(result.stdout);mode='clean-three-way-merge'
        elif rel not in changed:
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(new,target)
        else:mode='identical-overlap'
        changed[rel]=sha(target);delta.append(dict(file=rel,base_sha256=before,component_sha256=after,result_sha256=sha(target),mode=mode))
    records.append(dict(candidate=name,changes=delta))
if a.split_radix_oracle:
    assert (dest/'tests/radix_oracle.cpp').read_bytes()!=(base/'tests/radix_oracle.cpp').read_bytes()
    shutil.copy2(Path(__file__).parent/'templates/radix_extended_oracle.cpp',dest/'tests/radix_extended_oracle.cpp')
    shutil.copy2(base/'tests/radix_oracle.cpp',dest/'tests/radix_oracle.cpp')
    with (dest/'CMakeLists.txt').open('a',encoding='utf8') as f:f.write('''
add_executable(DisassemblyRadixExtendedOracle tests/radix_extended_oracle.cpp)
target_compile_features(DisassemblyRadixExtendedOracle PRIVATE cxx_std_17)
target_compile_definitions(DisassemblyRadixExtendedOracle PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN _CRT_SECURE_NO_WARNINGS)
target_include_directories(DisassemblyRadixExtendedOracle PRIVATE include src "${DISASSEMBLYFLEX_WORKSPACE}/FleX")
''')
    for rel in ['CMakeLists.txt','tests/radix_oracle.cpp','tests/radix_extended_oracle.cpp']:changed[rel]=sha(dest/rel)
receipt=dict(base=a.base,components=records,source=str(dest),files=changed,split_radix_oracle=a.split_radix_oracle,time=now(),requires_fresh_integrated_validation=True)
write(ROOT/'evidence'/f'{a.name}-composition.json',receipt);event('reviewed-composition',name=a.name,base=a.base,components=a.components.split(','),files=len(changed));print('Composed',len(changed),'files; fresh validation required.')
