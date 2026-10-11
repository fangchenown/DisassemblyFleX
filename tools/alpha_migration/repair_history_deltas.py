"""Fix the nested KG mirror filter and bridge recovered alpha2.1 to first Git tag."""
import difflib
from common import *
vs=read(LEDGER/'versions.json');records=[]
for v in vs:
    for repo in ['OpenFleX','KG3D_OpenFleX']:
        delta=v.get('source_delta',{}).get(repo,{});prior=delta.get('previous_commit')
        if not prior:continue
        target=ROOT/'history'/v['version']/(repo+'-code.patch');previous=target.with_name(repo+'-code.previous-filter.patch')
        if target.exists() and not previous.exists():shutil.copy2(target,previous)
        patch=git(['diff','--no-ext-diff','--no-color','--unified=3',prior,delta['commit'],'--','.',':(exclude)**/*.generated.h',':(exclude)**/*.generated.hpp'],WS/repo);target.write_bytes(patch)
        records.append(dict(version=v['version'],repository=repo,bytes=len(patch),sha256=sha(target),path=str(target),original_filter_receipt=str(previous),reason='Full tree handles embedded modules, alpha2.9 directory renames, ABI and build-tool changes; generated headers omitted but complete Git bundles and changed-file lists retained. No donor source changed.'))
v=next(x for x in vs if x['version']=='alpha2.2');commit=v['git']['OpenFleX'][-1]['commit'];previous=ROOT/'history/alpha2.1/source/OpenFleX';paths=git(['ls-tree','-r','--name-only',commit],WS/'OpenFleX').decode().splitlines()
def useful(path):
    p=Path(path)
    return (p.parts[0] in ['src','shaders','include','cmake'] or path=='CMakeLists.txt') and p.suffix in ['.cpp','.h','.hpp','.hlsl','.hlsli','.cmake','.txt'] and '.generated.' not in path
before={p.relative_to(Path(longpath(previous))).as_posix():p.read_bytes() for p in Path(longpath(previous)).rglob('*') if p.is_file() and useful(p.relative_to(Path(longpath(previous))).as_posix())}
after={p:git(['show',commit+':'+p],WS/'OpenFleX') for p in paths if useful(p)};diff=[];changes=[]
for path in sorted(set(before)|set(after)):
    x=before.get(path,b'');y=after.get(path,b'')
    if x==y:continue
    changes.append(dict(file=path,before_sha256=hashlib.sha256(x).hexdigest() if x else None,after_sha256=hashlib.sha256(y).hexdigest() if y else None))
    diff.extend(difflib.unified_diff(decode_text(x).replace('\r','').splitlines(True),decode_text(y).replace('\r','').splitlines(True),fromfile='alpha2.1/'+path,tofile='alpha2.2/'+path))
target=ROOT/'history/alpha2.2/OpenFleX-code.patch';target.write_text(''.join(diff),encoding='utf8');write(target.with_name('OpenFleX-code-delta.json'),changes)
records.append(dict(version='alpha2.2',repository='OpenFleX',path=str(target),sha256=sha(target),bytes=target.stat().st_size,files=len(changes),reason='Bridge the independently manifest-verified alpha2.1 release to the first available alpha2.2 Git tag.'))
write(ROOT/'history/corrected-source-deltas.json',records);event('source-delta-index-repaired',versions=len(records));print('Corrected',len(records),'source-delta entries.')
