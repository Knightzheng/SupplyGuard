# SupplyGuard 项目推进报告

> 本文件是跨 Codex 线程的项目事实入口。  
> 顶部快照随推进更新；底部历史记录只能追加，不得删除或改写。  
> 时间统一使用 Asia/Shanghai（UTC+8）。

## 1. 当前状态快照

| 项目 | 当前状态 |
|---|---|
| 项目阶段 | M2：OSV 数据同步与漏洞匹配（进行中） |
| 总体状态 | M0、M1 已验收；M2 Advisory 模型和首批匹配已完成 |
| 当前版本 | v0.1.0.dev0 |
| 公开仓库 | https://github.com/Knightzheng/SupplyGuard |
| 当前开发分支/PR | `codex/osv-advisory-models` / https://github.com/Knightzheng/SupplyGuard/pull/1 |
| 当前工作重点 | 设计 SQLite Advisory Repository、本地索引和原子快照导入 |
| 已完成 | M0、M1；M2 OSV 模型、安全解析、SemVer 区间和可解释组件匹配 |
| 进行中 | M2：OSV 数据同步与漏洞匹配 |
| 下一任务 | 建立与存储实现解耦的 Advisory Repository，并以 SQLite 完成离线包坐标查询 |
| 当前阻塞 | 无 |
| 额外金钱成本 | 0 元 |
| 最后更新时间 | 2026-06-21 17:26，Asia/Shanghai |

## 2. 里程碑看板

| 里程碑 | 状态 | 完成度 | 验收说明 |
|---|---|---:|---|
| M0 治理和工程骨架 | 已完成 | 100% | 治理文档、项目骨架、最小 CLI、独立环境和测试入口均已验证 |
| M1 依赖解析与统一图模型 | 已完成 | 100% | package-lock v2/v3 与精确 requirements 输入、统一图、证据、路径和异常测试均已完成 |
| M2 OSV 同步与漏洞匹配 | 进行中 | 30% | OSV 模型、Schema 关键校验、SemVer 事件范围和首批匹配已完成；同步与本地索引待完成 |
| M3 风险报告和 SBOM | 未开始 | 0% | — |
| M4 API 与 Web 控制台 | 未开始 | 0% | — |
| M5 修复建议、策略与 CI | 未开始 | 0% | — |
| M6 基准、发布与简历材料 | 未开始 | 0% | — |

完成度只用于快速定位，不代表验收通过。里程碑状态必须以 `PROJECT_PLAN.md` 的验收条件为准。

## 3. 当前架构决策

| 编号 | 决策 | 状态 | 理由 |
|---|---|---|---|
| ADR-001 | 核心运行不依赖付费 API、云 GPU 或云服务器 | 已采纳 | 符合用户预算约束并保证项目可复现 |
| ADR-002 | 默认使用 Python 3.12、FastAPI、Typer、SQLite、React/TypeScript | 初步采纳 | 降低本地开发门槛，同时覆盖 CLI、后端与前端能力 |
| ADR-003 | OSV 本地缓存作为核心漏洞数据路径，在线查询仅作为可选能力 | 初步采纳 | 保证离线扫描、可复现和零调用成本 |
| ADR-004 | 核心领域模型与 API/UI 解耦 | 已采纳 | 避免框架绑定并便于测试 |
| ADR-005 | M0 使用 argparse 与 unittest 建立无第三方依赖的离线基线 | 已采纳 | PyPI 当前不可达；先保证独立环境和核心开发链路可运行，Typer/pytest 作为后续可替换工具而非运行前提 |
| ADR-006 | 组件稳定 ID 使用规范化 Package URL | 已采纳 | PURL 可读、确定且便于后续 SBOM 与 OSV 对接；来源证据不参与 ID，避免同一组件因文件位置变化而改变身份 |
| ADR-007 | 首批 Python 输入采用 requirements.txt 精确 `==` 固定版本 | 已采纳 | 可用标准库离线解析；通配符、范围、URL 和 include 不伪装成精确组件，而是显式告警 |
| ADR-008 | M2 首批范围比较只支持 npm SEMVER；PyPI 先支持 affected.versions 精确匹配 | 已采纳 | 错误实现 PEP 440 会产生漏报或误报；未实现的 ECOSYSTEM/GIT 范围返回结构化告警，不静默跳过 |

后续改变已采纳决策时，必须追加新的决策记录并说明替代关系。

## 4. 当前风险与待确认事项

