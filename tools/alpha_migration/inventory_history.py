"""Enumerate every alpha release, alias tag and ledger using read-only local evidence."""
import csv,base64,zipfile,re,collections
from common import *
ARCH=WS/'Build/WorkspaceArchive-20260905'
def version_key(s):
    m=re.fullmatch(r'alpha(\d+)\.(\d+)([a-z]?)(.*)',s);assert m,s
    return int(m[1]),int(m[2]),m[3],m[4]
def canonical(s):
    m=re.search(r'alpha\d+\.\d+[a-z]?(?:-mix4)?',s,re.I);return m[0].lower() if m else None
def history_version(name):
    if name.lower().startswith('openflexalpharelease'):return 'alpha0.1'
    m=re.match(r'OpenFlexAlpha(\d+)([a-z]?)(?=[A-Z]|[-_])',name,re.I)
    if not m:return None
    # Prefixes encode alpha0.2 as 02 and alpha8.2c as 82c. A lower-case suffix
    # is accepted only before a capitalized descriptive word.
    m=re.match(r'(?i:OpenFlexAlpha)(\d+)([a-z]?)(?=[A-Z]|[-_])',name)
    if not m:return None
    d=m[1];return 'alpha'+str(int(d[:-1]))+'.'+d[-1]+m[2] if len(d)>1 else None
def selected_doc(p):
    return p.suffix.lower() in ['.md','.txt','.html','.json'] and p.stat().st_size<5_000_000
def main():
    versions={}
    def row(v):return versions.setdefault(v,dict(version=v,order_key=version_key(v),git={},release_roots=[],history_roots=[],archive=None,status='discovered',optimization_ids=[]))
    for d in csv.DictReader((WS/'Release/ARCHIVED_VERSIONS.csv').open(encoding='utf-8-sig')):
        v=d['Version'];record=read(ARCH/f'receipts/release/{v}.json');manifest=ARCH/f'manifests/release/{v}.tsv'
        assert sha(manifest)==record['ManifestSHA256'].lower()
        row(v)['archive']=dict(snapshot=record['Snapshot'],subfolder=record['SnapshotSubfolder'],manifest=str(manifest),manifest_sha256=sha(manifest),files=record['Files'],bytes=record['Bytes'])
    for repo_name in ['OpenFleX','KG3D_OpenFleX']:
        repo=WS/repo_name
        tags=git(['tag','--list','*alpha*'],repo).decode().splitlines()
        for tag in tags:
            v=canonical(tag);assert v,tag
            entry=dict(tag=tag,commit=git(['rev-parse',tag+'^{commit}'],repo).decode().strip(),tree=git(['rev-parse',tag+'^{tree}'],repo).decode().strip(),date=git(['show','-s','--format=%cI',tag+'^{commit}'],repo).decode().strip())
            row(v)['git'].setdefault(repo_name,[]).append(entry)
    for root in [WS/'Release',WS/'Deleted/WorkspaceSlimming-20260905/Release']:
        for p in root.iterdir():
            if p.is_dir() and re.fullmatch(r'alpha\d+\.\d+[a-z]?(?:-mix4)?',p.name):row(p.name)['release_roots'].append(str(p))
    unmapped=[]
    for p in (WS/'History').iterdir():
        if not p.is_dir() or not p.name.lower().startswith('openflexalpha'):continue
        v=history_version(p.name)
        if not v:unmapped.append(p.name);continue
        row(v)['history_roots'].append(str(p))
    # Preserve ledger documents in the new task root, with independent hashes.
    documents=[]
    for v,r in sorted(versions.items(),key=lambda x:version_key(x[0])):
        dest=ROOT/'history'/v;dest.mkdir(exist_ok=True)
        for root in map(Path,r['history_roots']):
            for p in root.rglob('*'):
                if not p.is_file() or not selected_doc(p):continue
                target=dest/'ledgers'/root.name/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
                documents.append(dict(version=v,kind='archived-ledger',original=str(p),copy=str(target),sha256=sha(p)))
        for root in map(Path,r['release_roots']):
            candidates=[root/x for x in ['README_CN.md','README.md','PACKAGE_NOTES_CN.md','VERSION.json','RELEASE_STATUS.json','REPORT_CN.html','OpenFleX/release_notes.txt','OpenFleX/README.md']]
            if (root/'ledger').exists():candidates.extend((root/'ledger').glob('*.md'))
            for p in candidates:
                if not p.is_file() or not selected_doc(p):continue
                target=dest/'release-docs'/root.name/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
                if not target.exists():shutil.copy2(p,target)
                documents.append(dict(version=v,kind='release-document',original=str(p),copy=str(target),sha256=sha(p)))
        for repo,entries in r['git'].items():
            previous=[x for x in versions.values() if version_key(x['version'])<version_key(v) and repo in x['git']]
            prev=max(previous,key=lambda x:version_key(x['version'])) if previous else None
            current=entries[-1]['commit']
            if prev:
                prior=prev['git'][repo][-1]['commit']
                changes=git(['diff','--name-status',prior,current],WS/repo).decode('utf8',errors='replace')
                stats=git(['diff','--shortstat',prior,current],WS/repo).decode('utf8',errors='replace').strip()
            else:prior=None;changes=git(['ls-tree','-r','--name-only',current],WS/repo).decode('utf8',errors='replace');stats='First locally tagged source state'
            (dest/(repo+'-changed-files.txt')).write_text(changes,encoding='utf8')
            r.setdefault('source_delta',{})[repo]=dict(previous_version=prev['version'] if prev else None,previous_commit=prior,commit=current,statistics=stats,identical_tree=bool(prev and prev['git'][repo][-1]['tree']==entries[-1]['tree']),changed_files=str(dest/(repo+'-changed-files.txt')))
    ordered=[dict(r,sequence=i+1) for i,(v,r) in enumerate(sorted(versions.items(),key=lambda x:version_key(x[0])))]
    write(ROOT/'history/documents.json',documents);write(ROOT/'history/version-inventory.json',ordered);write(ROOT/'history/unmapped-history-directories.json',unmapped)
    write(LEDGER/'versions.json',ordered);state(phase='chronological-history-review',current_version=ordered[0]['version'])
    event('history-inventory',versions=len(ordered),documents=len(documents),unmapped=unmapped)
    print(json.dumps(dict(versions=len(ordered),first=ordered[0]['version'],last=ordered[-1]['version'],documents=len(documents),unmapped=unmapped),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
