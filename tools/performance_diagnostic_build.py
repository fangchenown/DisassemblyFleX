"""Build an isolated shared Context timing proxy for both tested DLLs."""
import json, os, re, shutil, subprocess
from pathlib import Path
import performance_benchmark as bench
from build import environment

ROOT=bench.ROOT;SOURCE=ROOT/'source-snapshots/context-proxy-v3';BINARY=ROOT/'builds/context-proxy-v3'
def main():
    assert not SOURCE.exists() and not BINARY.exists()
    SOURCE.mkdir(parents=True);BINARY.mkdir(parents=True)
    for top in ['include','src','shaders','cmake','reference','tools','tests']:
        shutil.copytree(bench.PROJECT/top,SOURCE/top,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copy2(bench.PROJECT/'CMakeLists.txt',SOURCE/'CMakeLists.txt')
    proxy=SOURCE/'tests/demo/PerformanceContext.hpp'
    text='''#pragma once
#include "dx/context/Device.h"
#include <array>
namespace NvFlex {Context::Context():mEnableTimers(false){} Context::~Context()=default;}
namespace perf {
using namespace NvFlex;
struct Sample {unsigned long long calls=0;double ms=0;};
static bool enabled=false;
static std::array<Sample,128> samples;
static std::array<const char*,128> names;
struct Scope {unsigned index;double start;bool active;
Scope(unsigned i,const char*n):index(i),start(enabled?Ms():0),active(enabled){names[i]=n;}
~Scope(){if(active){auto&s=samples[index];s.ms+=Ms()-start;++s.calls;}}};
struct ContextProxy final : Context {
Context* wrapped; explicit ContextProxy(Context*c):wrapped(c){}
'''
    base=(bench.PROJECT/'tests/TraceContext.generated.hpp').read_text()
    methods=re.findall(r'    ([^\n]+?) override \{\n(.*?)\n    \}',base,re.S)
    assert len(methods)==45,len(methods)
    for index,(signature,body) in enumerate(methods):
        call=next(line.strip() for line in body.splitlines() if 'wrapped->' in line)
        if call.startswith('auto result='):call=call.replace('auto result=','return ',1)
        label=signature.replace('"','')
        text+='    '+signature+' override { wrapped->mEnableTimers=mEnableTimers; Scope scope('+str(index)+',"'+label+'"); '+call+' }\n'
    text+='''};
static void Save(const std::string&root){std::ofstream f(root+"/context-cpu.csv");f<<"method,calls,total_ms\\n";
for(unsigned i=0;i<samples.size();++i)if(names[i])f<<std::quoted(names[i])<<","<<samples[i].calls<<","<<std::setprecision(12)<<samples[i].ms<<"\\n";}
}
'''
    proxy.write_text(text)
    head=SOURCE/'tests/demo/headless.cpp';text=head.read_text()
    # Include after Ms definition, where NvFlex and ostream declarations exist.
    anchor='double BeginApiTrace()';index=text.index(anchor);text=text[:index]+'#include "PerformanceContext.hpp"\n'+text[index:]
    text=text.replace('    double initStart=Ms();Init(g_scene);','    auto contextAddress=reinterpret_cast<NvFlex::Context**>(reinterpret_cast<char*>(g_flexLib)+0x10);\n    auto originalContext=*contextAddress;perf::ContextProxy proxy(originalContext);*contextAddress=&proxy;\n    double initStart=Ms();Init(g_scene);')
    text=text.replace('        diagnosticFrame=f;apiSamples.clear();probeRows.clear();','        perf::enabled=f>60;\n        diagnosticFrame=f;apiSamples.clear();probeRows.clear();')
    text=text.replace('    RunCopyProbe();','    perf::enabled=false;perf::Save(outputRoot);\n    RunCopyProbe();')
    text=text.replace('    Shutdown();return 0;','    *contextAddress=originalContext;Shutdown();return 0;')
    head.write_text(text)
    cmake=SOURCE/'CMakeLists.txt';text=cmake.read_text();text+='\ntarget_include_directories(DisassemblyFlexDemo PRIVATE include src "${DISASSEMBLYFLEX_WORKSPACE}/FleX")\n';cmake.write_text(text)
    bench.write(SOURCE/'source_manifest.json',{p.relative_to(SOURCE).as_posix():bench.sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()})
    temp=ROOT/'temp/context-proxy-build-v3';temp.mkdir();env=environment(temp)
    command=['cmake','-S',str(SOURCE),'-B',str(BINARY),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_MAKE_PROGRAM='+str(bench.WS/'Build/Toolchains/ninja/1.13.2/ninja.exe'),'-DDISASSEMBLYFLEX_WORKSPACE='+str(bench.WS)]
    # Also acquire the shared lock for CPU-heavy compilation, avoiding benchmark interference.
    import msvcrt,time
    with (bench.WS/'Build/OpenFlexAlpha82c-20260928/gpu.lock').open('a+b') as lock:
        while True:
            try:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
            except OSError:time.sleep(.1)
        with (ROOT/'logs/context-proxy-build-v3.log').open('wb') as log:
            for cmd in [command,['cmake','--build',str(BINARY),'--target','DisassemblyFlexDemo','--parallel','4']]:
                result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode:raise RuntimeError('See context-proxy-build.log')
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    bench.write(ROOT/'evidence/context-proxy-build.json',dict(status='PASS',exe=str(BINARY/'DisassemblyFlexDemo.exe'),sha256=bench.sha(BINARY/'DisassemblyFlexDemo.exe'),source=str(SOURCE),methods=len(methods)))
    bench.event('diagnostic-build-complete',source=str(SOURCE),binary=str(BINARY))
    print('Diagnostic Context proxy built')
if __name__=='__main__':main()