| 编号 | 等级 | 事项 | 处理计划 |
|---|---|---|---|
| R-001 | 已关闭 | 首批 Python 固定依赖格式尚未最终限定 | 已选择 requirements.txt 精确 `==` 格式；uv.lock/Poetry 可作为后续插件 |
| R-002 | 中 | 用户主要面试语言尚未确认 | 核心先保持 Python；在进入 Java 生态或大规模前端工作前再确认，不阻塞 M0 |
| R-003 | 低 | OSV 本地数据规模和同步方式尚未实测 | M2 先针对单一生态做小规模原型与磁盘占用测量 |
| R-004 | 低 | 当前环境访问 PyPI 会长时间无响应 | M0 已采用标准库离线链路；后续引入第三方依赖前先做短时连通性检查，禁止重复长时间重试 |
| R-005 | 中 | PyPI ECOSYSTEM 和 GIT 范围比较尚未实现 | 匹配结果携带 unsupported-version-range 告警；M2 后续优先实现 PEP 440，再评估 GIT 范围需求 |

## 5. 下一线程执行入口

新线程必须先阅读 `PROJECT_RULES.md`，然后执行以下最小任务：

1. 检查项目文件树和 Git 状态。
2. 定义只读 Advisory Repository 协议，按生态和规范化包名查询候选漏洞。
3. 先添加空库、重复导入、事务失败、重启后查询和损坏 JSON 测试。
4. 使用标准库 SQLite 建立本地索引；快照导入失败不得破坏上一份可用数据。
5. 运行 `scripts\check.ps1`，确认现有 41 项测试和新增测试均通过。
6. 更新本文件的当前快照并追加推进记录。

## 6. 推进记录

### 记录 0001：建立项目治理文档

- 时间：2026-06-21，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M0 治理和工程骨架
- 本次目标：创建详细计划、项目推进规则和跨线程进度报告三份 Markdown 文档。
- 开始前状态：项目工作目录为空，没有代码、项目计划或历史报告。
- 实际完成：
  - 建立 `PROJECT_PLAN.md`，定义项目目标、范围、架构、里程碑、测试策略、风险和完成标准。
  - 建立 `PROJECT_RULES.md`，将项目根目录设为唯一可写边界，并规定线程启动、报告、验证、成本和交接规则。
  - 建立 `REPORT.md`，初始化状态快照、里程碑、架构决策、风险和追加式记录模板。
- 创建文件：
  - `PROJECT_PLAN.md`
  - `PROJECT_RULES.md`
  - `REPORT.md`
- 修改文件：无。
- 删除文件：无。
- 关键命令与检查：
  - 只读检查当前工作目录文件树。
  - 搜索项目相关历史记忆；没有发现可复用记录。
- 测试结果：本次仅创建文档，不涉及代码测试；文档创建后需进行文件存在性、边界规则关键字和内容结构检查。
- 技术决策：
  - 将 `D:\code\codex\工作项目` 固定为唯一可写项目根目录。
  - 所有新 Codex 线程必须读取三份根文档。
  - 采用顶部状态快照加底部追加历史记录的报告结构。
  - 项目额外金钱成本目标固定为 0 元。
- 未完成事项：尚未建立代码骨架、版本控制配置、测试环境或 CI。
- 风险与阻塞：无阻塞；首批 Python 依赖输入格式仍待 M1 前确认。
- 下一步：完成 M0 的工程骨架、最小 CLI 和第一个自动化测试。
- 文件边界合规声明：本次只在 `D:\code\codex\工作项目` 内创建文件；对其他目录仅进行了只读搜索，没有外部写入、移动或删除。

### 记录 0002：治理文档只读验收

- 时间：2026-06-21，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M0 治理和工程骨架
- 本次目标：验证三份根文档存在、结构完整，并核对文件边界、报告机制和零成本要求。
- 开始前状态：三份文档已经创建，尚未完成创建后的只读验收。
- 实际完成：
  - 确认三个文件均位于项目根目录。
  - 检查唯一可写目录、外部只读/复制、推进单元、新线程检查清单、M6 验收、初始报告和边界声明等关键内容。
  - 在项目计划成本红线中补充“额外金钱成本预算固定为 0 元”的明确表述。
