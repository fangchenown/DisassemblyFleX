# DisassemblyFleX / OpenFleX alpha8.2c 静态比较 — ARCHIVED / COMPLETE

完成时间：2026-10-10T16:49:42+08:00。此任务无待办、无活动作业，不恢复任何旧性能探索。

- 中文主报告：`I:/CodeX Project/KG3D_Cloth/Build/DisassemblyFleX-OpenFleX82c-Static-20261010/delivery/index.html`
- 逐入口：93对核心 + 20个OF扩展 + 36个Ext；全量C++定义6723、HLSL函数790、OF核心源入口191。
- 预编译程序356记录 / 279唯一容器；225 runtime默认项 / 88构建项；227编译/初始化调用位置。
- 报告核验PASS：8655个HTML、585376个本地链接、2232个冻结源文件、两正式DLL哈希；检索/筛选/分页执行验证通过。
- 包：`DisassemblyFleX-OpenFleX82c-StaticComparison.zip`，48868708字节，11191文件逐个校验通过。
- 包SHA256：`b58045585f12f153cd75661a659a88fe4ff84c0d3357dc18b85777cb4784dd0c`。
- 本轮没有运行FlexDemo/物理求解/性能测试，没有修改两套实现；所有操作均为锁屏可执行CLI。
- 内部AST表达式局限完整公开；静态对应不是逐位数值/性能/全输入等价证明。
- 归档：`I:/CodeX Project/KG3D_Cloth/DisassemblyFleX/Comparison82cExecutionLedgerArchive/20261010-complete`。所有以前任务及归档保留。

## 以下为执行期间的历史断点（已全部关闭，不作为活动指令）

# DisassemblyFleX / OpenFleX alpha8.2c 静态逐项比较 — ACTIVE / GO

用户指定两段对话并要求逐C++函数/方法、逐shader、逐入口比较，分析行为/表现/性能影响，暂不做实际性能测试。本任务只读取/解析/静态核查并生成报告，不运行DLL、FlexDemo或GPU benchmark，不改两项目实现。

## 恢复顺序
1. 本文件、01_ACCEPTANCE.md、state.json、tasks.json、events.jsonl。
2. `Build/DisassemblyFleX-OpenFleX82c-Static-20261010/` 下 identity、inventory、analysis、jobs 及工具；核查活动PID，已有产物按哈希续用。
3. 冻结源码→语法清点/覆盖审计→入口映射→算法/shader/调度/资源逐项分析→中文主报告+全量条目附录→交付/归档。

## 已确定版本
- DisassemblyFleX 使用正式性能修复 final-v2，DLL SHA256 0407fe58026c9d8dc93c36d5adf42d554bb3e660fe1f79eafd666d9a3e81e357。依据对应构建源码快照，不混入旧版本。
- OpenFleX 使用 Release/alpha8.2c/SDK/alpha82c-final-core-v3 的构建源码快照和默认runtime profile；正式Core SHA256 46d2d3ddc01377e0ff1b6019bab68d8801fc620ff017e0599278cb62c0c61b7e。
- 发布commit OpenFleX 194d0a9e7b119fd5226bb005b9aa329e5e7b059d；Wrapper 5e358a569e0d3e4e54e0ba06d57dd4f70c1cc0a5；Sword3 1f5f7374ffc53fa499aa520efcbf227f3fe4fd07。tag/branch同名，需要使用refs/tags/明确消歧。
- 原 alpha8.2c 任务已完成归档，根入口的旧ACTIVE硬目标已被其发布任务更新，不得重新开展旧性能探索。

## 当前断点
已冻结源码：sources/DisassemblyFleX 来自final-v2构建快照；sources/OpenFleX从正式发布source-snapshot.zip提取；另冻结KG3D_OpenFleX、KG3D_FleXAdaptor、OpenGLIntegration发布源码。production_drift两个核心均空，SHA已核实。参考对话采用工具预览+指定JSONL首8MiB/尾96MiB的可见消息（明确不是全历史）；第二个对话的文件截至alpha6.8，8.2c身份以正式Release快照为准。

分析工具全在 Build/DisassemblyFleX-OpenFleX82c-Static-20261010/tools/；所有输入/清单为JSON。Tree-sitter 0.26在本机解析崩溃，已换固定0.25.2+CPP0.23.4（dependencies-025），不影响被比较DLL；安装/错误记录保留。长SPIRV文件名通过Windows扩展路径读写处理。

