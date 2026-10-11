"""Recover early OpenFleX source snapshots into this task only, verifying archived hashes."""
import zipfile,base64,csv,argparse
from common import *
ARCH=WS/'Build/WorkspaceArchive-20260905'
def main():
    p=argparse.ArgumentParser();p.add_argument('--versions',default=','.join(['alpha0.'+str(i) for i in range(1,10)]+['alpha1.'+str(i) for i in range(10)]+['alpha2.0','alpha2.1']));a=p.parse_args()
    exe=ARCH/'tools/restic_0.19.1_windows_amd64.exe';all_receipts=[]
    for v in a.versions.split(','):
        record=read(ARCH/f'receipts/release/{v}.json');manifest=ARCH/f'manifests/release/{v}.tsv';assert sha(manifest)==record['ManifestSHA256'].lower()
        folder=record['SnapshotSubfolder'].rstrip('/')+'/OpenFleX/source/OpenFleX';archive=ROOT/'history'/v/'OpenFleX-source.zip';archive.parent.mkdir(exist_ok=True)
        if not archive.exists():
            command([exe,'--repo',ARCH/'repository','--insecure-no-password','--no-lock','--cache-dir',ROOT/'history/restic-cache','dump','--archive','zip','--target',archive,record['Snapshot']+':'+folder,'/'],v+'-recover-source')
        dest=ROOT/'history'/v/'source/OpenFleX';dest.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                if member.is_dir():continue
                relative=member.filename.replace('\\','/').lstrip('/')
                assert ':' not in relative and '..' not in Path(relative).parts
                target=dest/relative;assert dest.resolve() in target.resolve().parents
                target_long=Path(longpath(target))
                if not target_long.exists():target_long.parent.mkdir(parents=True,exist_ok=True);target_long.write_bytes(z.read(member))
        prefix='OpenFleX\\source\\OpenFleX\\';verified=0
        with manifest.open(encoding='utf-8-sig') as fd:
            next(fd)
            for line in fd:
                f=line.rstrip('\n').split('\t')
                if f[0]!='F':continue
                name=base64.b64decode(f[1]).decode('utf8')
                if not name.startswith(prefix):continue
                path=Path(longpath(dest/Path(name[len(prefix):])));assert path.exists(),str(path);assert path.stat().st_size==int(f[2]) and sha(path)==f[5].lower(),str(path);verified+=1
        count=sum(p.is_file() for p in Path(longpath(dest)).rglob('*'));assert count==verified,(v,count,verified)
        receipt=dict(version=v,snapshot=record['Snapshot'],source=str(dest),files=verified,archive_sha256=sha(archive),manifest_sha256=sha(manifest),status='PASS');write(ROOT/'history'/v/'source-recovery.json',receipt);all_receipts.append(receipt);event('early-source-recovered',**receipt);print(v,verified,'verified',flush=True)
    write(ROOT/'history/early-source-recoveries.json',all_receipts)
if __name__=='__main__':main()