- 创建文件：无。
- 修改文件：`PROJECT_PLAN.md`、`REPORT.md`。
- 删除文件：无。
- 关键命令与检查：使用 PowerShell 只读列出根目录文件，并以 `Select-String` 检查关键条款。
- 测试结果：三个文件存在；九项关键内容检查全部应通过；本次不涉及代码测试。
- 技术决策及理由：将零成本从隐含约束改成可直接检查的硬指标，避免后续线程误引入付费能力。
- 计划偏差：无。
- 未完成事项：代码骨架、最小 CLI 和自动化测试尚未建立。
- 风险与阻塞：无。
- 下一步：按照“下一线程执行入口”完成 M0 工程骨架任务。
- 文件边界合规声明：所有修改均位于 `D:\code\codex\工作项目` 内；未对外部目录执行写入、移动或删除。

### 记录 0003：完成 M0 离线工程骨架

- 时间：2026-06-21 16:30，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M0 治理和工程骨架
- 本次目标：建立独立 Python 环境、最小 CLI、基础测试链路和本地 Git 仓库。
- 开始前状态：根目录只有三份治理文档，不是 Git 仓库，没有代码、虚拟环境或测试。
- 实际完成：
  - 初始化 `main` 分支本地 Git 仓库，并使用已有 Git 用户身份配置；没有创建远端。
  - 创建项目专用 `.venv`，Python 版本为 3.13.2；`.venv` 已由 `.gitignore` 排除。
  - 建立 Python 包、模块入口、版本元数据和基于 argparse 的零依赖 CLI。
  - 建立 `bootstrap.ps1` 与 `check.ps1`，所有临时目录和 Python 字节码重定向至项目内 `.tmp`。
  - 建立 3 项端到端 CLI 测试，覆盖版本、帮助和未知参数错误。
  - 建立 README、pyproject、编辑器配置、忽略规则和后续模块占位目录。
- 创建文件：`.editorconfig`、`.gitignore`、`README.md`、`pyproject.toml`、`supplyguard/*`、`tests/test_cli.py`、`scripts/*`、`benchmarks/.gitkeep`、`data/.gitkeep`、`docs/.gitkeep`，以及被忽略的 `.venv`、`.tmp`。
- 修改文件：`REPORT.md`。
- 删除文件：无。
- 关键命令与检查：
  - `git init -b main`
  - `scripts\bootstrap.ps1`
  - `scripts\check.ps1`
  - `.venv\Scripts\python.exe -m supplyguard --help`
- 测试结果：Python 语法编译通过；3 项 unittest 全部通过，耗时约 0.235 秒；`--version` 输出 `SupplyGuard 0.1.0.dev0`。
- 技术决策及理由：
  - 用户明确授权创建 Git 仓库和后续 GitHub 发布；本轮只建立本地仓库，远端在提交内容审查后再创建。
  - 用户要求独立虚拟环境，所有执行固定使用项目内 `.venv`。
  - 两次 `pip install -e ".[dev]"` 分别在约 124 秒和 304 秒后超时且无输出；确认并终止两个遗留的本项目 pip 进程。
  - PyPI 短时连通性检查同样超时，因此 M0 改用 argparse、compileall 和 unittest，保持完全离线可运行；没有全局安装依赖。
- 计划偏差：原计划默认采用 Typer、pytest、Ruff 和 mypy；因当前 PyPI 不可达而暂缓。该偏差不影响 M0 的 CLI 与测试验收，也不改变后续核心架构。
- 未完成事项：尚未创建首次 Git 提交或 GitHub 远端；M1 领域模型和解析器尚未开始。
- 风险与阻塞：外部 Python 依赖下载当前不可用，但不阻塞标准库实现的 M1 核心模型与 package-lock 解析器。
- 下一步：提交经过审查的 M0 基线，然后进入 M1，先完成领域模型和相应不变量测试。
- 文件边界合规声明：所有创建、修改、Git 元数据、虚拟环境、缓存和临时文件均位于 `D:\code\codex\工作项目` 内；未向其他目录写入、移动或删除文件。

### 记录 0004：建立 M1 不可变领域模型

- 时间：2026-06-21 16:36，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M1 依赖解析与统一图模型
- 本次目标：实现 Component、DependencyEdge、SourceEvidence 及稳定组件 ID，并先覆盖模型不变量测试。
- 开始前状态：M0 已完成并形成提交 `dcd9cae`；项目没有依赖领域模型。
- 实际完成：
  - 新增 `Ecosystem`，首批定义 npm 和 PyPI。
  - 新增不可变 `SourceEvidence`，规范化分隔符并拒绝绝对路径、目录穿越和非法位置指针。
  - 新增不可变 `Component`，实现 npm scoped 包和 PyPI PEP 503 名称规范化。
  - 使用 Package URL 生成不受来源文件影响的稳定组件 ID，并确定性排序、去重来源证据。
  - 新增 `DependencyEdge`，区分项目直接依赖和组件间传递依赖。
