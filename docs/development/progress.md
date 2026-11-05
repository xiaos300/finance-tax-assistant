# 开发进度

更新日期：2026-11-05｜[需求1.3](../requirements/03_软件需求分析说明书.md#12-需求基线与后续设计输入)｜[实施契约1.2](../architecture/12_开发实施契约补充.md#1-契约入口与优先关系)｜当前阶段：**D1 已完成真实验收与交接，本轮停止；D2 未开始**。

D0 历史验收保持；2026-11-04 本轮用户[正式批准仅 D1](../../Documentation.md#d1-正式实施批准--2026-11-04)。已提供 D1 工程、规范化 seed 和验收脚本，初次结果见[D1 报告](reports/2026-11-04_D1.md)与[summary](reports/2026-11-04_D1/summary.json)。初次连接为空、149 单测及[暂缓交接](../../Documentation.md#d1-操作者选择暂缓凭证调整--2026-11-04)均为历史记录。2026-11-05 用户更新口令后，216 项测试全部通过，测试库/开发库迁移、seed、权限与 HTTP 只读检查完成，详见[最终报告](reports/2026-11-05_D1.md)。模型 none；日常演示令牌仍需操作者本机配置，本次 HTTP 使用临时子进程令牌，不影响 D1 已完成的确定性接口验收。

| 阶段 | local_status | external_status | overall_status | 当前证据/下一动作 |
| --- | --- | --- | --- | --- |
| D0 工程与配置 | passed | not_applicable | passed | [D0报告](reports/2026-11-03_D0_baseline.md)、[summary](reports/2026-11-03_D0_baseline/summary.json)：TC061完整、TC051配置子项通过；已停止 |
| D1 PostgreSQL/只读 | passed | not_applicable | passed | [最终报告](reports/2026-11-05_D1.md)：216 passed、0 failed/blocked；两库完成准备，开发库 HTTP 6 项通过，文档检查交接完成；停止 |
| D2 只读Harness/Web | not_started | not_started | not_started | 模型未配置；本地可用替身但仍须D1完成 |
| D3 受控写闭环 | not_started | not_started | not_started | 等D2本地门；真实闭环未验证 |
| D4 记忆/完整交互 | not_started | not_started | not_started | 等D3本地门 |
| D5 非功能/回归 | not_started | not_started | not_started | 等D4本地门 |
| D6 部署/交付 | not_started | not_started | not_started | 候选材料可按依赖准备；最终门需全部live/环境/通知 |
| D7 可选增强 | not_started | not_applicable | not_in_scope | FR-017/018/跨企业金额未默认纳入 |

## 外部条件台账

| ID | 状态 | 缺少证据 | 不阻断的工作 |
| --- | --- | --- | --- |
| EXT-MODEL | unverified | 已选 DeepSeek 官方渠道；拟优先验证 `deepseek-flash`，`deepseek-v4-pro` 为对照候选；账号、预算、实际连通性及工具链 probe 待验证 | D0/D1、D2—D5本地分支 |
| EXT-ENV | D1_satisfied | [最终证据](reports/2026-11-05_D1.md)：独立口令、真实 PG 两库准备和 D1 业务门通过；日常演示令牌未持久配置，本轮用临时令牌验证 HTTP | 后续日常使用按根 README 配置令牌；后续阶段环境另行核验，不自动关闭模型或部署门 |
| EXT-NOTICE | awaiting_source | 用户负责核验正式截止、入口、大小及演示载体 | 全部开发与候选交付准备 |
| EXT-POLICY | awaiting_confirmation | Q-007最终历史保留/彻底擦除要求 | 当前保守政策与删除停止未来输入 |

EXT-ENV 于 2026-11-05 按真实验收更新；其余外部决策保持 2026-11-03 口径，详见[项目需求速览与决策清单](../requirements/00_项目需求速览与决策清单.md#5-待确认问题与决策清单)。

## 测试与问题状态

- D0 当期记录：[TC061/TC051 定义](test-cases.json)及[实际子项结果](reports/2026-11-03_D0_baseline/summary.json)：TC061完整passed；TC051仅D0配置子项passed，聊天503/无伪轮留D2、整项not_run。其余59项未执行，其中TC040/041/050增强未纳入；[AC-036](../requirements/03_软件需求分析说明书.md#84-非功能及增强验收)仅工程子项取证，47项Must AC均不能据D0宣称完整通过。
- [17项复审问题](01_架构复审问题清单.md#1-实质性问题与修正)已登记；P0/P1设计处置已补，运行验证仍未执行。REV-015外部证据保持待验证。
- [D0实现报告](reports/2026-11-03_D0_baseline.md)记录18项后端测试、1项Vitest、构建、健康HTTP、秘密扫描、失败修复及交接；失败证据保留在[attempt1](reports/2026-11-03_D0_attempt1/commands.json)/[attempt2](reports/2026-11-03_D0_attempt2/commands.json)/[attempt3](reports/2026-11-03_D0_attempt3/commands.json)。
- D0 当期未初始化 Git 的历史事实保持；当前已有仓库，2026-11-04 前检未提交/推送。原需求/官方材料及工程本轮未改，见[完整性证据](reports/2026-11-04_D1_preflight/baseline-integrity.json)。

更新本文件时必须同时链接实际阶段报告和证据，记录失败/阻塞原因及下一可执行任务；状态定义以[总计划的阶段状态与切换规则](02_开发实施总计划.md#3-阶段状态与切换规则)为准。

2026-11-04 文档维护补记：仅修复引用与导航，不改变上述 2026-11-03 阶段/测试状态；本轮[文档导航验收](reports/2026-11-04_markdown_navigation.md#验证结果与边界)。后续每阶段收尾必须按[根 Markdown 引用规范](../../AGENTS.md#markdown-文档引用锚点与可追溯性规范)检查并记录。

2026-11-04 D1 前检收尾：只读检查及报告完成，D1 local/overall 仍 not_started、external=not_applicable；没有执行迁移/seed、建删重置库/容器/卷或安装系统工具。报告与下一动作见[D1 前检交接](reports/D1_开发前检查与环境准备.md#收尾验证与下一动作)，文档/范围检查见[验证记录](reports/2026-11-04_D1_preflight/review-validation.json)。等待用户正式开发授权，不推进 D2。

2026-11-04 命名审查：用户决定 finance_tax_dev / finance_tax_test 与 finance_tax_app / finance_tax_migrator，现存 tax_db 禁止改动。[方案](reports/D1_数据库命名变更审查与创建授权方案.md)建议保留 harness schema，原 harness_test_ 保护改为精确测试库允许名单且保留环境/目标/角色校验；这两项实施补充及执行待确认。只完成文档和[验证](reports/2026-11-04_D1_naming_review/review-validation.json)，未连接数据库、改配置、创建对象或开发 D1。旧前检中的旧名步骤暂停使用，local/overall 仍 not_started。

2026-11-04 正式 D1 收尾：前述前检/审查段落为批准前历史，当前以本节与表格为准。TC001/002/005/006/007 的完整真实门 blocked；TC009/011/027 确定性、TC013 读权限、TC052 PG 角色/schema 子项 blocked，整项不提前关闭，TC052 恢复子项留 D6 not_run。目标保护、金额精度、空白/月边界、DTO 和规则纯函数等无连接子项 passed，详见[逐子项](reports/2026-11-04_D1/summary.json)。[批准](../../Documentation.md#d1-正式实施批准--2026-11-04)与[交接](../../Documentation.md#d1-实施交接--2026-11-04)已记录；本轮停止，不推进 D2。

2026-11-04 文档可读性整改：仅重组[README](../../README.md)、新增[开发者指南](../开发者指南.md)并为[D1 报告](reports/2026-11-04_D1.md#非技术读者快速了解-d1)增加通俗说明，见[整改记录](reports/2026-11-04_D1_文档可读性整改.md)。本轮只做文档检查，没有重跑业务测试或数据库操作；上方阶段状态和既有测试结果保持，D1 仍 blocked，不进入 D2。

2026-11-04 D1 恢复补记：用户在只读诊断后要求继续，已修复 IPv4 /32、IPv6 /128/展开写法的精确主机比较；端口、角色、所有者、环境和精确测试目标保护均保留。原 106/47 和 55 子集记录不覆盖；本轮 149 单测（含 98 个保护子集）见[报告](reports/2026-11-04_D1_IP地址校验修复.md)，不计为完整 PG 用例通过。未初始化、迁移、装载、授权或重置，D1 未完成，不进入 D2。

2026-11-04 连接配置复核：用户表示本机配置完成后，仅重新只读核验，确认双测试登录已成功；此前缺双测试连接的段落为当期历史。当前开发维护连接仍空，管理员认证仍失败，详见[本轮复核](reports/2026-11-04_D1_连接配置复核.md)。不改历史 summary，不运行迁移/seed/grant/重置或业务测试，D1 仍 blocked，不推进 D2。

2026-11-04 D1 再次恢复：用户已修改并明确继续推进 D1，五类真实登录通过，采用前已审阅的预建对象补齐方案，决定见[执行记录](../../Documentation.md#d1-既有项目对象准备恢复--2026-11-04)。新增显式准备/来源范围保护及单元配置隔离，169 单测通过；共用口令在任何对象变更前被拒绝，未运行真实迁移/seed/grant/业务测试。原各次缺字段/认证失败和测试记录仅作历史，不回填 passed，当前仍 blocked，不推进 D2。
