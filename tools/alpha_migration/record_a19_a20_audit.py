"""Packaging corrections and alpha2.0 optimization waves, with explicit DF scope."""
from common import *
rows=[]
def add(v,key,title,disposition,reason,df,donor):
    assert (WS/donor).exists()
    rows.append(dict(version=v,id=v+'-'+key,title=title,disposition=disposition,reason=reason,df_evidence=df,donor_evidence=donor,reviewed=now(),performance_claim='Only new paired DF measurements can establish a migrated gain.'))
d='Build/DisassemblyFleX-AlphaMigration-20261010/history/alpha1.9/rename-normalized-review.patch'
for key,title,status,reason,df in [
 ('rename','NvFlex→OpenFleX API/ABI names / Android wrapper','not-transplanted-abi','alpha1.9大量源码变化为重命名与Android符号包装；DF目标仍原NvFlex Windows DLL接口，不能重命名其导出。派生normalized patch仅用于排除机械改名，不覆盖原证据。','tools/generate_exports.py'),
 ('uav-slot','FL11_0 fluid SurfaceNormals u8→u5','not-applicable-specific-fix','OF使用了第9个CS UAV导致CreateComputeShader失败，改为各entry互斥复用u5；DF原84 shader与Context本来只用8个UAV，未有该槽位bug。','src/runtime/D3D11Context.cpp; shaders/machine'),
 ('errors','shader Create HRESULT诊断','diagnostic-only','OF增强失败日志，非性能优化。DF已有Check抛出失败；不把日志增强算作速度收益。','src/runtime/D3D11Context.cpp'),
 ('repair','FrozenStructuralCorrection及短边修复变体','not-transplanted-semantic-change','新增/调整OF特殊短边补偿器；部分if(false)实验分支不执行。DF无这一附加数学规则，不以该修复改写原NV约束。','src/solver/ParticleStep.cpp'),
 ('packaging','K盘独立包/构建路径约束','build-organization-only','发布/containment和文件组织调整，不改变有效GPU算法；本任务已将所有产物隔离Build并冻结源码。','tools/alpha_migration/build_candidate.py')]:add('alpha1.9',key,title,status,reason,df,d)
d='History/OpenFlexAlpha20QModelEditorOptimizationLedger-2026-08-14/OpenFlexExecutionLedger/phases/P03_D3D11_AND_CONSTRAINT_WAVES.md'
for key,title,status,reason,df in [
 ('tri-init','count-delimited triangle contact init','already-present-different-contract','DF只clear static contact counts再生成有效payload，没有OF整块payload初始化pass；公开GetContacts仍按容量读取原buffer内容，不能偷偷多清/少清。','src/solver/ParticleStep.cpp; src/api/ContactOutputApi.cpp'),
 ('dense-contact','8-lane dense solid direct Jacobi contact','not-transplanted-semantic-risk','OF消除独立CAS scatter且改八lane归约；DF SolveDensities/SolveContacts数据流不同，浮点累加次序与接触边界不能直接沿用。','src/solver/ParticleStep.cpp; shaders/recovered'),
 ('boundary','消除重复adapter boundary clear','already-avoids-cost','DF不存在adapter再清一次的双重层；当前dispatch后的唯一SRV/UAV unbind仍有hazard意义。','src/runtime/D3D11Context.cpp'),
 ('csr-normals','CSR gather替代atomic face-normal scatter','not-admitted-without-large-total-gain','改变法线累加顺序；历史UpdateNormals快57.4%但完整solver/editor在噪声内，且已有可见shading差异。DF原normal还可反馈aero，不能凭pass收益使用微差例外。','src/solver/ParticleStep.cpp: UpdateTriangles/UpdateVertexNormals'),
 ('prefix','dense active-prefix spring/rigid extent','candidate-family','OF历史无可测收益；DF原spring按maxParticles派发，针对真正空尾需单独证明最大引用ID并实测，已记A003 family，不能简单activeCount截断。','src/api/SpringApi.cpp; src/solver/ParticleStep.cpp'),
 ('rigid-batch','rigid-aware两轮spring batch','historically-rejected','仅约0.004ms spring gain无完整收益；DF跨轮回调/共享约束不同，不盲移植。','src/solver/ParticleStep.cpp'),
 ('rigid32','rigid 32线程组','already-present-vendor-selection','OF0.134→0.191ms失败；DF已有NV平均成员数自动选32/NV/128NV路径。','src/solver/ParticleStep.cpp'),
 ('packed16','packed16 solid rows','different-layout-contract','OF作为dense-contact依赖有条件保留，单独仅0.006ms。DF consumer/公有GetNeighbors为32-bit，不能孤立压缩。','src/api/ContactOutputApi.cpp'),
 ('rows16','16 rows/512线程neighbor gather','historically-rejected','OF BuildNeighbors0.310→0.317ms回退；DF当前非该cooperative格式。','shaders/machine/058_g_Flex_CollideParticles.smasm'),
 ('bucket8','counting-grid规模4→8','historically-rejected-not-applicable','BucketScan增长、neighbors不变；DF radix grid无该bucket scale。','src/solver/RadixSort.cpp'),
 ('sphere-cull','packed-path sphere/AABB cull','historically-rejected','OF实际选中路径下无收益，不覆盖此前alpha0.4另一gather路径；DF仍须按自身访问规则评估，不能外推原接受数字。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('candidate-parallel','packed-path candidate lane并行','historically-rejected','额外lane控制/归约未摊薄；DF原邻居顺序不同。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('rigid-o3','rigid shader O3','no-measured-historical-gain','OF近噪声保留，不算收益；DF保留原指令schedule，重新FXC优化可能改变指令/舍入且无需为已编译原程序加O3。','tools/build_shaders.py'),
 ('all-o3','全部runtime shader统一O3','historically-rejected','历史solver1.325→1.374ms回退；DF原84 instruction containers更不能当成无损编译flag实验。','tools/build_shaders.py'),
 ('unbind','删除34对shader/CB unbind','historically-rejected-already-different','OF完整帧噪声/submit回退；DF本来每dispatch只unbind SRV/UAV，不额外清shader/CB。','src/runtime/D3D11Context.cpp: unbindResources'),
 ('context-swap','Body D3D11.1 ContextState swap','historically-rejected-outside-core','OF不比手动scope快；DF原nativeContext合同不同。','src/runtime/D3D11Context.cpp'),
 ('body-scope','animation/frame两个Body scope合并','historically-rejected-outside-core','引擎级scope合并无完整帧收益，不在DF solver。','tests/demo/headless.cpp'),
 ('body-threads','Body render128→256threads','historically-rejected-outside-core','高寄存器Deform慢3.1%，不是DF数学核可移植改动。','tests/demo/headless.cpp')]:add('alpha2.0',key,title,status,reason,df,d)
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
vs=read(LEDGER/'versions.json')
for v in vs:
    if v['version'] in ['alpha1.9','alpha2.0']:v.update(status='ideas-reviewed-candidates-pending' if v['version']=='alpha2.0' else 'reviewed-no-direct-port',review_ids=[r['id'] for r in rows if r['version']==v['version']])
write(LEDGER/'versions.json',vs);event('history-reviewed',versions=['alpha1.9','alpha2.0'],ideas=len(rows));print('Recorded',len(rows),'ideas.')