- 创建文件：`supplyguard/domain/__init__.py`、`supplyguard/domain/models.py`、`tests/test_domain_models.py`。
- 修改文件：`REPORT.md`。
- 删除文件：无。
- 关键命令与检查：`scripts\check.ps1`。
- 测试结果：语法编译通过；原有 3 项 CLI 测试和新增 8 项领域模型测试全部通过，共 11 项，耗时约 0.210 秒。
- 技术决策及理由：组件 ID 采用规范化 PURL；证据作为组件附属事实但不参与 ID；领域对象采用 frozen dataclass，防止扫描过程中被隐式修改。
- 计划偏差：无。
- 未完成事项：统一依赖图、环检测、路径输出和 package-lock 解析器尚未实现。
- 风险与阻塞：当前模型只声明 npm/PyPI；增加生态必须补充名称规范化测试。
- 下一步：先建立 package-lock v2/v3 夹具和失败测试，再实现安全解析与 Node 依赖位置解析。
- 文件边界合规声明：所有源码、测试、报告和运行缓存均位于项目根目录内；没有外部文件写入。

### 记录 0005：实现确定性依赖图并修复测试门禁

- 时间：2026-06-21 16:39，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M1 依赖解析与统一图模型
- 本次目标：实现组件合并、引用校验、根到组件路径和环检测，并确保检查脚本正确传递失败状态。
- 开始前状态：领域模型已提交为 `f6f5dad`，没有统一图实现；新增失败测试因缺少 `supplyguard.graph` 而报错。
- 实际完成：
  - 新增不可变 `DependencyGraph`，按 PURL 合并重复组件及来源证据，并确定性排序组件和边。
  - 拒绝引用不存在父组件或子组件的悬空边。
  - 实现直接依赖列表和有上限、可避环的根到目标路径查询。
  - 使用 Tarjan 算法识别循环强连通分量。
  - 修复 `check.ps1` 和 `bootstrap.ps1`，显式检查 Python 子进程退出码，测试失败不再被 PowerShell 错误地报告为成功。
- 创建文件：`supplyguard/graph/__init__.py`、`supplyguard/graph/model.py`、`tests/test_dependency_graph.py`。
- 修改文件：`scripts/bootstrap.ps1`、`scripts/check.ps1`、`REPORT.md`。
- 删除文件：无。
- 关键命令与检查：先运行 `scripts\check.ps1` 得到预期 ImportError，再实现图模块并重新运行检查。
- 测试结果：失败测试复现成功；实现后语法编译通过，16 项 unittest 全部通过，耗时约 0.217 秒。
- 技术决策及理由：图根节点继续以 `DependencyEdge.parent_id = None` 表示，避免将业务项目伪装成包组件；环检测返回确定排序的循环强连通分量，复杂度为 O(V+E)。
- 计划偏差：发现并修复 M0 检查脚本未传播非零退出码的问题；属于必要质量修复，没有扩展产品范围。
- 未完成事项：package-lock 解析、损坏输入处理和真实锁文件夹具尚未实现。
- 风险与阻塞：大图的路径数量可能指数增长，当前通过 `max_paths` 和 `max_depth` 限制；后续基准必须验证。
- 下一步：建立 package-lock v2/v3 夹具，完成安全 JSON 读取、npm 包名提取和 Node 依赖位置解析。
- 文件边界合规声明：所有新增源码、测试、报告、缓存和 Git 修改均位于项目根目录内；没有外部写入。

### 记录 0006：实现 package-lock v2/v3 安全解析

- 时间：2026-06-21 16:49，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M1 依赖解析与统一图模型
- 本次目标：将 npm package-lock v2/v3 转换为统一组件和依赖图，同时显式处理不完整或恶意输入。
- 开始前状态：确定性依赖图已提交为 `58091b8`；没有输入解析器。
- 实际完成：
  - 先建立失败测试，覆盖 v2/v3、scoped 包、嵌套依赖、开发依赖、重复组件、workspace link 和损坏输入。
  - 实现 20 MiB 默认体积限制、UTF-8 解码、JSON 类型校验和 lockfileVersion 校验。
  - 实现 Node 向父级 `node_modules` 查找依赖的解析规则，区分 runtime、development、optional 和 peer 范围。
  - 支持 workspace link 读取目标包元数据，但不执行任何项目脚本。
  - 对缺少版本、无法解析依赖、无法识别位置和失效 link 生成结构化告警，不静默忽略。
  - 将重复包位置合并为稳定 PURL 组件，同时保留全部来源 JSON Pointer。
