"""Reviewed integration and CPU history; mark only examined ideas, not unknown waves."""
from common import *
rows=[];docs=read(ROOT/'history/documents-expanded.json')
def add(v,key,title,disposition,reason,df):
    sources=[x['copy'] for x in docs if x['version']==v and '/phases/' in x['copy'].replace('\\','/') and x['copy'].endswith('.md')]
    assert sources
    rows.append(dict(version=v,id=v+'-'+key,title=title,disposition=disposition,reason=reason,df_evidence=df,donor_evidence=sources,source_delta=str(ROOT/'history'/v/'OpenFleX-code.patch'),reviewed=now(),performance_claim='No new DF gain credited for absent OF-specific work.'))
for key,title,status,reason,df in [
 ('swap','generation-safe host vector swap','already-avoids-cost','DF 没有 snapshot→canonical CPU vector 复制，两域的 caller staging buffers 即结果目的地。','src/api/ParticleTransferApi.cpp; src/solver/SolverStorage.cpp'),
 ('retire','per-destination transfer retirement','already-avoids-cost','DF Get 直接排队原生 GPU copy，Map 仅等待其目标 staging，无 OF 全library host FIFO resolve。显式 NvFlexWait 保留原合同。','src/runtime/D3D11Resources.cpp: map/copyToHost'),
 ('loopback','未观察 velocity Get→Set 同代 loopback','different-cost-model','OF 大收益来自避免 host materialization；DF 未 Map 的 Get/Set 已按GPU命令顺序复制，不做CPU数组下载/上传循环。GPU staging往返仍存在，但省CPU收益不能外推，跳过复制需另一完整代际合同。','src/solver/SolverStorage.cpp: ReadBytes/WriteBytes'),
 ('state-swap','D3D11.1 state swap / CS shadow','historically-rejected','历史不能影响主导的异步readback等待，DF本来也未逐backend调用全域保存；精细缓存另列受控候选。','src/runtime/D3D11Context.cpp'),
 ('marker','shared-context immediate completion marker','historically-rejected','17,703,227 completion polls导致约3.45ms/frame等待，不移植busy-poll路径。','src/runtime/D3D11Resources.cpp'),
 ('setter','fused strided setter / overwrite / solver-tail waits','historically-rejected-or-existing-direct','OF多项原型在干净基线恢复时回退；DF SetParams/SetParticles不存在OF全队列同步架构。','src/api/ParamsApi.cpp; src/api/ParticleTransferApi.cpp')]:add('alpha0.7',key,title,status,reason,df)
for key,title,status,reason,df in [
 ('C01-C02','状态/资源scope微优化','historically-rejected','alpha0.8最终C01-C05均关闭，局部耗时变化未过完整帧门；不按局部更快继承其默认。','src/runtime/D3D11Context.cpp'),
 ('C03','exact-range state preservation','historically-rejected','省约0.008ms Update，但完整帧median/p95/p99回退，且DF原NV公开Context保存范围必须保持。','src/runtime/D3D11Context.cpp: contextPush/contextPop'),
 ('C04','transfer-only bypass state preservation','already-avoids-cost','DF map/copy/transfer函数没有调用contextPush/contextPop；OF候选完整帧亦回退。','src/runtime/D3D11Resources.cpp'),
 ('C05','删除generic batch boundary clear','historically-rejected','OF local Update CPU省9.68%但frame慢1.15%，DF当前单一pass unbind还用于hazard处理，不盲删。','src/runtime/D3D11Context.cpp: dispatch/unbindResources'),
 ('lifetime','共享生命周期 readback pool 修复','not-applicable-specific-bug','修OF snapshot析构引用已删除solver的UAF。DF没有该token/pool对象；保留本任务多solver/销毁oracle防止引入类似问题。','src/runtime/D3D11Resources.cpp; tests/d3d12_pool_oracle.cpp'),
 ('queue','共享渲染队列因果观测','measurement-lesson','测试必须包括调用完成等待，不能只计submit来掩盖前序队列工作；当前FlexDemo complete_ms包含最后Map。未声称实际游戏FPS。','tools/alpha_migration/run_matrix.py')]:add('alpha0.8',key,title,status,reason,df)
for key,title,reason in [
 ('interop','版本化solver SRV/UAV注册、generation/lifetime契约','OF新增OpenFleXD3D11Interop接口与KG consumer协作，DF本次维持NV ABI与原Demo调用；不能在单DLL内自动消除应用主动Get/Map。'),
 ('gpu-render','直接SRV渲染/胶囊GPU动画/零transfer模式','改动的是KG渲染与动画生产消费流程，改变本次冻结FlexDemo测量工作会失去公平口径。DF原nativeinterop已有专门oracle，但本轮不改Demo工作量。')]:add('alpha0.9',key,title,'outside-dll-contract',reason,'src/runtime/D3D11Resources.cpp; tests/interop_oracle.cpp')
