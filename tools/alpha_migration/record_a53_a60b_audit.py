from common import *
docs=read(ROOT/'history/documents-expanded.json');vs=read(LEDGER/'versions.json');rows=[]
def add(v,key,title,status,reason,file='00_CURRENT.md'):
    e=[x['copy'] for x in docs if x['version']==v and Path(x['copy']).name==file];assert e
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=e,source_delta=str(ROOT/'history'/v/'OpenFleX-code.patch'),reviewed=now()))
add('alpha5.3','distributed','N帧分布式Update与已完成态发布','not-transplanted-timing-contract','默认关闭的KG/Core扩展改变公共更新完成时点和物理周期；DF NvFlexUpdate/Get/Map合同保持原调用粒度，不以分摊改变任务。')
add('alpha5.3b','frame-skip','N帧简单跳算+累计dt/presentation补偿','not-transplanted-semantic-change','跳帧和扩大dt改变物理及显示，不能按省掉Update数量记同工作加速。')
add('alpha5.4','vk-selection','同DLL运行时选择Vulkan与adapter LUID配对','outside-current-backends','DF本轮目标原D3D11/D3D12 DLL；没有Vulkan→D3D11 host bridge，不添加另一后端或改变computeType ABI。')
for key,title,status,reason in [
 ('persistent-map','Vulkan persistent mapping','already-present-d12-not-d11-equivalent','DF D3D12 Constant12已持久映射且按fence复用版本；D3D11动态Map/Unmap不能直接改成Vulkan内存映射规则。'),
 ('epoch','submission epoch/iteration小batch','already-batched-d12','DF D3D12已有一个recording/list汇集命令，等显式Flush/Map需要时提交；D3D11 immediate语义不同。原caller可见等待不能删除。'),
 ('readback','窄读回/按需derived contact report','already-avoids-cost','DF按请求域和CopyDesc直接copy，无OF多域CPU snapshot；contact rows还是物理输入，不能跳其生成。'),
 ('cadence','相邻substep reuse/final-only','not-transplanted-semantic-change','降低真实工作频率，与本轮结果要求不兼容。'),
 ('fast-hash','有界Vulkan fast hash','different-order-contract','依赖OF Vulkan网格与candidate append顺序，不能替换DF排序/行截断而声称等价。'),
 ('rejected','单command buffer/handle cache/回收池/4x hash','historically-rejected','历史负收益或device-lost；DF资源引用、descriptor更新和fence所有权继续保守，不复活数值handle缓存。')]:add('alpha5.5',key,title,status,reason)
for key,title,status,reason in [
 ('upload','UploadBatch/changed-range/提交epoch','already-present-or-specific','DF12在command list内合并copies且使用持久资源；公开Set写入及Get快照必须逐调用保留，不能以OF host-generation假设抑制native/device来源更新。'),
 ('moving','Vulkan MovingFrame compute','engine-bridge-only','KG跨API数据生产者，不是DF内部求解器pass。'),
 ('contact','dense contact +8x fast-hash','different-algorithm-layout','OF独立Vulkan消费者/表布局；DF保持原shader方程和neighbor顺序。'),
 ('scope','model-only性能与client FPS边界','measurement-lesson','历史无法进目标地图便未声称地图FPS；本任务同样明确FlexDemo headless完整仿真帧，不把它写成游戏FPS。')]:add('alpha5.6',key,title,status,reason)
add('alpha5.7','rest-hoist','source rest-position row hoist','already-present','DF058源rest在每粒子起始只读一次。')
add('alpha5.7','atomic-head','单次atomic head exchange建链','not-applicable','DF使用radix排序和bucket start/end，没有这个linked-list插头原子序列。')
add('alpha5.7','cell-cull','current-space cell-AABB early rejection','not-directly-equivalent','OF fast-hash包含exact-cell过滤；DF原wrapped bucket与浮点边界需独立保守证明，不能按其epsilon/原点直接套用。')
add('alpha5.7b','exact-cell','固定原点/低负载open addressing/64-thread exact kernels','different-grid-layout','修OF Vulkan scratch/64-byte ABI/descriptor/cell-range并调优；DF原SM5数组/哈希和callbacks排序映射不相同。')
add('alpha5.8','frame-readback','整帧持久staging+单fence合并回读','already-avoids-donor-cost','DF各Get只排队copy，最终Map完成等待，D12共用recording；没有OF每域vector/staging/queue-submit一套，新增OpenFleXGetFrameState ABI非必需。','FINAL_RECEIPT.md')
add('alpha5.8','rigid-upload','低精度rigid冗余上传抑制','not-admitted-approximation','不能凭近似比较跳过调用者数据变化；DF对输入字节和时序保持原规则。','FINAL_RECEIPT.md')
add('alpha5.9','float3','合并读回float3 rigid translation packing与临时vector移除','already-correct-layout','DF NvFlexGetRigids直接以12字节stride复制translations，没有OF Float4 staging拆包或每帧3*N临时vector。','P30_FIX_AND_TARGETED_TESTS.md')
add('alpha5.9b','matrix','Vulkan MovingFrame四列线性组合修复','specific-backend-correctness','把四个错误dot改成列向量组合，修OF跨API矩阵布局；DF没有该额外MovingFrame shader，不能改原NV数学核。','P30_FIX_AND_TARGETED_TESTS.md')
add('alpha6.0','interop','Vulkan/D3D11 shared texture+external fence GPU resident','outside-current-bridge','DF不存在Vulkan→CPU→D3D11桥，原生D3D互操作已有自己的API/fence测试。该设计可供未来应用桥接参考，不是本轮Core可直接移植的节省。','P01_INTEROP_DESIGN.md')
add('alpha6.0b','publication','V2/V3不再每对象重注册canonical solver资源','specific-engine-bridge-fix','原重复PublishInitial覆盖pending solver output；DF没有VulkanInterop/Body V2/V3注册循环。','P20_FIX.md')
add('alpha6.0b','first-consumer','共享fence wait延至首次消费','different-synchronization-contract','只适用于OF跨API共享纹理的Acquire；DF标准Map/Wait/外部Context的既有完成语义保留。','P20_FIX.md')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('history-reviewed',through='alpha6.0b',ideas=len(rows));state(history_review_cursor='alpha6.0b',history_next='alpha6.1');print('Recorded',len(rows),'ideas.')
