# SupplyGuard

SupplyGuard 是一个离线优先的软件供应链安全分析平台。项目将解析依赖清单与 SBOM，使用公开漏洞数据构建可解释的风险报告、依赖路径和修复建议。

当前已完成 **M1：依赖解析与统一图模型**，准备进入 OSV 数据与漏洞匹配阶段。

## 当前能力

- 提供可运行的 `supplyguard` CLI 骨架。
- 支持 `--version` 和 `--help`。
- 提供 npm package-lock v2/v3 安全解析，包括嵌套依赖、scoped 包和 workspace link。
- 提供 Python `requirements.txt` 精确固定版本解析。
- 使用规范化 PURL 作为稳定组件 ID，并保留项目相对来源证据。
- 提供确定性依赖图、根到组件路径查询和循环依赖检测。
- 对无法解析、未固定或缺少版本的输入生成显式告警。
- 所有开发缓存、临时文件和虚拟环境均限制在项目根目录内。
- 提供语法编译检查和标准库自动化测试的统一入口。

漏洞数据同步、漏洞版本匹配和风险分析将在后续里程碑实现，当前版本仍不应被描述为可用的漏洞扫描器。

## 环境要求

- Windows PowerShell
- Python 3.12 或更高版本
- M0 阶段不需要下载第三方 Python 依赖

## 本地初始化

在项目根目录执行：

```powershell
.\scripts\bootstrap.ps1
```

脚本会创建项目专用的 `.venv`，并把 Python 字节码和临时文件全部放在当前项目目录中，不修改全局 Python 环境。

## 使用 CLI

```powershell
.\.venv\Scripts\python -m supplyguard --version
.\.venv\Scripts\python -m supplyguard --help
```

## 运行质量检查

```powershell
.\scripts\check.ps1
```

检查内容包括 Python 语法编译检查和 `unittest` 自动化测试。Ruff、mypy、pytest 等第三方质量工具将在依赖网络可用后引入，但不会影响当前离线检查链路。

## 项目治理

开始修改前必须阅读：

- `PROJECT_RULES.md`：文件边界、成本、测试和交接硬规则。
- `PROJECT_PLAN.md`：功能范围、架构、里程碑和验收标准。
- `REPORT.md`：当前状态、风险、决策和历史推进记录。

项目额外金钱成本目标为 **0 元**，核心能力不得依赖付费 API、云 GPU 或云服务器。
