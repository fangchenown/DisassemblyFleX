"""Pin Microsoft's DXBC container hash implementation and its license."""
import hashlib,json,urllib.request
from pathlib import Path
from ledger import PROJECT,write_json
root=PROJECT/'tools/third_party/dxc_hash';root.mkdir(parents=True,exist_ok=True)
headers={'User-Agent':'DisassemblyFleX-reconstruction'}
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=60).read()
records=[]
api='https://api.github.com/repos/microsoft/DirectXShaderCompiler/commits?path=lib/DxilHash/DxilHash.cpp&per_page=1'
commit=json.loads(get(api))[0]['sha']
for filename,repo_path in [('DxilHash.cpp','lib/DxilHash/DxilHash.cpp'),('LICENSE.TXT','LICENSE.TXT')]:
    url=f'https://raw.githubusercontent.com/microsoft/DirectXShaderCompiler/{commit}/{repo_path}'
    data=get(url);(root/filename).write_bytes(data);records.append({'file':filename,'url':url,'sha256':hashlib.sha256(data).hexdigest()})
write_json(root/'provenance.json',{'repository':'microsoft/DirectXShaderCompiler','commit':commit,'files':records})
print('Pinned DXBC hash source at',commit)
