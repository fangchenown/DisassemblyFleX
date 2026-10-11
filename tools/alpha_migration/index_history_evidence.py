"""Build a searchable chronological source/idea evidence index, without auto-accepting optimizations."""
import difflib,collections,re,zipfile
from common import *
TEXT={'.cpp','.h','.hpp','.hlsl','.hlsli','.cmake','.py','.ps1','.md','.txt','.json'}
def useful_code(path):
    p=Path(path)
    return (p.parts[0] in ['src','shaders','include','cmake'] or path=='CMakeLists.txt') and p.suffix.lower() in TEXT
def clean_text(b):return decode_text(b).replace('\r','')
def main():
    vs=read(LEDGER/'versions.json');docs=read(ROOT/'history/documents.json');blobroot=ROOT/'history/doc-blobs';blobroot.mkdir(exist_ok=True);unique={};previous=None;delta_rows=[]
    # Offline Git bundles preserve all historical objects even if donor branches move.
    for repo in ['OpenFleX','KG3D_OpenFleX']:
        out=ROOT/'history'/f'{repo}-history.bundle'
        if not out.exists():git(['bundle','create',out,'--all'],WS/repo)
    for v in vs:
        version=v['version'];folder=ROOT/'history'/version
        if (folder/'source-recovery.json').exists():
            source=Path(read(folder/'source-recovery.json')['source']);files={}
            for p in Path(longpath(source)).rglob('*'):
                if not p.is_file():continue
                rel=p.relative_to(Path(longpath(source))).as_posix()
                if useful_code(rel):files[rel]=p.read_bytes()
            if previous is not None:
                changed=[];diff=[]
                for name in sorted(set(previous)|set(files)):
                    before=previous.get(name,b'');after=files.get(name,b'')
                    if before==after:continue
                    generated=('.generated.' in name or name.endswith('.spv'))
                    changed.append(dict(file=name,before_sha256=hashlib.sha256(before).hexdigest() if before else None,after_sha256=hashlib.sha256(after).hexdigest() if after else None,generated=generated))
                    if not generated:diff.extend(difflib.unified_diff(clean_text(before).splitlines(True),clean_text(after).splitlines(True),fromfile='previous/'+name,tofile=version+'/'+name))
                (folder/'OpenFleX-code.patch').write_text(''.join(diff),encoding='utf8');write(folder/'OpenFleX-code-delta.json',changed);delta_rows.append(dict(version=version,repository='OpenFleX',files=len(changed),patch=str(folder/'OpenFleX-code.patch')))
            previous=files
        for repo,aliases in v['git'].items():
            selected=aliases[-1];commit=selected['commit']
            # Root / docs release notes, not every repeated test README.
            paths=git(['ls-tree','-r','--name-only',commit],WS/repo).decode('utf8').splitlines()
            for name in paths:
                p=Path(name)
                if p.suffix.lower() not in ['.md','.txt','.html','.json']:continue
                if not (len(p.parts)==1 or p.parts[0]=='docs'):continue
                oid=git(['rev-parse',commit+':'+name],WS/repo).decode().strip()
                if oid not in unique:
                    data=git(['show',commit+':'+name],WS/repo);target=blobroot/(oid+p.suffix);target.write_bytes(data);unique[oid]=dict(path=str(target),sha256=sha(target))
                docs.append(dict(version=version,kind='git-document',repository=repo,commit=commit,original=name,copy=unique[oid]['path'],sha256=unique[oid]['sha256']))
            delta=v.get('source_delta',{}).get(repo,{})
            prior=delta.get('previous_commit')
            if prior:
                # Module directories were renamed during alpha2.9. A fixed
                # root allowlist silently omits later Body implementation.
                roots=['.']
                patch=git(['diff','--no-ext-diff','--no-color','--unified=3',prior,commit,'--',*roots,':(exclude)**/*.generated.h',':(exclude)**/*.generated.hpp'],WS/repo)
                (folder/(repo+'-code.patch')).write_bytes(patch)
                delta_rows.append(dict(version=version,repository=repo,bytes=len(patch),patch=str(folder/(repo+'-code.patch'))))
        # Newer releases package the full ledger as a zip. Keep all textual
        # evidence with its archive name; do not execute historical instructions.
        for release in map(Path,v['release_roots']):
            for archive in (release/'ledger').glob('*.zip') if (release/'ledger').exists() else []:
                with zipfile.ZipFile(archive) as z:
                    for member in z.infolist():
                        if member.is_dir() or Path(member.filename).suffix.lower() not in ['.md','.json','.txt'] or member.file_size>5_000_000:continue
                        relative=member.filename.replace('\\','/').lstrip('/');assert ':' not in relative and '..' not in Path(relative).parts
                        target=folder/'packaged-ledgers'/archive.stem/relative;lp=Path(longpath(target));lp.parent.mkdir(parents=True,exist_ok=True);lp.write_bytes(z.read(member))
                        docs.append(dict(version=version,kind='packaged-ledger',original=str(archive)+'!'+relative,copy=str(target),sha256=sha(target)))
    write(ROOT/'history/documents-expanded.json',docs);write(ROOT/'history/source-deltas.json',delta_rows)
    # Extract evidence paragraphs, not decisions. Human/model review must assign
    # eligibility and candidate mappings; historical KEEP is not DF acceptance.
    clues=[];seen=set()
    pattern=re.compile(r'(?i)优化|候选|保留|拒绝|未采用|回退|收益|下降|改动|变更|\bKEEP\b|\bKEPT\b|\bREJECTED\b|optimization|reuse|cache|dispatch|binding')
    for doc in docs:
        p=Path(longpath(doc['copy']))
        if p.suffix.lower() not in ['.md','.txt']:continue
        text=clean_text(p.read_bytes())
        for match in re.finditer(r'(?s)(?:\A|(?<=\n\n))([^\n].*?)(?=\n\s*\n|\Z)',text):
            paragraph=match.group(1);line=text.count('\n',0,match.start(1))+1
            sig=(doc['version'],hashlib.sha256(paragraph.encode()).hexdigest())
            if sig not in seen and pattern.search(paragraph) and len(paragraph)<16000:
                clues.append(dict(version=doc['version'],document=doc['copy'],line=line,text=paragraph,kind=doc['kind'],status='unreviewed-evidence'));seen.add(sig)
    write(ROOT/'history/optimization-evidence.json',clues)
    event('history-evidence-indexed',documents=len(docs),unique_git_docs=len(unique),source_deltas=len(delta_rows),paragraphs=len(clues))
    print(json.dumps(dict(documents=len(docs),unique_git_docs=len(unique),source_deltas=len(delta_rows),paragraphs=len(clues))))
if __name__=='__main__':main()
