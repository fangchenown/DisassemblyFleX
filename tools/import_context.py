import hashlib,json
from pathlib import Path
from ledger import PROJECT,write_json,event
destination=PROJECT/'src/dx/context';destination.mkdir(parents=True,exist_ok=True)
records=[]
for source in (PROJECT.parent/'FleX/src/dx/context').glob('*.h'):
    text=source.read_text(encoding='utf-8');original=text
    if source.name=='Context.h':
        text=text.replace('#include "Vector.h"','// VectorCached is included after Allocable is declared.')
        text+='\n#include "Vector.h"\n'
        text=text.replace('wchar_t* shaderLabel = L""','const wchar_t* shaderLabel = L""')
    if source.name=='Device.h':text=text.replace('#include "../../include/NvFlex.h"','#include "NvFlex.h"')
    target=destination/source.name
    if target.exists():raise RuntimeError('Context headers already copied')
    target.write_text(text,encoding='utf-8')
    records.append({'file':source.name,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                    'adaptation':text!=original,'adapted_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
write_json(PROJECT/'reference/context_headers.json',records)
event('context-interfaces-pinned','保留SDK内部Device/Context虚接口以兼容官方FlexExt；仅修复包含顺序和公共头路径。',files=len(records))