add('alpha1.0','body','KG3D_OpenFleXBody GPU集成','engine-only','OF core源码patch为空；优化主体为真实Body路径的GPU资源消费。不能把KG集成收益算成DF求解器收益。','src/api/ParticleTransferApi.cpp')
add('alpha1.1','dense-prefix','dense active-prefix symmetric-pair enablement','already-bounded-different-algorithm','OF将activeCount==capacity放宽到精确identity prefix；DF主要粒子pass已按mNumParticles，只有特定容量语义pass不能随意裁剪；spring空尾另列候选。OF symmetric-pair本身改变DF邻域顺序，不能移植。','src/solver/ParticleStep.cpp')
add('alpha1.1','body-fuse','Body 3派发→1 / standalone HLSL','engine-only','属KG Body处理与shader资产组织，冻结FlexDemo没有这一Body链；不合入DF数学核。','tests/demo/headless.cpp')
for v,key,title,reason in [
 ('alpha1.2','animation','KG3D animation integration','OF core patch为空；引擎骨骼/动画生产者不在DF核心。'),
 ('alpha1.3','fixed-skin','固定粒子骨骼蒙皮','OF core patch为空；修复Body固定顶点蒙皮语义，不应改变原NV solver pins。'),
 ('alpha1.4','skeletal','完整骨骼变形 / bind模式修复','OF core patch为空；CPU/GPU Body绑定语义修正，与DF求解器数值公式不同层。'),
 ('alpha1.8','body-equivalence','CPU/GPU Body字段/方法等价修复','OF core patch为空；73等字段/行为矩阵是KG层验收，不表示DF缺少同名内部实现。')]:add(v,key,title,'engine-only',reason,'src/api/ParticleTransferApi.cpp; src/solver/ParticleStep.cpp')
for key,title,reason in [
 ('interop2','D3D11 interop v2 / transactional commit','OF新增互操作版本、GPU资源标记及KG commit事务；不对应NV公开ABI内可删的计算成本。'),
 ('body-semantics','MoveLimit/移动坐标系/teleport/capsule/reset','引擎动画与Body产品合同；移入DF会擅自增加原NV未有的控制规则。'),
 ('force','移除Body近似积分，solver执行force/aero/damping','DF本来用原kernel执行这些力，不存在OF Body双重近似积分。'),
 ('state','完整caller CS保存恢复','OF互操作调用者状态合同；DF保留原Context语义并用native-state oracle验证，不能用OF全128SRV规则改写原16SRV观察行为。')]:add('alpha1.5',key,title,'not-applicable-or-existing',reason,'src/runtime/D3D11Context.cpp; src/solver/ParticleStep.cpp')
for key,title,reason in [
 ('render','duplicate binding与anchor smoothing方向修正','OF Body把CPU duplicate bookkeeping误当Follow、lerp权重反了；DF无这段渲染代码。'),
 ('projection','额外structural projection/analytic shape convergence','为补偿OF已降频的rigid/contact引入8pass等预算；会改变DF原约束算法与计算结果。'),
 ('ccd','防止反复重放同一pre-integration CCD','OF后加的收敛pass重复CCD问题，DF无该重复收敛链；不能删除原子步内唯一collision。')]:add('alpha1.6',key,title,'not-transplanted-specific-semantics',reason,'src/solver/ParticleStep.cpp')
for key,title,reason in [
 ('sparse-repair','compact stiff/short-edge repair CSR及融合','OF为补偿先前降频和Body接缝问题加入额外修正，长度阈值/权重为其资产门调整；DF没有对应额外修正，不改变NV数学结果来复制补丁。'),
 ('shape-local','一次broadphase + registers内局部shape convergence','OF额外convergence替代路线，DF contact顺序/CCD合同比较不同；无损不成立。'),
 ('capsule-static','静态capsule geometry缓存','值得保留的精确dirty思路；DF shape几何与变换分域当前API每SetShapes显式写入，缓存需覆盖GPU来源和外部写入，后续按真正setter热点审计。'),
 ('body-split','MoveLimit/anchor/capsule专用kernel','KG Body单核拆分优化，不在冻结FlexDemo/DF库内。'),
 ('noop-lesson','删除identity/zero Body派发也暴露浮点轨迹失败','历史candidate63的noop消除出现frame105残差；本任务A001已经出现类似调度波动，因此不能把公式没变直接等同逐bit/表现不变。')]:add('alpha1.7',key,title,'candidate-family' if key=='capsule-static' else 'not-transplanted-or-validation-lesson',reason,'src/api/ShapeApi.cpp; src/solver/ParticleStep.cpp')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
vs=read(LEDGER/'versions.json')
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='ideas-reviewed-candidates-pending' if v['version'] in ['alpha1.1','alpha1.7'] else 'reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('integration-history-reviewed',ideas=len(rows));print('Recorded',len(rows),'ideas.')
