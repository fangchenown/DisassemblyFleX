import collections
import fix_benchmark as fix
from performance_shader_audit import scan
def main():
    b=fix.configure('final-v2');data={name:scan(path) for name,path in b.CORES.items()};programs={name:collections.Counter(chunk['sha256'] for shader in rows for chunk in shader['programs']) for name,rows in data.items()}
    result=dict(dll_sha256={name:b.sha(path) for name,path in b.CORES.items()},containers={name:len(rows) for name,rows in data.items()},all_programs_equal=programs['reference']==programs['legacy']==programs['candidate'],programs=data)
    b.write(b.ROOT/'evidence/shader-audit-final-v2.json',result);assert result['all_programs_equal'] and all(n==84 for n in result['containers'].values());print('84 executable shader programs identical in all three DLLs')
if __name__=='__main__':main()
