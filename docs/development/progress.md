# 开发进度

更新日期：2026-11-03｜需求1.3｜实施契约1.2｜当前阶段：**D0 已完成并停止，等待用户审阅；D1 未授权**。

本轮按用户授权完成 D0 工程与配置基线及实际验收，未实施 D1 数据库业务或模型调用。原设计复审和数据离线复算不计作业务验收。

| 阶段 | local_status | external_status | overall_status | 当前证据/下一动作 |
| --- | --- | --- | --- | --- |
| D0 工程与配置 | passed | not_applicable | passed | [D0报告](reports/2026-11-03_D0_baseline.md)、[summary](reports/2026-11-03_D0_baseline/summary.json)：TC061完整、TC051配置子项通过；已停止 |
| D1 PostgreSQL/只读 | not_started | not_applicable | not_started | D0本地门已通过；需用户另行授权及真实PostgreSQL 18专属测试环境 |
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
| EXT-ENV | partially_observed | 已实测Python 3.13.9、Node 24.8.0、npm 11.6.0、局部uv 0.13.7、PowerShell 5.1和Docker CLI 29.5.2；冻结安装/前端构建通过。psql、pwsh缺失；Docker server/PostgreSQL 18/镜像尚未验证 | D0已完成；Windows PowerShell可运行D0脚本。D1需真实PG和维护/测试连接，不能以CLI版本通过集成门 |
| EXT-NOTICE | awaiting_source | 用户负责核验正式截止、入口、大小及演示载体 | 全部开发与候选交付准备 |
| EXT-POLICY | awaiting_confirmation | Q-007最终历史保留/彻底擦除要求 | 当前保守政策与删除停止未来输入 |

外部条件台账于 2026-11-03 同步，详见[项目需求速览与决策清单](../requirements/00_项目需求速览与决策清单.md)。

## 测试与问题状态

- TC061完整passed；TC051仅D0配置子项passed，聊天503/无伪轮留D2、整项not_run。其余59项未执行，其中TC040/041/050增强未纳入；AC-036仅工程子项取证，47项Must AC均不能据D0宣称完整通过。
- 17项复审问题已登记；P0/P1设计处置已补，运行验证仍未执行。REV-015外部证据保持待验证。
- [D0实现报告](reports/2026-11-03_D0_baseline.md)记录18项后端测试、1项Vitest、构建、健康HTTP、秘密扫描、失败修复及交接；失败证据保留在D0_attempt1/2/3。
- 原需求/官方材料不修改；当前不是Git仓库，未执行git init/commit。

更新本文件时必须同时链接实际阶段报告和证据，记录失败/阻塞原因及下一可执行任务；状态定义以[总计划](02_开发实施总计划.md)为准。
