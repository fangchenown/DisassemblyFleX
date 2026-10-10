DisassemblyFleX — NvFlexReleaseD3D_x64.dll 源码重建工程

目标平台：Windows x64 / MSVC / Direct3D 11 和 Direct3D 12。
工程包含真实可编译的 C++ 实现、84 个可编译 HLSL、84 个对应的文本指令约束，
以及官方 FlexDemo 场景的无窗口测试程序。运行库不转发到原 NvFlex 核心 DLL。

2026-10-10 正式性能修复：D3D12 常量缓冲区和描述符堆按实际 fence 复用，
并保护外部 Context 切换时的在途资源。说明见 PERFORMANCE_FIX_CN.txt。
当前交付与报告入口见 OPENFLEX_EXECUTION_LEDGER.md。

构建（从 KG3D_Cloth 根目录执行）：
  python -B DisassemblyFleX/tools/fix_task.py python -B DisassemblyFleX/tools/build.py --name my-build

产物：
  Build/DisassemblyFleXPerformanceFix-20261010/builds/my-build/NvFlexReleaseD3D_x64.dll
  Build/DisassemblyFleXPerformanceFix-20261010/builds/my-build/DisassemblyFlexDemo.exe

每次使用新的 --name，旧构建、源码快照和测试证据不会被覆盖。
构建通过 OpenFleX/tools/Invoke-OpenFlexCMakeConfigure.ps1 配置，所有编译生成物留在 Build。
工具链位置目前按此工作区固定在 tools/build.py，可在迁移机器时调整：
  MSVC 14.44.35207；Windows SDK 10.0.26100.0；Python 3.10；CMake；Ninja。
外部开发依赖来自工作区 FleX/external 的 NVAPI、AMD AGS、Aftermath 和 SDK 头文件。
构建核心 DLL 不需要原 NvFlexReleaseD3D_x64.dll 或原始 DXBC 文件。
原 DLL、原 Ext DLL 和 FleX/data 仅用于对照测试；FlexDemo 测试程序使用官方场景代码。

默认 shader 构建模式：preserved。
  1. 检查 HLSL 的可执行语句与对应 .smasm 文本指令的翻译结果一致。
  2. 使用 FXC 编译 HLSL，取得新生成的反射与签名。
  3. 根据 Microsoft 官方 SM5 格式，从文本逐操作数编码指令，不读取原二进制。
  4. 重新计算 DXBC 校验值，反汇编回环逐条检查。
全部 84 个重新编码的程序指令流已独立证明与原程序逐字节一致。
这保留了原浮点求值顺序和寄存器安排；直接让 FXC 重新安排会产生可观测差异。
编辑 HLSL 时需同步修改对应文本指令，否则严格模式会拒绝不一致的源文件。
如需自由编辑普通 HLSL，可显式使用 --shader-schedule fxc；该模式不承诺严格数值复现。
这些是逆向重建源代码，不能据此声称恢复了 NVIDIA 原厂的高级变量名或注释。
详细说明见 reference/SHADER_SCHEDULE_RECOVERY.txt。

运行单个官方场景对照（以下为场景 47，热身 60 帧、测量 240 帧）：
  python -B DisassemblyFleX/tools/fix_benchmark.py --build my-build --suite my-demo --scenes 47 --modes d3d11 --repeats 1
  --modes d3d12 比较原版、旧重建版与新构建；D3D11 比较原版与新构建。

综合 API 回归：
  python -B DisassemblyFleX/tools/fix_regression.py --build my-build --name my-regression

测试全部使用隐藏命令行、无顶层窗口和离屏 GPU 计算，GPU 作业遵循工作区共享锁。
运行期间申请 ES_SYSTEM_REQUIRED，不要求显示器常亮；不依赖鼠标、屏幕截图或已解锁桌面。
没有主动锁定或解锁用户会话；“可锁屏运行”是执行路径设计与无窗口证据，不冒称做过人工锁屏试验。

行为判定：
  - 导出名称、序号、ABI、离散结果、已初始化参数和确定性数据使用严格比较。
  - 官方手册明确 Flex 不保证确定性。GPU 原子累加、并行约束和散粒排列会造成重复波动。
  - 保留所有逐字节不一致记录，单独检查原版重复范围。历史源码重建验收中，个别亚坐标
    精度差使用明确披露的 float32 坐标量化及速度差分精度审计，不写成“逐位相同”。
  - 正式性能修复另外完成 300 帧全场景和代表场景 1800 帧检查；详细结果见修复报告，
    不把有限样本外推为任意时长轨迹逐位恒等。

已保留的原版行为/缺陷，包括：
  GetSprings / GetShapeBVH 的空操作、CallbackParams.solver 未初始化、CopySolver 的
  D3D11 staging 拷贝故障、零长度宿主缓冲区映射故障、资源耗尽后 ID 0 清理循环、
  D3D12 ClearState 与常量缓存不一致，以及本机 D3D12 原生资源读回访问违例。
本工程是兼容重建，不是修复这些原版缺陷的版本；详情见最终中文报告与原始证据。
AMD 分支按反汇编重建，但本机仅实际验证了 RTX 5080 / NVIDIA 驱动 581.15。

当前正式性能修复的报告和交付文件位于：
  ../Build/DisassemblyFleXPerformanceFix-20261010/delivery/
初始源码重建的历史报告和交付仍保留在：
  ../Build/DisassemblyFleX-20261009/delivery/
任务恢复/归档入口：OPENFLEX_EXECUTION_LEDGER.md。