已完成初步清点：C++定义含lambda/宏/SDK辅助，DF447、OF4288、KG包装1407、Adaptor208、OpenGL374。已恢复190左右条件语法视图和函数生成宏，最后一轮以inventory/summary.json为准。尚有少量函数内部语法节点错误，需做边界/遗漏审计，不能称每个AST表达式都解析完美。

Shader：DF84正式编译内置+3非构建readable示例；OF目前188显式/嵌入HLSL入口（大量宏/字符串生成变体另行整理），KG11、OpenGL15。辅助HLSL函数也已入表。compiled-shaders.json共356记录：DF84DXBC，OF21内嵌DXBC、177内嵌SPIRV、74显式SPIRV文件，去重279容器；Vulkan注册表74项。OF这21个内嵌DXBC与DF程序块无相同项，不能外推为已比较所有运行时编译宏组合。

API：静态PE解析DF93导出，OF113导出，Ext36。规范化前缀后93项对应且序号相同，但实际导出名0项相同；全部93映射到双方定义，见analysis/api-map.json。OF额外20入口另表。OFExt构建先STATIC lib再由发布脚本link /DLL /WHOLEARCHIVE形成测试DLL，这点已查明，不是来源断裂。

关键已核实差异（需要写入证据/逐项报告）：
- DF GetDeviceAndContext返回NvFlex抽象Device/Context，OF返回backend NativeDevice/NativeContext。
- DF回调给GPU buffer wrapper句柄及空间排序映射，solver字段沿用未初始化；OF InvokeCallback先EnsureHostState，构造host向量、按active顺序、初始化solver、捕获异常并回写变化。
- DF GetSprings为空操作；OF读取CPU spring镜像。GetShapeBVH两边不返回BVH，但OF报告unsupported。
- DF CopySolver复制大量GPU/CB/回调/散粒字段并保留已知故障；OF复制选定host粒子/刚体等并retire snapshot，不是同一状态集合。
- OF Windows工厂仅D3D11(1)/Vulkan(3)，D3D12(2)保留枚举但返回unsupported；DF支持D3D11/12，无Vulkan。
- OF FULL_FREQUENCY_SOLVER=ON，half-rate/final-only等关闭，不能把差异说成减频；runtime profile225项默认注入，显式覆盖优先且不少缓存。
- OF D3D11对单一fluid phase、surfaceTension/adhesion/freeSurfaceDrag全零等资格分支启用poly6密度；DF CalculateDensity明确sqrt→(1-r/h)^2→kSpiky1。OF校准有额外poly6路径，可能改变液体表现而不仅是调度优化。

下一步：完成完整配置/编译入口/变体与调用位置目录；建立算法families+逐方法/逐shader语义对应（避免强造同名等价）；做93API逐条差异和20扩展/36Ext说明；生成可搜索逐项HTML/JSON/CSV与中文主报告；最后coverage QA和归档。当前没有GPU测试或构建运行，仍不能归档/完成GO。

## 不变量
- 所有分析生成物在上述Build目录；本目录仅账本。保留三个已有DisassemblyFleX归档、alpha8.2c发布包与各工作区实现。
- “对应”要区分精确同名入口、包装转发、一对多/多对一语义映射、无直接对应；不得强造同名一一对应。
- 每个生产函数/方法、shader入口必须进入机器清单并有源码位置/签名/哈希/分类/分析或明确无对应说明；解析失败必须进入覆盖审计并处理。
- 第三方、测试、工具、声明和宏模板的范围单独说明，不能把未覆盖部分算作已逐项分析。
- 静态事实/条件性推断/历史动态证据分开，不能把两份不同协议历史性能数据相除当成本次测量。
- 仅隐藏CLI和文件处理；不需要解锁、键鼠或截图。


## 后续断点：报告生成 / QA
已生成delivery/index.html与逐条HTML。CPP最终6723（OF4287），修复2个DF截断边界、移除1个ObjC假lambda、编号区分同一行lambda/const重载。补查普通拼接C++字符串又找到3个GPU入口：density Pack、velocity Pack/Unpack；HLSL最终790，OF191入口。新增227编译/初始化调用位置、42部分shader文本、31公开类型及95头文件入口并集。所有93API已有专门差异说明，56额外/Ext入口独立说明。
新关键事实：DF默认maxParticles16384 vs OF0；CreateSolver DF numIterations1/zero gravity+buoyancy vs OF3/gravity.y -9.8/buoyancy1。两侧RegisterOGLBuffer头声明均未出现在Windows PE导出。
下一步等extend_comparison完成→render_report.py→validate_report.py。最后打包/验证/账本归档/GO完成。render/validate均纯CLI无GPU。不得遗漏普通字符串补充后的重新渲染。
