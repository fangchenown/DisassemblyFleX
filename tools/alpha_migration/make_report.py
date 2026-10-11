"""Publish reviewed Chinese results; refuses incomplete experiments or blank review."""
import csv,html,urllib.parse
from common import *
review=read(ROOT/'evidence/final-review.json')
version=review['run_version'];assert version=='v2'
assert review['status']=='PASS' and review['unresolved_issues']==[], 'Finish explicit numerical/performance review first'
assert read(ROOT/'jobs/final-validation-v2-pipeline.json')['status']=='PASS'
assert read(ROOT/'jobs/regression-confirmation-pipeline.json')['status']=='PASS'
assert read(ROOT/'jobs/quality-confirmation-pipeline.json')['status']=='PASS'
assert read(ROOT/'jobs/affinity-confirmation-pipeline.json')['status']=='PASS'
versions=read(LEDGER/'versions.json');ideas=read(LEDGER/'history_decisions.json');opts=read(LEDGER/'optimizations.json')
assert len(versions)==115 and all(v['status']=='review-complete' for v in versions)
assert all(o['status'].startswith(('accepted','rejected')) for o in opts)
assert set(review['candidate_notes'])=={o['id'] for o in opts}, 'Provide Chinese final rationale for every experiment'
candidate=review['candidate'];build=read(ROOT/'evidence'/f'{candidate}-build.json');delivery=ROOT/'delivery';delivery.mkdir(exist_ok=True)
report_data=PROJECT/'reports/alpha-migration-20261011';report_data.mkdir(parents=True,exist_ok=True)
def result(suite,left,right):
    stem=f'{suite}__{left}-vs-{right}'
    return read(ROOT/'analysis'/(stem+'-summary.json')),read(ROOT/'analysis'/(stem+'-scenes.json'))
primary={};emission={};quality={};emission_semantics={}
for api,left,suffix in [('d11','df',''),('d12','df12','-d3d12')]:
    right=candidate+suffix;primary[api]=result('final-primary-'+api+'-'+version,left,right);emission[api]=result('final-emission-'+api+'-'+version,left,right)
    emission_semantics[api]=read(ROOT/'analysis'/f'final-emission-{api}-{version}__{left}-vs-{right}-emission-semantics.json')
    for kind in ['quality','emission-quality','long']:
        stem=f'final-{kind}-{api}-{version}__{left}-vs-{right}';quality[api+'-'+kind]=read(ROOT/'analysis'/(stem+'-quality-summary.json'))
    for label in ['final-primary-'+api+'-'+version,'final-emission-'+api+'-'+version,'final-affinity-'+api+'-'+version]:
        for file in (ROOT/'analysis').glob(label+'*'):
            if file.is_file():shutil.copy2(file,report_data/file.name)
    shutil.copy2(ROOT/'analysis'/f'final-cpu-{api}-{version}__{left}-vs-{right}-cpu-attribution.json',report_data/f'cpu-{api}.json')
receipts=[read(p) for p in (ROOT/'runs').glob('*/receipt.json')];passed=[r for r in receipts if r['status']=='PASS'];failed=[r for r in receipts if r['status']=='FAIL']
stats=dict(successful_demo_processes=len(passed),retained_failed_demo_processes=len(failed),successful_simulated_frames=sum(r['frames'] for r in passed),clock_flagged_original_processes=sum(bool(r.get('timing_contaminated_by_suspend')) for r in passed))
write(report_data/'run-statistics.json',stats);write(report_data/'final-review.json',review);write(report_data/'optimizations.json',opts);write(report_data/'versions.json',versions);write(report_data/'history-decisions.json',ideas)
for f in (ROOT/('report-figures-'+version)).glob('*'):
    if f.is_file():shutil.copy2(f,report_data/f.name)
