"""Compact source-grounded reading aid; never assigns acceptance automatically."""
import argparse,re
from common import *
p=argparse.ArgumentParser();p.add_argument('versions',nargs='+');p.add_argument('--limit',type=int,default=14000);a=p.parse_args()
documents=read(ROOT/'history/documents-expanded.json');inventory=read(LEDGER/'versions.json')
for version in a.versions:
    v=next(x for x in inventory if x['version']==version);print('\nVERSION',version,'SEQUENCE',v['sequence'])
    ds=[d for d in documents if d['version']==version]
    primary=[d for d in ds if '/phases/' in d['copy'].replace('\\','/') and d['copy'].endswith('.md')]
    if not primary:primary=[d for d in ds if Path(d['copy']).name.startswith(('00_','01_','02_','04_','05_')) and d['copy'].endswith('.md')]
    used=set();budget=a.limit
    for d in primary:
        text=decode_text(Path(longpath(d['copy'])).read_bytes())
        lines=[]
        for no,line in enumerate(text.splitlines(),1):
            if line in used:continue
            if (line.startswith('|') and re.search(r'(?i)keep|reject|候选|优化|C\d\d|cache|reuse|copy|dispatch|[快慢]|收益|剔除',line)) or line.startswith('#'):
                lines.append(f'{no}: {line}');used.add(line)
        if lines and budget>0:
            result='\n'.join(lines)[:budget];print('DOCUMENT',d['copy']);print(result);budget-=len(result)
    for repo in ['OpenFleX','KG3D_OpenFleX']:
        delta=v.get('source_delta',{}).get(repo,{})
        patch=ROOT/'history'/version/(repo+'-code.patch')
        if patch.exists():
            text=patch.read_text(encoding='utf8',errors='replace');files=re.findall(r'^\+\+\+ (?:b/|'+re.escape(version)+r'/)(.*)$',text,re.M)
            print('SOURCE_DELTA',repo,'patch_bytes',patch.stat().st_size,'files',json.dumps(files,ensure_ascii=False))
        if delta:print('GIT_DELTA',json.dumps(delta,ensure_ascii=False)[:2000])
