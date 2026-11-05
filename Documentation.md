# 项目执行记录

## D1 成果提交与 D2 启动条件复核 · 2026-11-05

用户要求创建提交、按文档检查 D1 并决定 D2 是否可启动、提供提示词。本地提交 `964b729` 已保存 D1 工程、文档与验收证据（210 文件），未推送，既有 `note.assets/` 保留未提交。本轮复核 JUnit 216 项零失败/跳过、6 项 HTTP 记录及 75 个工程文件指纹，支持 D1 本地门已通过；检查方法、退出码、历史证据与本轮核对的区别、行尾空格保留例外、D2 范围和启动提示词见[复核报告](docs/development/reports/2026-11-05_D1_review.md)。

结论：D2 技术依赖满足，建议下一轮明确授权仅 D2 后启动；本次不实施 D2、不推进 D3。真实模型缺口仅阻塞 D2 live 分支，不能以 FakeModel 代替真实验收。现行阶段状态仍见[progress](docs/development/progress.md)。

## 自动本地提交授权 · 2026-11-05

来源：用户要求“给ai新增加一条规则在合适的时候自动提交代码”。已在 [AI 自动提交规则](AGENTS.md#自动提交代码)明确：独立任务完成、相关检查通过及文档同步后主动本地提交；仅纳入本轮归属明确的改动，混合文件按差异块处理；归属不清或无法安全拆分时保留并报告。不自动推送或改写历史，不扩大 D1 以外的实施范围。此前“不提交/推送”记录保留为历史，此后的本地提交适用本次授权。

本轮仅补充规则及本记录。开始时两份文件均已有未提交改动，且工作区包含大量既有 D1 成果；本轮保留这些改动，不将它们一并提交。后续任务按新规则检查改动归属并在满足条件时提交。

## D1 文档可读性整改 · 2026-11-04

来源：用户本轮仅授权文档整改和教学补充。重构[README](README.md)为面向初学开发者的统一操作入口；新增[开发者指南](docs/开发者指南.md)，按概念、作用、本项目代码和验证讲解；在[D1 报告顶部](docs/development/reports/2026-11-04_D1.md#非技术读者快速了解-d1)增加通俗状态说明，原技术正文和历史证据保留。README 继续唯一维护现行安装、配置、初始化、启动和排障步骤，指南不复制可执行命令。

本轮不修改业务代码、数据库结构、技术契约、锁文件或原始材料，不运行应用/业务测试、模型或数据库维护；D1 保持 blocked，后续阶段状态不变。范围、链接/锚点/命令字段核对及文件指纹比较见[文档整改记录](docs/development/reports/2026-11-04_D1_文档可读性整改.md)和[验证结果](docs/development/reports/2026-11-04_D1_docs/validation.json)。完成后停止，不推进 D2；恢复 D1 时按 README 先配置本机受控连接并只读核验，不把本次文档整改当执行数据库操作。

## D1 正式实施批准 · 2026-11-04

来源：用户本轮明确批准[命名审查方案](docs/development/reports/D1_数据库命名变更审查与创建授权方案.md)，授权仅限[D1 任务卡](docs/development/tasks/D1_PostgreSQL与只读业务.md)。采用 finance_tax_dev / finance_tax_test、finance_tax_app / finance_tax_migrator，两个库保留 harness schema；测试改为 finance_tax_test 精确允许名单，首轮串行，保留环境、实例、目标、角色、认证后核验和禁止回落。批准影响及 FR/DR/NFR/AC 列表沿用下方命名审查记录；正式需求 v1.3 与机器接口契约不变。

允许先只读核验本机 PostgreSQL 18 身份、实例和对象归属；缺失对象可创建，已存在同名对象仅检查报告差异，不接管、不改密码或所有者。先实现保护和隔离，再测试库迁移/seed/grant/验收，通过后才准备开发库。测试清理只限通过全部保护的 finance_tax_test；禁止删除数据库/容器/卷。tax_db 不连接、不修改、不作模板。凭证只由本机受控提供，不读取 pgAdmin 密码。保留现有工作区改动，不提交/推送，不推进 D2。数据库缺凭证时继续无依赖实现，真实门标 blocked；收尾见后续 D1 报告和[progress](docs/development/progress.md)。

## D1 实施交接 · 2026-11-04

仅 D1 的无连接实现、规范化资料和验收代码已提供，真实 PostgreSQL 门因未提供本机受控连接 blocked，**D1 未完成**。实现范围、失败修复、命令/退出码、子项和恢复动作见[D1 报告](docs/development/reports/2026-11-04_D1.md)，唯一状态见[progress](docs/development/progress.md)，逐项记录见[summary](docs/development/reports/2026-11-04_D1/summary.json)。没有真实认证 SQL、创建对象、迁移/seed/授权或 tax_db 连接；不把规范化金额复算、配置检查、测试跳过当真实 PG 通过。D2 及后续未运行，未提交/推送。

实施选择：原生 PostgreSQL 由受控 Python bootstrap 负责，替代本阶段主要文件清单中的空卷 shell 入口；Compose 交付仍留 D6。首迁移冻结 SQL 与集中 SQLAlchemy 表模型分开，后续模型变化不改写旧迁移。连接仅支持本机回环/5432；未来部署主机注册由部署阶段补充实测。写维护和测试 schema 重建还需匹配本项目创建来源回执，既有同名对象无回执不自动采纳。正式需求及机器契约指纹对照见[完整性记录](docs/development/reports/2026-11-04_D1/summary.json)；启动统一到[README](README.md#本机凭证与首次数据库准备)。

可恢复下一动作：操作者仅在本机受控补 ADMIN_DATABASE_URL 和双测试连接，按 README 先只读核验；同名对象先报告差异并暂停，缺失对象按授权创建。真实测试门通过后才准备开发库，随后补齐 D1 报告。当前完成阻塞交接并停止，不推进 D2；恢复时从 D1 门继续，不重做 D0、不重置 tax_db。

## D1 数据库命名决定与安全方案审查 · 2026-11-04

用户已决定开发库 finance_tax_dev、测试库 finance_tax_test、应用角色 finance_tax_app、维护角色 finance_tax_migrator；管理员预计 postgres，现存 tax_db 必须保护。授权仅为审查与文档，本轮不连接/创建/改配置/实现 D1。新名已决定，不再把上轮 harness/harness_test_d1 当待执行目标；完整影响、SQL 与 pgAdmin/Codex 分工见[命名审查方案](docs/development/reports/D1_数据库命名变更审查与创建授权方案.md)。

实施补充待确认项：建议保留 harness schema，以精确 finance_tax_test 允许名单取代旧 harness_test_ 前缀，并保留 APP_ENV/实例/三元组/角色/认证后目标核对及无回落保护；tax_db 在所有项目真实连接入口拒绝，不改其数据/结构/ACL。原依据为[契约6.3](docs/architecture/12_开发实施契约补充.md#63-运行角色与bootstrap)、[原测试保护](docs/architecture/05_数据库与数据架构设计.md#10-初始化迁移与备份)、[测试 fixture](docs/development/04_测试与验收规范.md#2-可复现fixture)及[AGENTS](AGENTS.md#代码与数据边界)。选项 A 保留 schema（建议）/B 改 finance_tax；安全方案与对象执行尚待确认，不改现行契约假称已生效。

影响 FR-003/004/005/013、DR-001/006/010/011、NFR-002/003/006/008 与 AC-001/002/005/006/007/013/014/032/036/038 的部署/隔离取证，不改业务定义；后续同步文件、TC052 等保护子项及验收要求见[影响表](docs/development/reports/D1_数据库命名变更审查与创建授权方案.md#名称变更的逐项影响)和[批准后同步清单](docs/development/reports/D1_数据库命名变更审查与创建授权方案.md#批准后同步清单与本轮验证)。受影响的目标执行与正式契约/代码实施暂停；本轮已完成无依赖的来源审查、可审阅 SQL 方案和[文档/范围验证](docs/development/reports/2026-11-04_D1_naming_review/review-validation.json)。下一动作等待用户确认方案及另行授权执行/正式 D1，当前停止；不修改 tax_db，不执行新旧前检命令。

## D1 开发前审查与环境准备 · 2026-11-04

用户仅授权前检与环境准备，尚未授权 D1 业务实现及数据库/容器/卷创建删除重置。用户本轮确认 D0 自动化与人工启动检查完成；本轮仅复核工程完整性及只读环境。结论和具体待执行步骤见[D1 开发前检查与环境准备](docs/development/reports/D1_开发前检查与环境准备.md#当前环境检查的实际结果)：现有 postgresql-x64-18 服务运行，已有 18.6 客户端且 127.0.0.1:5432 接受连接，优先考虑复用；Docker 本地 API 管道不可用。认证 SQL、项目库/角色/数据归属和权限均未验证，四类连接未提供，不能据就绪状态认定 D1 验收完成。

本轮保存[环境命令结果](docs/development/reports/2026-11-04_D1_preflight/environment-checks.json)、[系统查询权限重试](docs/development/reports/2026-11-04_D1_preflight/host-readonly-retry.json)、[原生 PG 查询](docs/development/reports/2026-11-04_D1_preflight/postgresql-native.json)及[基线完整性](docs/development/reports/2026-11-04_D1_preflight/baseline-integrity.json)：33 个 D0 非 Markdown 文件和 14 个保护输入 hash 保持一致。未改工程、依赖、需求/架构/契约或 .env；未安装工具、修改系统、启动服务或执行业务测试。文档路径/锚点与修改范围检查见[验证结果](docs/development/reports/2026-11-04_D1_preflight/review-validation.json)，状态见[progress](docs/development/progress.md)。

待用户确认的对象操作：是否复用当前实例、批准项目库 harness 与专用测试库 harness_test_d1 及角色的查重/归属核实和缺失时建立；凭证通过本机受控方式提供，不在聊天索要明文。具体边界见[风险与正式启动条件](docs/development/reports/D1_开发前检查与环境准备.md#风险需用户确认及正式启动条件)。下一动作仅等待用户正式 D1 授权及对象范围确认，当前停止，不执行报告中的未来命令，不推进 D2。

## Markdown 引用与导航规范落实 · 2026-11-04

按用户本轮指令在[AGENTS 独立章节](AGENTS.md#markdown-文档引用锚点与可追溯性规范)写入长期规则，修复 D0 报告、Plan、progress、README 和本记录中的关键依据/证据引用；通过[总计划](docs/development/02_开发实施总计划.md#6-报告与成果)和[报告规范](docs/development/reports/README.md)纳入后续阶段交付。修改范围、修改前后示例、实际检查及无法精确定位的限制见[落实记录](docs/development/reports/2026-11-04_markdown_navigation.md#验证结果与边界)及[机器验证明细](docs/development/reports/2026-11-04_markdown_navigation/link-validation.json)。本次只做文档维护，不改业务代码、依赖、需求/架构/实施契约和 D0 原始证据，不重跑业务测试；保留已有用户改动及历史验收结论。任务完成后停止，D1 仍未授权。

## 统一启动说明维护规则 · 2026-11-04

来源：用户本轮明确要求。从 D0 起指定根目录 [README](README.md) 为开发者统一启动入口；各阶段报告只记录该阶段特有的执行、测试和验收命令，通用启动引用 README。后续启动方式变化须同次更新 README、替换失效步骤并核对引用。已同步 [AGENTS](AGENTS.md#统一启动说明与阶段命令)、[导航](docs/development/00_开发导航.md)、[Plan](Plan.md)、[总计划](docs/development/02_开发实施总计划.md#6-报告与成果)、[D0](docs/development/tasks/D0_工程与配置基线.md#开发任务)/[D6](docs/development/tasks/D6_部署与竞赛交付.md#开发任务)任务卡和[报告规范](docs/development/reports/README.md)；D0 历史验收命令保留并明确标记历史证据。移除 AGENTS 中重复的待实现启动步骤，README 补充独立终端缓存设置及停止方法。

本轮仅调整文档，保留本轮前已有的 GitHub 交接日期改动；未修改工程、保护输入或 D0 验收结果，未推进 D1。Markdown 本地链接及代码围栏检查通过，git diff --check 首次发现两张任务卡新增行的换行符空白告警，统一为 LF 后复验通过；本轮未运行应用或业务测试。变更范围见当前 Git diff；当前已是 Git 仓库，以现有 Git 状态为准，早期非仓库记载属于历史。下一阶段须在获授权后读取对应卡并核对统一启动说明；D1 仍未授权。

## GitHub 上传交接 · 2026-11-04

按用户要求将现有 D0 项目整理为本地 Git 仓库，`main` 指向 `https://github.com/xiaos300/finance-tax-assistant.git`；远端查询为空仓库。已按 `.gitignore` 排除环境文件、虚拟环境、依赖和缓存，完成初始提交；本地提交身份设为 `xiaos300 <xiaos300@users.noreply.github.com>`。HTTPS 推送和 Windows 凭据管理器非交互重试均因缺少 GitHub 认证失败，SSH 也无有效公钥；**远端尚未上传**。下一动作：用户在本机完成有仓库写权限的 GitHub 登录后运行 `git push -u origin main`，再以 `git ls-remote origin refs/heads/main` 核对提交哈希。没有推进 D1 或改变 D0 验收状态。

## 当前交接 · 2026-11-03 · D0 完成后停止

用户明确授权仅实施 D0，并要求验收交接后停止。已建立 FastAPI/Pydantic 2 与 Vue 3/TypeScript/Vite/Pinia 最小工程，实际解析依赖锁并冻结安装；数据库/维护设置独立于模型，test_stub 仅 test 可配，健康接口、最小严格 DTO、错误封装和安全脚本已实现。最终验收退出 0（[D0 机器汇总](docs/development/reports/2026-11-03_D0_baseline/summary.json)、[执行记录](docs/development/reports/2026-11-03_D0_baseline/commands.json)）：后端18项、Vitest 1项、typecheck/build、live=200/ready=503、源码与构建秘密扫描通过。[TC061/TC051 定义](docs/development/test-cases.json)：TC061 完整 passed；TC051 仅配置子项通过，整项留 D2。详情见 [D0报告](docs/development/reports/2026-11-03_D0_baseline.md)、[progress](docs/development/progress.md)及 [启动说明](README.md)。

实施选择与来源：按[D0 卡](docs/development/tasks/D0_工程与配置基线.md#接口任务)和[契约1.2](docs/architecture/12_开发实施契约补充.md#7-http前端与生命周期的补足)保持无数据库/模型网络调用；ready 在本阶段保守返回未准备，真实准备验证留 D1。uv 0.13.7 局部安装在忽略目录，缓存显式放项目内；npm 使用 npm.cmd，脚本支持 Windows PowerShell 5.1，不更改系统执行策略。首次依赖漏洞/Node警告已通过更新测试依赖、精简依赖解决，最终 npm audit 0。Vite 默认清空已有 dist 在当前 Windows/Node 组合产生原生进程异常；Vite 7.3.7 配合校验路径和拒绝链接的逐项清理包装器已实测通过。pytest 非必要缓存关闭，避免其相对路径校验/权限问题。没有修改需求或核心选型，也没有新增业务接口。

保留的限制：psql、pwsh缺失，Docker仅CLI版本取证，PostgreSQL 18服务器/角色/迁移/seed/专属测试库均未验证；真实 DeepSeek 配置与 probe 未执行。未初始化 Git，未提交/推送；官方材料及 requirements 哈希未变（[当期 protected_input_hashes 记录](docs/development/reports/2026-11-03_D0_baseline/summary.json)）。D1 入口条件为用户另行授权、读取 D1 卡与本报告、落实 PostgreSQL 18 及维护/应用/专属测试连接。下一动作仅等待审阅，不推进后续阶段。

## 准备交接 · 2026-11-03（D0授权前历史）

已盘点需求、架构、机器契约、开发任务卡和现有文件，建立根目录规则、里程碑入口与交接记录。当前没有正式前后端工程、依赖锁、迁移或运行脚本，目录也尚未初始化 Git。D0—D6 尚未开始，D7 未纳入。获开发授权后的下一步是读 D0 任务卡，探测本机运行时并开始工程基线。当前状态见 [progress](docs/development/progress.md)。

三份根文档按「规则、里程碑、交接」分工。每阶段实测后更新状态及报告，将验证结果留在工作区供下一次继续。 [OpenAI 官方文章《Run long horizon tasks with Codex》](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)

## 复用的基线

| 内容 | 维护位置 |
| --- | --- |
| 业务范围、优先级、验收及追踪 | [需求基线 1.3](docs/requirements/03_软件需求分析说明书.md#12-需求基线与后续设计输入)、[追踪矩阵](docs/requirements/04_需求追踪矩阵.md)、[负责人决策速览](docs/requirements/00_项目需求速览与决策清单.md)。需求子目录「新建文件夹」中的五份副本当前与主文件逐一同哈希，以父目录文件为引用入口。 |
| 技术方案、接口和业务不变量 | [架构交接](docs/architecture/11_架构评审与开发交接.md)、[实施契约 1.2](docs/architecture/12_开发实施契约补充.md#1-契约入口与优先关系)及 [JSON Schema](docs/architecture/contracts/contracts.schema.json)、[Tools 定义](docs/architecture/contracts/tools.json)、[HTTP 映射](docs/architecture/contracts/http-operations.json)。 |
| 状态、用例与实际运行证据 | [progress](docs/development/progress.md)维护阶段状态和外部条件。[TC 清单](docs/development/test-cases.json)维护用例定义，[阶段报告](docs/development/reports/README.md)保留实际命令、结果和证据。 |

## 决定、差异与待核验

| 事项 | 当前口径及下一动作 |
| --- | --- |
| 需求与架构覆盖 | 现有[阶段映射](docs/development/03_模块依赖与阶段划分.md)覆盖 FR-001—FR-016。重点对照权限、9 月规则、S7/S8、独立回读、记忆失效及可选范围，未发现需要变更核心范围的冲突。架构 1.2 的既有补缺见[复审问题清单](docs/development/01_架构复审问题清单.md)，仍需软件取证。 |
| Q-004、Q-005、Q-009 | 11 月 3 日确认 DeepSeek 官方渠道和当前机器。旧架构与总计划中的「供应商未定」「设备待提供」是历史口径，按[决策速览](docs/requirements/00_项目需求速览与决策清单.md#5-待确认问题与决策清单)和 [progress 外部条件台账](docs/development/progress.md#外部条件台账)执行。首轮拟测 `deepseek-flash`，`deepseek-v4-pro` 为对照候选。D2 前后以真实工具调用 probe 确认适配协议、模型模式、可用额度和网络，性能目标留到实测后。 |
| 版本与计数 | 架构交接的 M0—M5 是历史顺序，执行用 D0—D7。导航和早期复审的 60 项属于旧计数；现有[用例清单](docs/development/test-cases.json)为 61 项，含 3 项可选，覆盖 47 项 Must AC 与 3 项可选 AC。 |
| S6/S7/S8 批准证据 | [需求依据](docs/requirements/03_软件需求分析说明书.md#11-依据与信息等级)记载已确认（[原文核验限制](docs/requirements/00_项目需求速览与决策清单.md#原文核验提示)），项目文件中的原始批准证据待核实。继续按现有范围，不据此重新缩减功能。 |
| 运行验证 | 本轮只做文档与静态核对。61 项软件用例均为 `not_run`。PG/Docker、依赖安装、真实模型工具链、启动和交付均无本轮运行证据。赛事通知与提交形式由负责人核验，缺失时保留候选交付状态。 |

## 需要负责人批准的事项

| 事项 | 执行边界 |
| --- | --- |
| [D1 命名与测试保护实施补充](docs/development/reports/D1_数据库命名变更审查与创建授权方案.md#批准后同步清单与本轮验证) | 2026-11-04 本轮明确批准四名称、harness schema、精确名单及本轮 D1/对象操作边界，见[正式批准](#d1-正式实施批准--2026-11-04)。已同步规则/架构/测试定义，真实执行因受控凭证缺失 blocked；tax_db 保护不变。 |
| [Q-007 历史证据政策](docs/requirements/00_项目需求速览与决策清单.md#5-待确认问题与决策清单) | 当前采用删除记忆后停止进入模型输入、历史证据受控保留。期限、可见范围、交付裁剪和彻底擦除待负责人决定。相关扩展在批准前暂停，基线实现可继续。涉及 FR-010/015、DR-010/011、NFR-008。 |
| [D7 可选增强](docs/development/tasks/D7_可选增强.md#前置依赖) | D6 通过后明确选择是否启用 FR-017、FR-018 或 FR-003 跨企业金额查询，当前均未纳入。 |
| 重大变更 | 本轮 D1 命名与保护方案已明确批准，见上方正式批准；当前凭证阻塞不等于撤销授权。其他 Must、权限、数据政策、核心选型或部署范围变更仍先登记来源、选项和 FR/AC/契约影响，获批准后再修改。 |

## 续记方式

每次阶段收尾或中断，追加一条简短记录，包含日期与阶段、实际完成项、决定及来源、验证结果与报告链接、未完成项或阻塞、下一动作。各阶段特有的执行、测试、验收命令、退出码、TC/AC、fixture、模型模式和脱敏证据集中留在阶段报告。开发者通用启动统一链接 [README](README.md)，启动方式变化同次更新该入口并替换失效步骤；部署、演示、恢复细节按对应阶段经实测的 runbook 维护，不复制通用开发启动步骤。

## PostgreSQL 只读连接诊断 · 2026-11-04

用户说明已配置 DATABASE_URL 后，本轮只做脱敏配置核对及只读 SQL，应用账号已成功登录 finance_tax_dev（PostgreSQL 18.6）；这更新了前次“连接字段为空”的时间点事实，不回写历史验收结果。[诊断记录](docs/development/reports/2026-11-04_PG_readonly_diagnostic.json)显示数据库 owner/编码及当前 app 角色属性符合所查预期，但 harness schema 不存在、其下无业务表；服务器地址文本为带掩码的 127.0.0.1/32，现有目标校验直接与不带掩码的主机比较，产生误拒绝，后续修复应规范化 IP 比较而不削弱实例检查。管理员候选连接启动未通过，具体原因未确定；两类测试连接仍未配置。

D1 仍 blocked，没有真实迁移/seed/grant 或业务验收通过。本轮没有修改业务代码、创建/重置数据库对象或连接 tax_db 业务库。可恢复下一动作是保留有效的应用连接，先处理校验缺陷和管理员只读诊断，再按原边界核对已存在项目对象来源及测试连接；任何对象变更仍须遵守同名对象不接管的约束，不因本次登录成功自动执行初始化。

## D1 连接校验修复恢复 · 2026-11-04

用户在应用连接已成功、地址误拒绝及初始化缺失的诊断后明确要求“继续”。本轮恢复仅 D1：修复服务器 IP 地址与配置地址的规范化比较，覆盖运行连接、管理员核验及创建来源回执比较，保留精确实例/端口、角色、owner/schema、环境及允许名单约束，不把同网段不同 IP 视为同一目标。修复和回归可独立完成；管理员/维护/测试连接及既有对象先只读核验，同名对象不自动采纳、改 owner/密码或删除重建，tax_db 不连接。

开始状态及脱敏配置见[本轮指纹](docs/development/reports/2026-11-04_D1_ip_guard/before.json)和[配置元数据](docs/development/reports/2026-11-04_D1_ip_guard/configuration-metadata.json)。应用/管理员字段已填，维护与双测试字段仍空，创建回执不存在；这不是数据库业务通过。原业务需求和机器契约不变，D2 不推进，Git 不提交/推送；实际修复、检查与剩余阻塞在本轮报告交接。

## D1 IP 校验修复交接与既有对象范围待明确 · 2026-11-04

已完成[本轮修复及报告](docs/development/reports/2026-11-04_D1_IP地址校验修复.md)，149 项单元测试 passed，真实只读应用连接确认地址格式误判修复且不同 IP/端口仍拒绝。原生 psql 进一步确认 postgres Password 认证失败；当前维护及双测试字段缺失。两个项目库/角色已存在，owner/编码及所查角色属性符合目标，app TEMP 权限过宽，开发库 harness 缺失，测试库 schema 未连接核验，创建来源回执不存在。没有数据库对象变更，D1 状态仍 blocked，详见[progress](docs/development/progress.md)。

按用户原“同名对象先只读检查报告，不擅自接管”边界，既有对象的来源/采用处理先明确。可审阅[差异与补齐顺序](docs/development/reports/2026-11-04_D1_IP地址校验修复.md#既有项目对象的差异与后续方案)：A，确认它们是操作者为本项目预建后，在原 owner/密码不变的条件下，采用受控来源记录并按测试先行补 schema/最小权限；B，由操作者按核验结果自行准备后再交接。本轮未选择或实施该来源处理，不伪造当前创建回执、不删改旧对象。潜在影响为 FR-003/004/005/013、DR-001/006/010/011、NFR-002/003/006/008 与 AC-001/002/014/032/036 的实例/权限/装载来源取证；正式业务含义、机器接口不变。若新增预建对象采用入口，先明确范围和来源记录后再同步维护/测试，不静默放宽来源保护。

可恢复下一动作：操作者仅在本机核对管理员现有口令并补 MIGRATION_DATABASE_URL、TEST_DATABASE_URL、TEST_MIGRATION_DATABASE_URL；确认既有项目对象来源及采用方式，再只读核验测试库，按批准范围准备测试库和完整真实门，通过后处理开发库。当前修复与独立检查已收尾，未提交/推送，不推进 D2。

## D1 连接配置只读复核 · 2026-11-04

用户通过配置问题的异步回复表示“已在本机配置完成，请重新检查”，本轮仅重新核验连接和目录状态。DATABASE_URL、TEST_DATABASE_URL、TEST_MIGRATION_DATABASE_URL 均已实际登录成功；根 .env 的 MIGRATION_DATABASE_URL 键存在但值为空，无进程覆盖；原生 psql 确认 postgres Password 认证仍失败。两个库均无 harness schema，app TEMP 权限仍过宽且无创建回执。结果和实际命令见[复核报告](docs/development/reports/2026-11-04_D1_连接配置复核.md)及[脱敏证据](docs/development/reports/2026-11-04_D1_connection_recheck/readonly-results.json)。

这更新了上次两类测试连接缺失的状态，不回写历史测试。既有对象来源/采用范围的前次确认问题尚未收到明确回复，本次配置确认不视作修改既有对象授权。没有初始化、迁移、seed、授权、重置或代码修改，D1 仍 blocked，不推进 D2。可恢复动作是本机补开发维护连接、核对管理员口令/编码，并明确既有对象处理范围后再按测试先行顺序准备。

## D1 既有项目对象准备恢复 · 2026-11-04

用户在已收到既有两库两角色差异、补 schema/最小权限方案及采用范围说明后，明确回复“已经修改，继续推进D1”。本轮据此按此前方案 A 继续这两个已核验的空项目库：保持既有角色密码、数据库/schema 所有者不变，记录操作者预建来源和本轮明确继续的依据，只补缺失 harness 与既定最小权限；不接管非预期对象、不删库/卷、不连接 tax_db。此后续指令覆盖之前纯文档/仅只读任务范围，D1 原业务需求与机器契约不变，D2 不推进。

[本轮只读前检](docs/development/reports/2026-11-04_D1_live/readonly-results.json)已验证五类连接实际登录、PG18.6、管理员身份、两个项目库 OID/owner/UTF8、两角色属性/无成员关系，两库 public 普通表为 0，harness 均不存在。先实现并检查显式预建对象准备入口：要求审批来源引用、准确库/角色 OID、实例、空对象集合、维护/应用连接及来源类型；不伪装成本程序新建。测试环境先处理 finance_tax_test，真实迁移/seed/grant 和完整 D1 子项通过后才准备 finance_tax_dev。所有来源/维护保护保留；任何对象/数据差异停止相关操作。

影响仍为前条已列 FR/DR/NFR/AC 的初始化来源和取证，原业务权限/生命周期承诺不变。实际执行及失败证据另存本轮目录，原 106/47、149 单测与前检记录保留为历史，不提交/推送 Git。

## D1 准备入口与独立凭证检查交接 · 2026-11-04

按上方恢复决定完成预建对象显式 PrepareExistingTest/PrepareExistingDev、审批引用、OID/实例/空对象集合校验和 prepared_databases 来源范围保护；不自动改密码/owner、不创建/删除数据库角色，tax_db 内部 override 也在连接前拒绝。单元测试改为不读操作者根 .env，完整单元集 169 passed（含先前 114 准备子集），见[本轮报告](docs/development/reports/2026-11-04_D1_真实验收恢复.md)。

五类连接已实际登录，但首次显式准备命令在 DDL 前因 app/migrator 口令相同退出 2；安全原因见[记录](docs/development/reports/2026-11-04_D1_live/preparation-blocker.json)。这项沿用已确认的独立角色口令要求，未关闭或绕过保护。未写来源回执，未创建 schema/迁移/seed/grant/重置，完整真实 PG 用例仍 blocked/not_run；D1 未完成。

已请操作者仅在本机为维护角色提供独立有效口令，同步 MIGRATION_DATABASE_URL 与 TEST_MIGRATION_DATABASE_URL，不在聊天发送秘密。既有角色密码不由本程序擅自重设。更新后先只读验证，再按已记录范围准备测试库及完整真实验收；通过后才处理开发库。当前独立工作和检查交接后停在 D1，不提交/推送，不推进 D2。

## D1 操作者选择暂缓凭证调整 · 2026-11-04

用户回复“暂不修改，先完成可独立进行的工作并交接”。据此停止依赖独立维护口令的数据库准备，不再次尝试初始化或修改角色密码。可独立工作已完成：169 项单元测试通过，文档路径/章节锚点、源码静态检查及保护输入差异核对结果见[交接检查](docs/development/reports/2026-11-04_D1_live/handoff-validation.json)；完整真实 PostgreSQL 业务门仍 blocked/not_run，D1 未完成。具体成果、失败证据和恢复顺序见[恢复报告](docs/development/reports/2026-11-04_D1_真实验收恢复.md#可恢复下一动作)。本轮交接后停止，不提交/推送，不进入 D2；待操作者自行调整实际角色口令及两个维护连接，并明确恢复后继续。

## D1 独立凭证恢复 · 2026-11-05

用户回复“我修改了密码”，据此前次 D1 恢复约定重新核验：两库 app/migrator 口令已区分，五类实际登录成功，实例/OID/owner 与前次一致，仍无 harness，未作数据库变更，见[只读证据](docs/development/reports/2026-11-05_D1_credentials/readonly-results.json)。按已批准 D1 范围恢复测试库显式准备、真实迁移/seed/权限及完整验收，通过后才准备开发库；既有密码/owner 不变，不连接 tax_db，不推进 D2、不提交推送。前次口令相同及停止记录保留为历史，不改写为通过。

## D1 真实验收完成交接 · 2026-11-05

按上述决定完成两库显式预建来源准备，测试先行：完整 216 项测试 passed、0 failed/blocked（169 单元、47 真实集成/API），之后开发库迁移/seed/授权/Inspect 全部退出 0，真实开发 app 连接的 HTTP 六项验证通过。真实执行发现并修复首迁移 JSON 默认值多余引号与授权 SQL 的驱动占位符误解析；失败、回滚和复验日志均保留，业务需求/机器契约及原始资料 hash 未变。范围、命令/退出码、fixture、SQLSTATE、seed hash 和 TC/AC 子项见[最终报告](docs/development/reports/2026-11-05_D1.md)及[最终汇总](docs/development/reports/2026-11-05_D1_credentials/final-summary.json)。

README、开发者指南、任务卡和 progress 已同步，历史 blocked 报告只增加当前结果导航，不回写旧验收。静态链接/锚点和人工追溯核对分别见[交接检查](docs/development/reports/2026-11-05_D1_credentials/handoff-validation.json)。D1 local/overall=passed，external=not_applicable；TC009/011/027/013/052 仅关闭卡内子项，后续整项及 D6 恢复未执行。当前 .env 日常演示令牌未配置，本轮 HTTP 使用临时子进程令牌且服务已停止；按根 README 本机配置即可日常使用，不需重复初始化。既有角色密码/owner 未由程序改变，tax_db 未连接/改动，未删库/容器/卷，未提交/推送 Git。本轮交接后停止，不推进 D2。