for f in (ROOT/'analysis').glob('regression-confirm-*-scenes.csv'):shutil.copy2(f,report_data/f.name)
with (report_data/'history-decisions.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['version','id','title','disposition','reason','closure_reason','closure_scope','candidate_ids','outcomes'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for row in ideas:w.writerow({k:json.dumps(row.get(k,''),ensure_ascii=False) if isinstance(row.get(k), (list,dict)) else row.get(k,'') for k in fields})
cn={
'A001-01':'受限的空三角形派发省略，保留原计时标签及结构约束路径',
'A002-01':'D3D12 40个描述符复制合为一次等价批量复制',
'A002-02':'D3D12按原顺序批量提交资源与UAV屏障',
'A003-01':'GPU计算最大实际弹簧端点，裁剪被证明没有输出的尾部线程',
'A003-02':'纯平面碰撞派生shader',
'A006-01':'shader名称异构查找与固定名称，消除临时字符串',
'A006-02':'D3D12保活对象集合改用哈希查找，保持释放与fence顺序',
'A006-03':'IPO/LTCG全程序优化',
'A006-04':'无回调求解域内复用D3D11绑定，保留全部UAV屏障边界',
'A021-01':'合并相邻的重复子步常量上传',
'A024-01':'弹簧线程组512改256、保留八路归约',
'A037-01':'受限的当前距离优先邻居过滤，保留邻居顺序及截断',
'A037-02':'满邻居行提前返回',
'A039-01':'删除原shader完全不读取的HalfSpringIndices分配及绑定',
'A042-01':'精确12字节弹簧元数据打包',
'A082-01':'前16位采用两次稳定8位排序，剩余位保留原4位排序'}
def e(s):return html.escape(str(s))
def num(v):return '不可用' if v is None else f'{v:.6f}'
def ci(v):return '['+', '.join(num(x) for x in v)+']'
def table(headers,rows,klass=''):
    return '<table class="'+klass+'"><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'
def paragraphs(xs):return ''.join('<p>'+e(x)+'</p>' for x in xs)
plain=[]
def make(out):
    def link(path,title):
        rel=os.path.relpath(path,out.parent).replace('\\','/');return '<a href="'+urllib.parse.quote(rel,safe='/.-_')+'">'+e(title)+'</a>'
    text=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DisassemblyFleX alpha历史优化迁移报告</title><style>body{font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif;max-width:1500px;margin:32px auto;padding:0 24px;color:#182335}h1,h2{color:#123e65}table{border-collapse:collapse;width:100%;margin:18px 0;font-size:13px}td,th{border:1px solid #c9d5df;padding:8px;vertical-align:top;text-align:left}th{background:#eaf1f7;position:sticky;top:0}tr:nth-child(even){background:#f7fafc}a{color:#075db1}code{overflow-wrap:anywhere}input{padding:10px;width:min(650px,90%);font:inherit}.note{border-left:4px solid #5683aa;padding:12px;background:#f1f6fb}.scroll{overflow:auto}summary{cursor:pointer;font-weight:bold}pre{white-space:pre-wrap;overflow-wrap:anywhere}nav a{margin-right:15px}</style><h1>DisassemblyFleX：OpenFleX alpha历史优化迁移报告</h1>']
    text.append('<nav><a href="#outcome">结果</a><a href="#implementation">实现</a><a href="#performance">逐场景数据</a><a href="#quality">正确性</a><a href="#history">115版本审计</a><a href="#delivery">交付与复现</a></nav>')
    text.append('<p>生成时间：'+e(now())+'。本报告只在显式终验审阅通过后生成。</p><h2 id="outcome">结果与测量边界</h2>')
    for api in ['d11','d12']:
        r=primary[api][0];sentence=f'{api.upper()}：67场景等权几何平均速度比为 {r["equal_scene_geomean"]:.6f}，95%区间 {ci(r["equal_scene_geomean_ci95"])}。速度比定义为原DF耗时/优化DF耗时，大于1表示优化版更快。'
        text.append('<p>'+e(sentence)+'</p>')
        if out==PROJECT/'ALPHA_MIGRATION_REPORT_CN.html':plain.append(sentence)
    text.append(paragraphs(review['outcome_notes']))
    text.append('<div class="note">主指标是无窗口FlexDemo的完整物理帧：Scene更新、Set/Update/Get及最终Map完成；Draw/Present不在其中，不能换算成游戏屏幕FPS。生产计时关闭昂贵捕获与GPU/CPU探针；质量与阶段归因另跑。统计单位是独立进程配对，不把每帧当独立重复。每场景区间与Holm多重比较结论同时保留。</div>')
    text.append('<p>环境：Windows 10 Education 19045，Core i5-13600K，RTX 5080 16GB，驱动581.15，64GB内存；MSVC14.44.35207、SDK10.0.26100。电源策略保持原状。所有GPU任务串行，使用无窗口进程及SystemRequired，不依赖桌面、键鼠或屏幕保持点亮。'+link(ROOT/'evidence/hardware.json','原始环境记录')+'</p>')
    text.append('<h2 id="implementation">实现与逐项取舍</h2><p>最终v2保留原84个shader容器，未启用任何修改后的浮点shader。新增5个程序均为整数辅助程序，单独登记；不把它们称为NVIDIA原厂高级源码。保持原浮点公式、约束次数、子步、迭代、公开数据和回调语义，未使用数值近似例外。邻居谓词重排在v1试验后被保守撤回，原数据与源码保留。</p>')
    rows=[]
    for o in opts:
        rows.append([e(o['id']+' / '+o['version']),e(cn.get(o['id'],o['title'])),'纳入正式版' if o['status'].startswith('accepted') else '不纳入',e(review['candidate_notes'][o['id']]),e(o.get('candidate',''))])
    text.append(table(['编号/历史版本','改动','最终决定','依据/边界','独立实验构建'],rows))
    text.append(paragraphs(review['implementation_notes']))
    text.append('<p>死流移除节省的是每个solver 4×已保留half-spring容量字节的逻辑存储；没有把它冒称为已测量的驱动峰值显存下降。稳定8位前缀只覆盖2048～1048576个键、1024对齐、24/32有效位，其他情况和分配失败保持原排序。新增scratch约为8×键容量+8×1024块数的逻辑字节数，采用高水位复用；这项内存代价需与局部收益一起评价。</p>')
    text.append('<h3>核心C++方法和入口</h3>')
    methods=[('src/api/UpdateApi.cpp','NvFlexUpdateSolver','回调存在时保留原绑定策略；无回调内部scope维护可失效的绑定缓存'),('src/solver/ParticleStep.cpp','UpdateParticleSubstep / Pass','空派发门控、最大端点间接派发；恢复原邻居程序，无scene-ID判断'),('src/api/SpringApi.cpp','NvFlexSetSprings','GPU最大端点准备及未读资源删除；不按activeCount猜测最大ID'),('src/api/CopySolverApi.cpp','NvFlexCopySolver','使私有派发范围失效，保留原调试接口语义'),('src/runtime/D3D11Context.cpp','bind / unbindResources / beginSolverBatch / endSolverBatch','首轮建立全空SRV证明；全部8个UAV绑定/解绑仍保留'),('src/runtime/D3D11Resources.cpp','map / unmap / copy(ConstantBuffer)','常量rename/修改时显式使缓存失效'),('src/runtime/D3D12Context.cpp','bind / prepareTransition / transition','相同描述符和按原顺序的资源屏障合批'),('src/runtime/D3D12Resources.hpp','Context12State retainedSet','保留vector的对象生命周期与释放顺序，只更换查重数据结构'),('src/runtime/Runtime.hpp','NvFlexLibrary shader map','异构名称查找，避免临时字符串'),('src/solver/RadixSort.cpp','sort / reserveWide / destructor','稳定整数前缀排序和scratch生命周期；原后续pass恢复物理front/back内容')]
    text.append(table(['源文件','函数/方法','改变及原因'],[[link(PROJECT/f,f),e(fn),e(reason)] for f,fn,reason in methods]))
    text.append('<p>上表是实际改动映射，不声称测到了每个微小C++方法的独立耗时。CPU归因使用同一harness的QueryThreadCycleTime/GetThreadTimes/GetProcessTimes阶段探针；其扰动结果与生产完整帧排名分开，周期数不换算为秒。</p>')
    auxiliary=read(ROOT/'builds'/candidate/'generated/aux_shader_manifest.json')
    text.append('<h3>新增/派生shader入口</h3>')
    text.append(table(['入口','源码','来源类型','关联原入口编号','DXBC SHA256'],[[e(s['name']),link(PROJECT/'shaders/auxiliary'/s['source'],s['source']),'原指令派生' if s.get('instructions') else '新写整数辅助程序',e(s.get('original_index','独立辅助入口')),'<code>'+e(s['dxbc_sha256'])+'</code>'] for s in auxiliary]))
    text.append('<p>为保持公开DetailTimers名称兼容，排序辅助程序沿用对应原标签，因此这里不伪造每个辅助入口的独立GPU时间。SortCellIndices等阶段数据用于归因；派发次数变化也会改变profile模式中的查询数量，阶段百分比不能替代生产完整帧收益。</p>')
    text.append('<h2 id="performance">双后端逐场景性能</h2>')
    text.append('<p>表中毫秒值是各进程平均帧耗时的中位数；速度比及区间基于配对进程的对数比，不能简单用两列中位数相除替代。小数位用于复核计算，不代表同等纳秒级硬件精度。67场景保持各自Initialize的发射默认值：例如Viscosity默认增长，Adhesion/Goo Gun默认为空。额外DEMO_EMIT实际发送空格键切换，而非强制开启，下面按真实粒子数量变化分类。</p>')
    for api in ['d11','d12']:
        text.append('<h3>'+api.upper()+'，默认67场景</h3>');rs=primary[api][1]
        figure=report_data/(api+'-primary.png')
        if figure.exists():
            uri=urllib.parse.quote(os.path.relpath(figure,out.parent).replace('\\','/'),safe='/.-_')
            text.append('<details><summary>展开逐场景置信区间图</summary><img style="max-width:100%;height:auto" src="'+uri+'" alt="'+api+'逐场景速度比与置信区间"></details>')
        text.append('<div class="scroll">'+table(['ID/场景','进程对数','原DF ms','优化DF ms','配对速度比','95%区间','Holm结论'],[[e(str(r['scene'])+' '+r['name']),r['n'],num(r['left_ms_median']),num(r['right_ms_median']),num(r['paired_speedup_geomean']),e(ci(r['paired_speedup_ci95'])),e(r['holm_decision'])] for r in rs])+'</div>')
        text.append('<h3>'+api.upper()+'，空格切换与实际发射增长</h3>');r=emission[api][0];classification=emission_semantics[api];g=classification['growth_only'];types={x['scene']:x for x in classification['scenes']}
        text.append('<p>最终v2只选实际增长的场景 '+e(g['scenes'])+'：等权速度比 '+num(g['equal_scene_geomean'])+'，95%区间 '+e(ci(g['equal_scene_geomean_ci95']))+'。v1曾额外包含切换后关闭的Viscosity控制，已单独标注并保留；最终v2不把它计为发射负载。选择依据实际粒子变化，不依据性能好坏。</p>')
        text.append(table(['ID/场景','实际粒子变化（首对）','原DF ms','优化DF ms','速度比','95%区间'],[[e(str(x['scene'])+' '+x['name']),e(types[x['scene']]['particle_ranges'][0]),num(x['left_ms_median']),num(x['right_ms_median']),num(x['paired_speedup_geomean']),e(ci(x['paired_speedup_ci95']))] for x in emission[api][1]]))
    text.append(paragraphs(review['performance_notes']))
    text.append('<h3>统一性能核心组的补充对照</h3><p>v1局部复测记录了不同分支在P/E核心间迁移比例的差异。最终v2在同一0xFFF性能核心组内另做8对2400帧对照，下表仅说明受控核心组下的结果，不替换默认调度的67场景数据。DLL不改变调用进程的亲和性或电源策略。</p>')
    for api,left,suffix in [('d11','df',''),('d12','df12','-d3d12')]:
        _,rows=result('final-affinity-'+api+'-'+version,left,candidate+suffix)
        text.append(table([api.upper()+'场景','进程对数','原DF ms','最终版 ms','速度比','95%区间','Holm结论'],[[e(str(r['scene'])+' '+r['name']),r['n'],num(r['left_ms_median']),num(r['right_ms_median']),num(r['paired_speedup_geomean']),e(ci(r['paired_speedup_ci95'])),e(r['holm_decision'])] for r in rows]))
    text.append('<p>'+link(report_data,'全部CSV与JSON统计')+'；'+link(ROOT/'analysis','局部候选、GPU阶段和CPU周期完整归因')+'。保留无收益、退化、时钟标记和整组补测，不按最好单次挑选。</p>')
    text.append('<h2 id="quality">正确性、表现与原有非确定性</h2>')
    text.append('<p>最终构建通过14项原有回归，另外通过16组弹簧全容量位置/速度及32次GPU边界检查、162组双后端整数排序及物理双缓冲/尾部差分。原84容器逐字节与指令往返核验通过。被撤回邻居候选的450组专项作为实验记录保留，不冒称该程序仍在最终DLL启用。原Ext二进制固定，没有混入OF Ext或游戏引擎改动。</p>')
    text.append(table(['质量套件','进程对数','快照对数','输入契约一致','非有限粒子数'],[[e(k),v['pairs'],v['snapshot_pairs'],e(v['all_contracts_equal']),v['nonfinite_state_particles']] for k,v in quality.items()]))
    text.append(paragraphs(review['quality_notes']))
    text.append('<p>布料中的原子累加存在原有重复波动。独立负对照只使用冻结原DF及同源码control-v0，各场景8次重复、全部同版本重复对，不用候选噪声设定容许范围。旧三重复观测及全部flags保留。输入params、ID/phase、质量、约束契约、确定性域和公开输出分别检查；轨迹RMS、空间分布和结构指标不能单独证明任意输入下等价。</p>')
    text.append('<p>NVIDIA原版在新增D3D12私有radix专项的自身对照中也以0xc0000409退出，发生在候选运行之前。该私有接口夹具不作为NVIDIA D3D12通过证据。最终保留原14项回归入口，新增162组排序专项明确使用冻结DF和CPU稳定排序对照；失败日志完整保留。现有DF对NV兼容范围及既有精度边界仍见'+link(PROJECT/'README_CN.txt','原工程说明')+'。</p>')
    text.append('<p>本任务成功FlexDemo进程 '+str(stats['successful_demo_processes'])+' 次、成功模拟帧 '+str(stats['successful_simulated_frames'])+'；其中包含筛选、重复、质量、基线及补测，不能解释成独立场景数量。保留失败运行 '+str(stats['retained_failed_demo_processes'])+' 次，原时钟标记进程 '+str(stats['clock_flagged_original_processes'])+' 次。</p>')
    text.append('<h2 id="history">115个alpha版本逐项审计</h2><p>按版本清单顺序审阅源差异与原发布证据；早期restic恢复、Git历史bundle和路径重命名修正均留存。不是按历史宣传数字直接相加。已具备、平台/引擎专用、缺失等价证明、历史拒绝及本轮实验均分别记录。</p><input id="filter" placeholder="筛选版本、优化、函数或结论…"><p id="visible"></p>')
    rs=[]
    for v in versions:
        matching=[r for r in ideas if r['version']==v['version']]
        if not matching:matching=[dict(id=o['id'],title=cn.get(o['id'],o['title']),disposition=o['status'],reason=o.get('decision','')) for o in opts if o['version']==v['version']]
        for r in matching:rs.append([e(v['version']),e(r['id']),e(r['title']),e(r['disposition']),e(r.get('closure_reason',r.get('reason',''))),e(r.get('closure_scope','')),e(json.dumps(r.get('outcomes',{}),ensure_ascii=False))])
    text.append(table(['版本','条目','优化思路','结论','实现差异/理由','覆盖边界','本轮实验结果'],rs,'searchable'))
    text.append('<p>'+link(report_data/'history-decisions.csv','逐项CSV')+'；'+link(report_data/'history-decisions.json','完整证据路径JSON')+'；'+link(ROOT/'history','冻结历史源码与原证据')+'</p>')
    text.append('<h2 id="delivery">交付、版本与复现</h2><p>基线Git：<code>51cac80f7bb0f466869da573ae9422f0885a9672</code>；交付标签：<code>'+e(review['tag'])+'</code>。最终提交与远端核验由独立发布回执记录，避免在提交内嵌其自身哈希。</p>')
    text.append('<p>DLL SHA256：<code>'+e(build['dll_sha256'])+'</code><br>Ext SHA256：<code>'+e(build['ext_sha256'])+'</code></p><p>'+link(delivery/'NvFlexReleaseD3D_x64.dll','交付DLL')+'；'+link(ROOT/'evidence/final-review.json','显式终验审阅')+'；'+link(PROJECT/'OPENFLEX_EXECUTION_LEDGER.md','账本与归档入口')+'；'+link(ROOT/'publication/git-publication.json','Git发布回执')+'</p>')
    text.append('<p>在原工作区、MSVC开发环境中使用CMake/Ninja构建NvFlexReconstructed目标，保持preserved shader schedule与frontend FP policy。所需FleX头文件、原Ext、场景资产及工具链沿用工作区依赖；仅克隆本仓库不会自动获得外部依赖。构建命令、输入哈希、每个候选独立source/build目录和复跑脚本均保留。原始数据位于Build目录，未把大量二进制轨迹塞进Git仓库。</p>')
    text.append('<pre>cmake -S DisassemblyFleX -B Build/DF-rebuild -G Ninja -DDISASSEMBLYFLEX_WORKSPACE="I:/CodeX Project/KG3D_Cloth" -DCMAKE_MAKE_PROGRAM="I:/CodeX Project/KG3D_Cloth/Build/Toolchains/ninja/1.13.2/ninja.exe" -DCMAKE_BUILD_TYPE=Release -DDISASSEMBLYFLEX_BUILD_DEMO=OFF -DDISASSEMBLYFLEX_SHADER_SCHEDULE=preserved -DDISASSEMBLYFLEX_SHADER_FP_POLICY=frontend\ncmake --build Build/DF-rebuild --target NvFlexReconstructed</pre>')
    text.append('<h3>结论适用范围</h3>'+paragraphs(review['limitations']))
    text.append('<script>const box=document.getElementById("filter"),rows=[...document.querySelectorAll(".searchable tbody tr")];function filter(){let n=0;for(const r of rows){const show=r.textContent.toLowerCase().includes(box.value.toLowerCase());r.hidden=!show;n+=show;}document.getElementById("visible").textContent=`显示 ${n} / ${rows.length} 条记录`;}box.addEventListener("input",filter);filter();</script></html>')
    out.write_text('\n'.join(text),encoding='utf8')
make(PROJECT/'ALPHA_MIGRATION_REPORT_CN.html');make(delivery/'REPORT_CN.html')
plain+=['',*review['outcome_notes'],'','实现与实验取舍']
for o in opts:plain+=[o['id']+' '+cn.get(o['id'],o['title'])+' — '+('纳入正式版' if o['status'].startswith('accepted') else '不纳入'),review['candidate_notes'][o['id']]]
for field,title in [('implementation_notes','实现说明'),('performance_notes','性能解读'),('quality_notes','质量审阅'),('limitations','适用范围')]:plain+=['',title,*review[field]]
plain+=['','逐版本详细表、每场景毫秒值/置信区间及原证据链接见ALPHA_MIGRATION_REPORT_CN.html和reports/alpha-migration-20261011/。','DLL SHA256 '+build['dll_sha256'],'Git标签 '+review['tag']]
(PROJECT/'ALPHA_MIGRATION_REPORT_CN.txt').write_text('\n'.join(plain)+'\n',encoding='utf8');shutil.copy2(PROJECT/'ALPHA_MIGRATION_REPORT_CN.txt',delivery/'REPORT_CN.txt')
event('final-report-generated',candidate=candidate,html=str(PROJECT/'ALPHA_MIGRATION_REPORT_CN.html'),data=str(report_data),statistics=stats);print('Chinese reports generated with',len(versions),'versions and',len(ideas),'historical records.')