- 创建文件：`supplyguard/parsers/__init__.py`、`supplyguard/parsers/package_lock.py`、`tests/test_package_lock_parser.py`。
- 修改文件：`supplyguard/domain/__init__.py`、`supplyguard/domain/models.py`、`supplyguard/graph/model.py`、`REPORT.md`。
- 删除文件：无。
- 关键命令与检查：`scripts\check.ps1`；`.venv\Scripts\python.exe -W error -m unittest discover -s tests -p 'test_*.py'`；`git diff --check`。
- 测试结果：首次失败测试因缺少 DependencyScope/解析器而按预期失败；实现后语法编译、23 项 unittest、warnings-as-errors 和 diff 格式检查全部通过；普通测试约 0.234 秒。
- 技术决策及理由：组件 scope 保存在依赖边而非组件；解析器只读取 lockfile，不调用 npm；所有非致命数据缺口必须形成结构化告警。
- 计划偏差：没有建立单独 JSON fixture 文件，当前小型夹具以内联 JSON 保持测试可读性；引入大型公开样本时再使用固定文件和许可证记录。
- 未完成事项：Python 固定版本依赖解析器、更多真实公开 lockfile 回归样本和 CLI scan 接入尚未完成。
- 风险与阻塞：npm alias、更多 workspace 布局及平台条件依赖仍需真实数据验证；现阶段不会宣称覆盖全部 npm 语义。
- 下一步：选择 requirements.txt 精确 `==` 固定格式作为首批 Python 输入，先定义注释、环境标记、哈希和非固定版本处理测试。
- 文件边界合规声明：真实文件测试只在项目内 `.tmp` 创建临时目录；所有其他代码、报告、缓存和 Git 修改也均位于项目根目录内。

### 记录 0007：完成 Python 固定依赖解析与 M1 验收

- 时间：2026-06-21 16:56，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M1 依赖解析与统一图模型
- 本次目标：完成第二类 MVP 输入并对 M1 整体验收。
- 开始前状态：package-lock 解析已提交为 `640abc6`；Python 输入格式尚未确定。
- 实际完成：
  - 选择 requirements.txt 精确 `name==version` 作为首批 Python 输入。
  - 先建立失败测试，再实现注释、extras、hash continuation、重复固定版本和环境标记解析。
  - 对版本范围、通配符、URL、include、index 指令和其他未知格式生成显式告警并跳过。
  - 实现 5 MiB 默认体积限制、UTF-8 文件入口和项目相对行号证据。
  - 将 ParseWarning 提取为解析器共享模型。
  - 复核 M1 验收项并同步 README 当前能力与限制。
- 创建文件：`supplyguard/parsers/models.py`、`supplyguard/parsers/requirements.py`、`tests/test_requirements_parser.py`。
- 修改文件：`supplyguard/parsers/__init__.py`、`supplyguard/parsers/package_lock.py`、`README.md`、`REPORT.md`。
- 删除文件：无。
- 关键命令与检查：`scripts\check.ps1`；`.venv\Scripts\python.exe -W error -m unittest discover -s tests -p 'test_*.py'`；`git diff --check`。
- 测试结果：首次失败测试因 requirements 模块不存在而按预期失败；实现后语法编译、29 项 unittest、warnings-as-errors 和 diff 格式检查全部通过；普通测试约 0.251 秒。
- 技术决策及理由：requirements 输入只接受真正精确的 `==` 版本；解析器不安装、不解析 include、不访问索引，也不执行环境 marker，从而保持确定性和安全边界。
- 计划偏差：M1 原计划只笼统写“Python 固定版本输入”，现已明确为 requirements 精确固定格式，属于计划内决策。
- 未完成事项：尚未加入真实公开仓库回归样本；CLI 尚未暴露 scan 命令；这些不属于 M1 的核心验收阻塞项。
- 风险与阻塞：requirements 是扁平清单，无法还原真实传递来源；当前图只表达“文件列出这些组件”，后续报告必须明确这一限制。
- 下一步：进入 M2，以固定 OSV 小样本实现 advisory 模型、事件范围匹配和本地存储接口。
- 文件边界合规声明：文件读取测试只在项目内 `.tmp` 写入临时数据；源码、测试、报告、缓存和 Git 修改全部位于项目根目录内。

