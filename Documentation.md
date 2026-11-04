# 项目执行记录

## GitHub 上传交接 · 2026-11-03

按用户要求将现有 D0 项目整理为本地 Git 仓库，`main` 指向 `https://github.com/xiaos300/finance-tax-assistant.git`；远端查询为空仓库。已按 `.gitignore` 排除环境文件、虚拟环境、依赖和缓存，完成初始提交；本地提交身份设为 `xiaos300 <xiaos300@users.noreply.github.com>`。HTTPS 推送和 Windows 凭据管理器非交互重试均因缺少 GitHub 认证失败，SSH 也无有效公钥；**远端尚未上传**。下一动作：用户在本机完成有仓库写权限的 GitHub 登录后运行 `git push -u origin main`，再以 `git ls-remote origin refs/heads/main` 核对提交哈希。没有推进 D1 或改变 D0 验收状态。

## 当前交接 · 2026-11-03 · D0 完成后停止

用户明确授权仅实施 D0，并要求验收交接后停止。已建立 FastAPI/Pydantic 2 与 Vue 3/TypeScript/Vite/Pinia 最小工程，实际解析依赖锁并冻结安装；数据库/维护设置独立于模型，test_stub 仅 test 可配，健康接口、最小严格 DTO、错误封装和安全脚本已实现。最终验收退出 0：后端18项、Vitest 1项、typecheck/build、live=200/ready=503、源码与构建秘密扫描通过。TC061 完整 passed；TC051 仅配置子项通过，整项留 D2。详情见 [D0报告](docs/development/reports/2026-11-03_D0_baseline.md)、[progress](docs/development/progress.md)及 [启动说明](README.md)。

实施选择与来源：按 D0 卡和契约1.2保持无数据库/模型网络调用；ready 在本阶段保守返回未准备，真实准备验证留 D1。uv 0.13.7 局部安装在忽略目录，缓存显式放项目内；npm 使用 npm.cmd，脚本支持 Windows PowerShell 5.1，不更改系统执行策略。首次依赖漏洞/Node警告已通过更新测试依赖、精简依赖解决，最终 npm audit 0。Vite 默认清空已有 dist 在当前 Windows/Node 组合产生原生进程异常；Vite 7.3.7 配合校验路径和拒绝链接的逐项清理包装器已实测通过。pytest 非必要缓存关闭，避免其相对路径校验/权限问题。没有修改需求或核心选型，也没有新增业务接口。

保留的限制：psql、pwsh缺失，Docker仅CLI版本取证，PostgreSQL 18服务器/角色/迁移/seed/专属测试库均未验证；真实 DeepSeek 配置与 probe 未执行。未初始化 Git，未提交/推送；官方材料及 requirements 哈希未变。D1 入口条件为用户另行授权、读取 D1 卡与本报告、落实 PostgreSQL 18 及维护/应用/专属测试连接。下一动作仅等待审阅，不推进后续阶段。

## 准备交接 · 2026-11-03（D0授权前历史）

已盘点需求、架构、机器契约、开发任务卡和现有文件，建立根目录规则、里程碑入口与交接记录。当前没有正式前后端工程、依赖锁、迁移或运行脚本，目录也尚未初始化 Git。D0—D6 尚未开始，D7 未纳入。获开发授权后的下一步是读 D0 任务卡，探测本机运行时并开始工程基线。当前状态见 [progress](docs/development/progress.md)。

三份根文档按「规则、里程碑、交接」分工。每阶段实测后更新状态及报告，将验证结果留在工作区供下一次继续。 [OpenAI 官方文章《Run long horizon tasks with Codex》](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)

## 复用的基线

| 内容 | 维护位置 |
| --- | --- |
| 业务范围、优先级、验收及追踪 | [需求说明书](docs/requirements/03_软件需求分析说明书.md)、[追踪矩阵](docs/requirements/04_需求追踪矩阵.md)、[负责人决策速览](docs/requirements/00_项目需求速览与决策清单.md)。需求子目录「新建文件夹」中的五份副本当前与主文件逐一同哈希，以父目录文件为引用入口。 |
| 技术方案、接口和业务不变量 | [架构交接](docs/architecture/11_架构评审与开发交接.md)、[实施契约 1.2](docs/architecture/12_开发实施契约补充.md)及其三份机器契约。 |
| 状态、用例与实际运行证据 | [progress](docs/development/progress.md)维护阶段状态和外部条件。[TC 清单](docs/development/test-cases.json)维护用例定义，[阶段报告](docs/development/reports/README.md)保留实际命令、结果和证据。 |

## 决定、差异与待核验

| 事项 | 当前口径及下一动作 |
| --- | --- |
| 需求与架构覆盖 | 现有阶段映射覆盖 FR-001—FR-016。重点对照权限、9 月规则、S7/S8、独立回读、记忆失效及可选范围，未发现需要变更核心范围的冲突。架构 1.2 的既有补缺见[复审问题清单](docs/development/01_架构复审问题清单.md)，仍需软件取证。 |
| Q-004、Q-005、Q-009 | 11 月 3 日确认 DeepSeek 官方渠道和当前机器。旧架构与总计划中的「供应商未定」「设备待提供」是历史口径，按决策速览和 progress 执行。首轮拟测 `deepseek-flash`，`deepseek-v4-pro` 为对照候选。D2 前后以真实工具调用 probe 确认适配协议、模型模式、可用额度和网络，性能目标留到实测后。 |
| 版本与计数 | 架构交接的 M0—M5 是历史顺序，执行用 D0—D7。导航和早期复审的 60 项属于旧计数；现有清单为 61 项，含 3 项可选，覆盖 47 项 Must AC 与 3 项可选 AC。 |
| S6/S7/S8 批准证据 | 需求基线记载已确认，项目文件中的原始批准证据待核实。继续按现有范围，不据此重新缩减功能。 |
| 运行验证 | 本轮只做文档与静态核对。61 项软件用例均为 `not_run`。PG/Docker、依赖安装、真实模型工具链、启动和交付均无本轮运行证据。赛事通知与提交形式由负责人核验，缺失时保留候选交付状态。 |

## 需要负责人批准的事项

| 事项 | 执行边界 |
| --- | --- |
| Q-007 历史证据政策 | 当前采用删除记忆后停止进入模型输入、历史证据受控保留。期限、可见范围、交付裁剪和彻底擦除待负责人决定。相关扩展在批准前暂停，基线实现可继续。涉及 FR-010/015、DR-010/011、NFR-008。 |
| D7 可选增强 | D6 通过后明确选择是否启用 FR-017、FR-018 或 FR-003 跨企业金额查询，当前均未纳入。 |
| 重大变更 | 当前未提出需要立即批准的核心需求或架构变更。后续若改 Must、权限、数据政策、核心选型或部署范围，先记来源、选项和 FR/AC/契约影响，获批准后再修改。 |

## 续记方式

每次阶段收尾或中断，追加一条简短记录，包含日期与阶段、实际完成项、决定及来源、验证结果与报告链接、未完成项或阻塞、下一动作。运行命令、退出码、TC/AC、fixture、模型模式和脱敏证据集中留在阶段报告。未来启动和演示命令链接到经实跑的 runbook；当前命令约定见任务卡及 [AGENTS.md](AGENTS.md)。
