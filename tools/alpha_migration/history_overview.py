"""Read candidate/fix evidence with bounded output; never auto-classify or accept it."""
import argparse,re
from common import *
p=argparse.ArgumentParser();p.add_argument('versions',nargs='+');p.add_argument('--limit',type=int,default=6000);a=p.parse_args();docs=read(ROOT/'history/documents-expanded.json');versions=read(LEDGER/'versions.json')
for version in a.versions:
    v=next(x for x in versions if x['version']==version);print('\nVERSION',version)
    for repo,delta in v.get('source_delta',{}).items():
        patch=ROOT/'history'/version/(repo+'-code.patch');files=[]
        if patch.exists():
            for file in re.findall(r'^\+\+\+ b/(.+)$',patch.read_text(encoding='utf8',errors='replace'),re.M):
                if Path(file).suffix.lower() in ['.cpp','.h','.hpp','.hlsl','.hlsli','.cmake','.props','.targets'] or Path(file).name=='CMakeLists.txt':files.append(file)
        print(repo,'same_tree=',delta.get('identical_tree'),'code_files=',json.dumps(files,ensure_ascii=False)[:1800])
    choices=[]
    for d in docs:
        name=Path(d['copy']).name.lower()
        if d['version']==version and '/phases/' in d['copy'].replace('\\','/') and name.endswith('.md') and re.search(r'cause|design|implement|optim|fix|candidate|repair|neighbors|rigids|triangles|springs|particles|submission|grid|waves|results|retained',name):choices.append(d)
    if not choices:choices=[d for d in docs if d['version']==version and Path(d['copy']).name in ['00_CURRENT.md','FINAL_REPORT.md']]
    budget=a.limit
    for d in choices:
        content=decode_text(Path(longpath(d['copy'])).read_bytes());print('DOC',d.get('original',d['copy']));
        if len(content)<=budget:print(content);budget-=len(content)
        elif budget>0:print(content[:budget//2]+'\n[... bounded excerpt ...]\n'+content[-budget//2:]);budget=0
