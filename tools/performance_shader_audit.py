"""Independently compare executable shader chunks embedded in the tested PEs."""
import struct,hashlib,collections
import performance_benchmark as b
def scan(path):
    raw=path.read_bytes();offset=0;found=[]
    while True:
        offset=raw.find(b'DXBC',offset)
        if offset<0:break
        try:
            version,size,count=struct.unpack_from('<III',raw,offset+20)
            assert version==1 and 1<=count<32 and 32+count*4<=size<=len(raw)-offset
            chunks=[]
            for i in range(count):
                location=struct.unpack_from('<I',raw,offset+32+4*i)[0]
                assert 32+count*4<=location<=size-8
                tag,length=struct.unpack_from('<4sI',raw,offset+location);assert location+8+length<=size
                if tag in [b'SHEX',b'SHDR']:
                    code=raw[offset+location+8:offset+location+8+length]
                    chunks.append(dict(tag=tag.decode(),bytes=length,sha256=hashlib.sha256(code).hexdigest()))
            if chunks:found.append(dict(file_offset=offset,container_bytes=size,programs=chunks))
        except (AssertionError,struct.error):pass
        offset+=4
    return found
def main():
    data={k:scan(p) for k,p in b.CORES.items()}
    programs={k:collections.Counter(c['sha256'] for shader in v for c in shader['programs']) for k,v in data.items()}
    result=dict(dll_sha256={k:b.sha(p) for k,p in b.CORES.items()},containers={k:len(v) for k,v in data.items()},program_multiset_equal=programs['reference']==programs['candidate'],data=data)
    b.write(b.ROOT/'evidence/shader-program-audit.json',result)
    print({k:v for k,v in result.items() if k!='data'});assert result['program_multiset_equal'] and result['containers']==dict(reference=84,candidate=84)
if __name__=='__main__':main()