### 记录 0008：创建并发布 GitHub 公开仓库

- 时间：2026-06-21 17:22，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：跨里程碑发布检查点
- 本次目标：建立以项目命名的 GitHub 公开仓库，完善公开 README 并推送现有历史。
- 开始前状态：本地 `main` 含 5 个功能提交，没有远端；用户已经安装 GitHub CLI 并认证账号 `Knightzheng`。
- 实际完成：
  - 重写公开 README，补充项目目标、当前进度、已实现能力、架构图、快速开始、29 项测试范围、安全边界和治理入口。
  - 将 pyproject 中的占位 URL 替换为真实 GitHub 地址。
  - 增加 Apache License 2.0 文本，与 pyproject 许可证声明保持一致。
  - 运行测试、diff 检查和敏感信息扫描后形成提交 `42d8646`。
  - 创建公开仓库 `Knightzheng/SupplyGuard`，配置 `origin`，推送 `main` 全部历史。
  - 设置仓库描述和 `sbom`、`software-supply-chain`、`security`、`osv`、`python` topics。
- 创建文件：`LICENSE`。
- 修改文件：`README.md`、`pyproject.toml`、`REPORT.md`、项目内 `.git/config`。
- 删除文件：无。
- 关键命令与检查：`scripts\check.ps1`；`git diff --check`；`rg` 敏感字段扫描；`gh repo create SupplyGuard --public --source . --remote origin --push`；`gh repo edit`。
- 测试结果：29 项 unittest 全部通过，约 0.248 秒；敏感信息赋值扫描无命中；仓库查询确认 visibility 为 PUBLIC，地址为 `https://github.com/Knightzheng/SupplyGuard`。
- 技术决策及理由：新仓库直接以现有 `main` 历史初始化，没有创建无意义的初始 PR；后续功能开发应使用分支和 PR 工作流。
- 计划偏差：无。
- 未完成事项：M2 尚未产生代码；GitHub Actions 将在需要 CI 时按计划加入。
- 风险与阻塞：GitHub 创建后的默认分支元数据可能存在短暂同步延迟，但 `main` 已成功推送并设置 upstream。
- 下一步：开始 M2，先用仓库内固定 OSV 样本实现 Advisory 模型、版本事件范围和匹配测试。
- 文件边界合规声明：本地文件修改仅发生在项目根目录和项目内 `.git`；GitHub 写入属于用户明确授权的远端仓库操作，没有写入其他本地目录。

### 记录 0009：启动 M2 OSV 模型与首批匹配

- 时间：2026-06-21 17:24，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M2 OSV 数据同步与漏洞匹配
- 本次目标：基于 OSV Schema 建立 Advisory 领域模型、事件区间和可解释组件匹配基线。
- 开始前状态：公开仓库已建立，`main` 最新提交为 `f2344a3`；M2 尚无代码。
- 实际完成：
  - 创建分支 `codex/osv-advisory-models`。
  - 只读核对 OSSF 官方 OSV Schema，确认 affected/package/ranges/versions 及 introduced、fixed、last_affected、limit 结构。
  - 添加仓库内合成 OSV 固定样本，不依赖在线测试数据。
  - 实现不可变 Advisory、AffectedPackage、VersionRange 和 VersionEvent 模型。
  - 实现无第三方依赖的 SemVer 2.0 比较，覆盖 prerelease 顺序和 build metadata 忽略规则。
  - 实现 OSV UTF-8/体积限制、时间戳、事件结构和 endpoint 语义校验。
  - 实现 npm SEMVER 范围、npm/PyPI 显式版本匹配及结构化匹配证据。
  - 对 ECOSYSTEM/GIT 或非法版本返回结构化告警，不将未知状态当成安全。
  - 同步 README 的 M2 进度、架构范围、安全限制和 41 项测试说明。
