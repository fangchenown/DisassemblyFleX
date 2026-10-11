"""Scope D3D11 binding reuse to callback-free solver submission; preserve hazard clears."""
import argparse,difflib
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',default='a06-bindings-v1');a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
if not dest.exists():shutil.copytree(base,dest)
changes={}
def put(path,s):changes[path]=((base/path).read_text(encoding='utf8'),s);(dest/path).write_text(s,encoding='utf8')
path='src/runtime/D3D11Context.hpp';s=(base/path).read_text(encoding='utf8');needle='    void contextPop() override;';assert s.count(needle)==1
s=s.replace(needle,needle+'''
    // Internal, nested-safe submission scope. Public Context calls outside it
    // keep the original full binding policy. No COM object is cached/owned.
    void beginSolverBatch();
    void endSolverBatch();''')
needle='    void unbindResources();';assert s.count(needle)==1
s=s.replace(needle,needle+'''
    unsigned solverBatchDepth=0,lastReadSpan=32;
    bool resourcesKnownClear=false,samplerKnown=false,constantKnown[2]{};
    ID3D11Buffer* boundConstants[2]{};
    void invalidateBindings();
    void invalidateConstant(ID3D11Buffer*);''');put(path,s)
path='src/runtime/D3D11Context.cpp';s=(base/path).read_text(encoding='utf8');marker='void ContextD3D11::bind(';start=s.index(marker);end=s.index('void ContextD3D11::dispatch(',start)
replacement='''void ContextD3D11::invalidateBindings(){resourcesKnownClear=false;samplerKnown=false;lastReadSpan=32;for(unsigned i=0;i<2;++i){constantKnown[i]=false;boundConstants[i]=nullptr;}}
void ContextD3D11::invalidateConstant(ID3D11Buffer* buffer){if(solverBatchDepth)for(unsigned i=0;i<2;++i)if(boundConstants[i]==buffer)constantKnown[i]=false;}
void ContextD3D11::beginSolverBatch(){++solverBatchDepth;invalidateBindings();}
void ContextD3D11::endSolverBatch(){if(solverBatchDepth)--solverBatchDepth;invalidateBindings();}
void ContextD3D11::bind(const NvFlex::DispatchParams* params){
    auto shader=static_cast<Shader*>(params->shader);immediate->CSSetShader(shader->shader.Get(),nullptr,0);
    ID3D11ShaderResourceView* reads[32]{};ID3D11UnorderedAccessView* writes[8]{};
    unsigned readSpan=solverBatchDepth&&resourcesKnownClear?0u:32u;
    for(unsigned i=0;i<32;++i)if(params->readOnly[i]){reads[i]=static_cast<ReadView*>(params->readOnly[i])->view.Get();readSpan=std::max(readSpan,i+1);}
    for(unsigned i=0;i<8;++i)if(params->readWrite[i])writes[i]=static_cast<WriteView*>(params->readWrite[i])->view.Get();
    if(readSpan)immediate->CSSetShaderResources(0,readSpan,reads);
    // Keep all eight UAV binds/unbinds, including the reserved NV extension
    // slot and every read/write hazard boundary from the original runtime.
    immediate->CSSetUnorderedAccessViews(0,8,writes,nullptr);lastReadSpan=readSpan;
    auto constant=[&](unsigned slot,NvFlex::ConstantBuffer* input){
        if(!input)return;auto cb=static_cast<ConstantBuffer*>(input)->buffer.Get();
        if(!solverBatchDepth||!constantKnown[slot]||boundConstants[slot]!=cb)immediate->CSSetConstantBuffers(slot,1,&cb);
        if(solverBatchDepth){boundConstants[slot]=cb;constantKnown[slot]=true;}
    };
    constant(0,params->rootConstantBuffer);constant(1,params->secondConstantBuffer);
    auto sampler=linearSampler.Get();if(!solverBatchDepth||!samplerKnown)immediate->CSSetSamplers(0,1,&sampler);samplerKnown=solverBatchDepth!=0;
#if defined(DF_VALIDATE_BINDINGS)
    if(solverBatchDepth){
        bool mismatch=false;ID3D11ShaderResourceView* actualReads[32]{};immediate->CSGetShaderResources(0,32,actualReads);
        for(unsigned i=0;i<32;++i){
            if(actualReads[i]!=reads[i]){
                bool alias=false;if(reads[i]){ComPtr<ID3D11Resource> resource;reads[i]->GetResource(&resource);for(auto write:writes)if(write){ComPtr<ID3D11Resource> output;write->GetResource(&output);alias=alias||resource.Get()==output.Get();}}
                if(!(actualReads[i]==nullptr&&alias))mismatch=true;
            }
            if(actualReads[i])actualReads[i]->Release();
        }
        ID3D11UnorderedAccessView* actualWrites[8]{};immediate->CSGetUnorderedAccessViews(0,8,actualWrites);
        for(unsigned i=0;i<8;++i){mismatch=mismatch||actualWrites[i]!=writes[i];if(actualWrites[i])actualWrites[i]->Release();}
        for(unsigned i=0;i<2;++i)if(constantKnown[i]){ComPtr<ID3D11Buffer> actual;immediate->CSGetConstantBuffers(i,1,&actual);mismatch=mismatch||actual.Get()!=boundConstants[i];}
        ComPtr<ID3D11SamplerState> actualSampler;immediate->CSGetSamplers(0,1,&actualSampler);mismatch=mismatch||actualSampler.Get()!=sampler;
        if(mismatch)throw std::runtime_error("D3D11 solver binding state differs from submitted resources");
    }
#endif
}
void ContextD3D11::unbindResources(){
    ID3D11ShaderResourceView* reads[32]{};ID3D11UnorderedAccessView* writes[8]{};
    unsigned readSpan=solverBatchDepth?lastReadSpan:32u;
    if(readSpan)immediate->CSSetShaderResources(0,readSpan,reads);
    immediate->CSSetUnorderedAccessViews(0,8,writes,nullptr);resourcesKnownClear=solverBatchDepth!=0;
#if defined(DF_VALIDATE_BINDINGS)
    if(solverBatchDepth){
        bool mismatch=false;immediate->CSGetShaderResources(0,32,reads);immediate->CSGetUnorderedAccessViews(0,8,writes);
        for(auto p:reads)if(p){mismatch=true;p->Release();}for(auto p:writes)if(p){mismatch=true;p->Release();}
        if(mismatch)throw std::runtime_error("D3D11 solver hazard boundary retains a resource binding");
    }
#endif
}
'''
s=s[:start]+replacement+s[end:]
s=s.replace('void ContextD3D11::updateContext(const NvFlexContextDesc* opaque){','void ContextD3D11::updateContext(const NvFlexContextDesc* opaque){\n    invalidateBindings();')
s=s.replace('void ContextD3D11::clearState(){immediate->ClearState();}','void ContextD3D11::clearState(){immediate->ClearState();invalidateBindings();resourcesKnownClear=solverBatchDepth!=0;}')
s=s.replace('void ContextD3D11::contextPush(){','void ContextD3D11::contextPush(){\n    invalidateBindings();')
s=s.replace('void ContextD3D11::contextPop(){if(saved.empty())','void ContextD3D11::contextPop(){invalidateBindings();if(saved.empty())');put(path,s)
path='src/runtime/D3D11Resources.cpp';s=(base/path).read_text(encoding='utf8')
for needle,replacement in [('void* ContextD3D11::map(NvFlex::ConstantBuffer* buffer){','void* ContextD3D11::map(NvFlex::ConstantBuffer* buffer){invalidateConstant(static_cast<ConstantBuffer*>(buffer)->buffer.Get());'),('void ContextD3D11::unmap(NvFlex::ConstantBuffer* buffer){','void ContextD3D11::unmap(NvFlex::ConstantBuffer* buffer){invalidateConstant(static_cast<ConstantBuffer*>(buffer)->buffer.Get());'),('void ContextD3D11::copy(NvFlex::ConstantBuffer* dst,NvFlex::Buffer* src){','void ContextD3D11::copy(NvFlex::ConstantBuffer* dst,NvFlex::Buffer* src){invalidateConstant(static_cast<ConstantBuffer*>(dst)->buffer.Get());')]:
    assert s.count(needle)==1;s=s.replace(needle,replacement)
