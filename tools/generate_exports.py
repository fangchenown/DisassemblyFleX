"""Make the exact 93-name export surface; missing implementations fail loudly.

Every missing implementation remains a failing acceptance item. The temporary
fail-fast bodies must reach zero before the DLL can be accepted or delivered.
"""
import csv,json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((P/'reference/exports.csv').open(encoding='utf-8-sig')))
header=(P/'include/NvFlex.h').read_text(encoding='utf-8')
header=re.sub(r'/\*.*?\*/|//[^\n]*','',header,flags=re.S)
decls={name:(ret.strip(),re.sub(r'\s*=\s*[^,]+','',params.strip()))
       for ret,name,params in re.findall(r'NV_FLEX_API\s+([\w* ]+?)\s+(NvFlex\w+)\(([^;{}]*)\);',header,re.S)}
restored=set()
implemented=set()
for source in (P/'src').rglob('*.cpp'):
    restored.update(re.findall(r'DF_RESTORED: (NvFlex\w+)',source.read_text(encoding='utf-8')))
    implemented.update(re.findall(r'DF_IMPLEMENTED: (NvFlex\w+)',source.read_text(encoding='utf-8')))
implemented.update(restored)
code=['#include "NvFlex.h"','#include <windows.h>','#include <cstdio>',
      '[[noreturn]] static void Unrestored(const char* name) { std::fprintf(stderr,"DISASSEMBLYFLEX_UNRESTORED:%s\\n",name); std::fflush(stderr); TerminateProcess(GetCurrentProcess(),0x7d); __assume(0); }']
definitions=['LIBRARY NvFlexReleaseD3D_x64','EXPORTS'];inventory=[]
for row in rows:
    exported=row['name'];name=exported.split('@')[0][1:] if exported.startswith('?') else exported
    special=exported.startswith('?') or name.startswith('NvFlexMake')
    implementation='DF_'+name if special else name
    definitions.append(f'    {exported}={implementation} @{row["ordinal"]}')
    ready=name in restored
    inventory.append({'export':exported,'ordinal':int(row['ordinal']),'implementation':implementation,'restored':ready,'implemented':name in implemented,'rva':row['rva']})
    if name in implemented:continue
    if exported.startswith('?'):
        ret='int';params='NvFlexLibrary* lib, unsigned id' if 'TriangleMesh' in name else 'const NvFlexSolver* solver'
    else:
        ret,params=decls[name]
    code.append(f'extern "C" {ret} {implementation}({params}) {{ Unrestored("{name}"); }}')
missing=sum(not r['implemented'] for r in inventory)
if not missing:code=['#include "NvFlex.h"','// All 93 exports have source implementations; no fail-fast stubs.']
(OUT/'UnrestoredApi.cpp').write_text('\n'.join(code)+'\n',encoding='utf-8')
(OUT/'NvFlex.def').write_text('\n'.join(definitions)+'\n',encoding='utf-8')
(OUT/'api_inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
print('Export surface:',len(rows),'implemented:',sum(r['implemented'] for r in inventory),'basic direct-oracle verified:',sum(r['restored'] for r in inventory),'missing:',missing)
