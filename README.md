# DisassemblyFleX

面向 Windows x64 / MSVC / Direct3D 11、Direct3D 12 的 NvFlex 核心 DLL 源码重建工程。

本仓库保存 C++ 实现、重建 HLSL 与配套 SM5 文本指令、构建和测试工具，以及历次任务的执行账本。重建代码不代表恢复了 NVIDIA 原厂的高级源代码、变量名或注释；兼容性结论及验证范围以项目文档和测试证据为准。

## 文档入口

- [alpha 历史优化迁移详细中文报告（HTML）](ALPHA_MIGRATION_REPORT_CN.html)／[文本版](ALPHA_MIGRATION_REPORT_CN.txt)。
- [逐场景统计与 115 个历史版本的逐项审计数据](reports/alpha-migration-20261011/)。

- [工程说明、构建步骤与验证边界](README_CN.txt)
- [当前交付记录](CURRENT_DELIVERY.json)
- [D3D12 性能修复说明](PERFORMANCE_FIX_CN.txt)
- [性能测试说明](PERFORMANCE_TESTING_CN.txt)
- [执行账本与归档索引](OPENFLEX_EXECUTION_LEDGER.md)

## 目录

- `src/`、`include/`：C++ 实现与接口。
- `shaders/recovered/`、`shaders/machine/`：重建 HLSL 与对应文本指令。
- `shaders/readable/`：参考实现。
- `tests/`、`tools/`：验证程序、无窗口 FlexDemo 测试入口与构建工具。
- `reference/`：重建依据和说明。
- `*ExecutionLedger*`：执行记录与历史归档。

## 构建环境

当前构建脚本沿用 `KG3D_Cloth` 工作区布局，需要工作区中的 `FleX` 开发依赖、场景资产及 `OpenFleX/tools/Invoke-OpenFlexCMakeConfigure.ps1` 等工具。详细工具链位置与命令见 [README_CN.txt](README_CN.txt)。

工作区外层 `Build/` 中的 DLL、完整报告及原始测试数据不在本仓库内；历史记录中的本地路径保留原样。仅克隆本仓库不会自动获得这些外部依赖和测试产物。

## 文件完整性

仓库通过 `.gitattributes` 保留原有文件字节和换行，便于核对历史验证记录中的哈希。Python 缓存及本地构建中间文件由 `.gitignore` 排除。

## 本轮性能优化

本轮保留 9 类优化、拒绝 7 类候选，审阅 115 个 alpha 版本与 391 条历史记录。最终版本保留原有 84 个 shader 容器，新增 5 个整数辅助程序；邻居浮点程序改写已经撤回。

在本机 RTX 5080、固定 FlexDemo 无窗口完整物理帧测试中，67 场景等权速度比相对此前 DF 为 D3D11 1.00823、D3D12 1.04486。详见报告中的置信区间、局部负向点估计、P/E 核调度、原有非确定性及测试边界；这些数字不是实际游戏屏幕 FPS。