put(path,s)
path='src/api/UpdateApi.cpp';s=(base/path).read_text(encoding='utf8');needle='    if(s.mNumParticles){float subdt=dt/float(substeps);';assert s.count(needle)==1
replacement='''    if(s.mNumParticles){
        bool callbacks=false;for(int i=0;i<int(eNvFlexStageCount);++i){NvFlexSolverCallback value{};std::memcpy(&value,s.mCallbacks+sizeof(value)*i,sizeof(value));callbacks=callbacks||value.function!=nullptr;}
        struct BindingScope {
            df::ContextD3D11* context;
            explicit BindingScope(df::ContextD3D11* c):context(c){if(context)context->beginSolverBatch();}
            ~BindingScope(){if(context)context->endSolverBatch();}
        } scope(callbacks?nullptr:dynamic_cast<df::ContextD3D11*>(library->mContext));
        float subdt=dt/float(substeps);'''
s=s.replace(needle,replacement);put(path,s)
path='CMakeLists.txt';s=(base/path).read_text(encoding='utf8');needle='set_target_properties(NvFlexReconstructed PROPERTIES OUTPUT_NAME NvFlexReleaseD3D_x64)';assert s.count(needle)==1
s=s.replace(needle,needle+'''
option(DISASSEMBLYFLEX_VALIDATE_BINDINGS "Diagnostic native-state checks; never use for performance measurements" OFF)
if(DISASSEMBLYFLEX_VALIDATE_BINDINGS)
  target_compile_definitions(NvFlexReconstructed PRIVATE DF_VALIDATE_BINDINGS=1)
endif()''');put(path,s)
diff=[]
for path,(old,new) in changes.items():diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=a.base+'/'+path,tofile=a.name+'/'+path))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8')
item=dict(id='A006-04',version='alpha0.6',candidate=a.name,base=a.base,title='Callback-free D3D11 submission scope with proven-clear SRV ranges and invalidated CB/sampler bindings',status='candidate-prepared',source=str(dest),evidence=str(patch),donor='alpha0.6 hazard-safe state batch; alpha0.8/2.0 boundary experiments inform conservative scope',numerical_change=False,shader_change=False,invariants=['first bind/unbind full32SRV; only known-null suffix omitted afterwards','all8UAV binds and unbinds preserved','root/second CB cache invalidated on map, unmap, copy, ClearState, context update and push/pop','sampler invalidated on all state resets','zero-particle and any solver-callback path preserve full original policy','public Context outside scope retains original policy','no descriptor/resource/callback/iteration removed'],required_validation=['native state validator build plus ordinary production build','large cloth and SDF highest slots','mutable CB payloads','borrowed/external context, callbacks, zero active, multiple solvers','all outputs and whole-frame FlexDemo'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[x for x in rows if x['id']!=item['id']]+[item]);event('candidate-prepared',**item)