- 创建文件：`supplyguard/advisories/*`、`supplyguard/matching/*`、`tests/fixtures/osv/OSV-SYNTHETIC-0001.json`、`tests/test_osv_advisories.py`、`tests/test_advisory_matching.py`。
- 修改文件：`supplyguard/domain/__init__.py`、`supplyguard/domain/models.py`、`README.md`、`REPORT.md`。
- 删除文件：无。
- 关键命令与检查：官方 schema 只读请求；`scripts\check.ps1`；warnings-as-errors unittest；`git diff --check`。
- 测试结果：初始测试按预期因模块不存在而失败；首次实现暴露无效混合 endpoint 夹具和开放区间 None 比较缺陷，修复后 41 项 unittest 与 warnings-as-errors 全部通过，普通测试约 0.305 秒。
- 技术决策及理由：严格遵守同一 OSV range 中 fixed 与 last_affected 互斥；只实现能够验证的 SemVer 比较，PEP 440/GIT 不做猜测性比较。
- 计划偏差：无。
- 未完成事项：SQLite 索引、快照导入、增量同步、PyPI ECOSYSTEM 范围和批量组件扫描尚未实现。
- 风险与阻塞：当前匹配覆盖面有限但限制已显式返回；没有外部服务阻塞。
- 下一步：定义 Advisory Repository 接口，使用标准库 SQLite 实现按生态/包名的离线候选查询和原子快照替换。
- 文件边界合规声明：固定样本、临时测试数据、源码、报告和缓存全部位于项目根目录内；外部 OSV Schema 仅只读访问。
- 勘误：记录 0008 的时间误写为 17:22；当时 `Get-Date` 实际输出为 2026-06-21 17:15 +08:00。历史记录不改写，本条追加纠正。

### 记录 0010：推送 M2 分支并创建草稿 PR

- 时间：2026-06-21 17:26，Asia/Shanghai
- 执行者：Codex 当前线程
- 对应里程碑：M2 OSV 数据同步与漏洞匹配
- 本次目标：按 GitHub 分支工作流发布 M2 第一单元，形成可审查检查点。
- 开始前状态：M2 代码、README 和记录已经通过 41 项测试，尚未提交到远端功能分支。
- 实际完成：
  - 提交 `04c1a67 feat: add OSV advisory matching`。
  - 推送 `codex/osv-advisory-models` 并设置 upstream。
  - 创建草稿 PR #1 `[codex] add OSV advisory matching`，目标分支为 `main`。
  - PR 正文记录变更、原因、影响、未实现边界和验证命令。
- 创建文件：项目跟踪文件无新增；忽略目录 `.tmp` 中创建 `pr-body.md` 作为 GitHub CLI 输入。
- 修改文件：`REPORT.md`。
- 删除文件：无。
- 关键命令与检查：`git push -u origin codex/osv-advisory-models`；`gh pr create --draft`；`gh pr view 1`。
- 测试结果：提交前 41 项 unittest 与 warnings-as-errors 全部通过；PR 查询确认 state=OPEN、isDraft=true、base=main、head=codex/osv-advisory-models。
- 技术决策及理由：M2 后续小单元继续推送到同一草稿 PR，待本阶段检查点稳定后再转为可审查状态。
- 计划偏差：首次 `gh pr view` 未提供 PR 编号而返回参数错误；PR 已在前一步成功创建，随后使用编号 1 查询确认，没有重复创建。
- 未完成事项：草稿 PR 未合并；SQLite Repository、快照导入和数据同步仍待实现。
- 风险与阻塞：无。
- 下一步：在当前功能分支先以失败测试定义 Advisory Repository 和原子 SQLite 快照导入，再实现代码并推送到 PR #1。
- 文件边界合规声明：本地跟踪修改仅位于项目根目录；PR 临时正文位于项目内 `.tmp`；远端写入仅针对用户授权的 `Knightzheng/SupplyGuard`。

---

## 7. 推进记录模板

后续线程复制以下模板，在“推进记录”末尾追加，不得覆盖历史条目：

```markdown
### 记录 NNNN：简短标题

- 时间：YYYY-MM-DD HH:mm，Asia/Shanghai
- 执行者：Codex 线程或用户
- 对应里程碑：M0-M6
- 本次目标：
- 开始前状态：
- 实际完成：
- 创建文件：
- 修改文件：
- 删除文件：
- 关键命令与检查：
- 测试结果：
- 技术决策及理由：
- 计划偏差：无；如有则说明原因和影响
- 未完成事项：
- 风险与阻塞：
- 下一步：必须写成新线程可以直接执行的具体步骤
- 文件边界合规声明：确认所有写入、删除、移动、缓存和临时文件均位于项目根目录内
```
