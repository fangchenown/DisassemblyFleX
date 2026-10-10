import argparse,json,struct
from pathlib import Path
from ledger import PROJECT,write_json
def main():
    parser=argparse.ArgumentParser();parser.add_argument('trace',type=Path);args=parser.parse_args();root=args.trace
    rows=[json.loads(l) for l in (root/'context.jsonl').read_text(encoding='utf-8').splitlines()]
    shader_index=json.loads((PROJECT.parent/'Build/NvFlexDisassembly-20261009/shaders/index.json').read_text(encoding='utf-8'))
    shader_names={int(r['rva'],16):r['name'] for r in shader_index}
    labels={r['id']:r['name'] for r in rows if r['op']=='solver_field' and r['id']}
    objects={r['id']:r for r in rows if r['op'] in ('buffer','constant')}
    for oid,obj in objects.items():
        if obj.get('label','').startswith('library+'):
            labels[oid]={744:'mCellBucketStarts',776:'mCellBucketEnds',344:'clearIntCB',368:'clearFloat4CB',816:'triMeshInfoCB'}.get(int(obj['label'][8:]),obj['label'])
    shaders={};mapped={};dispatches=[]
    def named(oid):return labels.get(oid,'id'+str(oid)) if oid else None
    for row in rows:
        if row['op']=='shader':shaders[row['id']]=shader_names.get(row['rva'],row['label'])
        if row['op']=='mapped_bytes':mapped[row['id']]=row['file']
        if row['op'] in ('dispatch','dispatchIndirect'):
            cb=[]
            for oid in row['cb']:
                entry={'id':oid,'name':named(oid),'file':mapped.get(oid)}
                if oid in mapped:
                    data=(root/mapped[oid]).read_bytes()
                    if len(data)<=64:entry['words']=list(struct.unpack('<'+'I'*(len(data)//4),data))
                cb.append(entry)
            dispatches.append({'sequence':row['sequence'],'phase':row['phase'],'op':row['op'],'shader':shaders.get(row['shader'],row['shader']),
                               'grid':row['grid'],'cb':cb,'reads':{str(i):named(x) for i,x in enumerate(row['reads']) if x},
                               'writes':{str(i):named(x) for i,x in enumerate(row['writes']) if x}})
    result={'dispatches':dispatches,'objects':objects,'labels':labels}
    write_json(root/'analysis.json',result)
    text=[]
    for row in dispatches:
        text.append(f"{row['sequence']:04d} {row['phase']} {row['shader']} grid={row['grid']}")
        text.append('  SRV '+str(row['reads'])+' UAV '+str(row['writes']))
        text.append('  CB '+str(row['cb']))
    (root/'dispatches.txt').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print('Dispatches',len(dispatches));print('\n'.join(text[:45]))
if __name__=='__main__':main()
