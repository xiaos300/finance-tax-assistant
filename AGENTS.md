# 财税 Harness 项目开发规则

适用本目录及子目录。项目为模拟财税竞赛助手：查询当前数据、按本轮明确意愿补发票用途/备注、保存后独立回读、多轮检查及记忆/规则管理。当前为开发准备完成状态，尚无正式前后端工程；复审指令本身不等于要求立即编码。

## 开始工作

1. 先读[开发导航](docs/development/00_开发导航.md)、[Plan.md](Plan.md)和[Documentation.md](Documentation.md)，确认授权范围、阶段依赖和最近决策。
2. 读[progress](docs/development/progress.md)、当前阶段任务卡和前一阶段报告，确认本地门、外部门、已运行验证和下一动作。
3. 读[需求说明书](docs/requirements/03_软件需求分析说明书.md)、[追踪矩阵](docs/requirements/04_需求追踪矩阵.md)、相关架构章节及[实施契约](docs/architecture/12_开发实施契约补充.md)。接口按 schema、工具和 HTTP 映射执行。碰到矛盾时，区分正式需求、实施补充及历史记录，定位到编号和来源后再处理。

用户授权开发后从D0开始；持续开发授权内完成当前本地门再推进依赖就绪的任务，不为常规实现选择重复询问。外部账号、设备、赛事通知缺失单独记录，继续不依赖它们的工作。阶段状态/真实模型门规则见[总计划](docs/development/02_开发实施总计划.md)。不要把仅替身通过称为真实AI验收完成。

## 不得擅自改变的架构和业务

- Vue 3/TypeScript/Vite/Pinia；FastAPI/Pydantic 2；PostgreSQL 18、SQLAlchemy 2.0同步Session+psycopg 3、Alembic；HTTPX模型适配；Compose app+db。开发、集成测试、演示使用PostgreSQL。
- 模块化单体、单应用进程；无新增Redis、队列、向量库、Agent框架或微服务。已选 DeepSeek 官方渠道，适配器按 ModelGateway 契约接入，真实能力以 probe 和 live 证据为准。
- 模型理解/选工具，程序验身份/权限/参数、算金额、执行/回读；不以关键词场景脚本或预存预期替代模型。
- U001读写甲乙合法字段；U002只读甲。企业+业务编号复合键；银行只读；发票只写purpose/note，金额BIGINT分/API元字符串。
- 仅2026-09用途检查：甲全票必填、乙≥1000元；空白算未填，备注不替代用途。8月可查金额，不做历史用途规则恢复。
- 可空默认企业、实际操作企业、权限与任务归属分开；选择/跳过/切清/引用/恢复均不是写授权。明确乙请求不自动改默认甲。
- 当前轮意图→稳定操作账本/CAS→提交后新Session回读；未知提交不盲重写。新会话不复用旧授权；删除记忆停止未来输入，不能回滚票据或承诺历史完全擦除。
- 16项Must及已确认S7/S8网页交互必须完整；FR-017/018与跨企业金额Should仅D7明确选择后实施，不增加跨企业批量写或真实财税接口。

## 代码与数据边界

Router→Service→Repository；纯规则不含I/O；模块间DTO/TransactionPort，不传FastAPI Request/ORM Session到模型或Router。Evidence为叶子，Memory不反调Ledger；ConversationStatePort不回调runner。模型/正文不能执行SQL、shell或任意URL。

目录按[09](docs/architecture/09_工程目录结构设计.md)与任务卡随实际功能创建，不批量建空占位文件。规范DTO放backend/app/core/contracts.py并与JSON Schema回归；runtime工具注册表是tools.json契约的实现。供应商字段留在适配器，wire正文由Gateway发送前记录，秘密与鉴权头不入正文/证据。

官方docx/xlsx、五份requirements为保护输入；需要改需求必须记录来源和影响，不为方便实现静默缩范围。正常启动不seed；迁移/seed/grant-runtime需维护角色，常驻app无DDL/超级用户凭证。测试仅harness_test_专属库且不等于演示连接目标，禁止测试夹具回落DATABASE_URL。

涉及 Must、业务权限、写入授权、数据生命周期、公开部署、核心选型或 D7 范围的变更，先在 Documentation 登记待批准项，列出来源、选项、受影响的 FR/DR/NFR/AC、契约及验收影响。暂停受影响实施，继续已授权且无依赖的工作。获得明确批准后记录日期和依据，再同步需求、追踪、架构契约、测试及计划中受影响的条目。

已有用户改动不覆盖；动手前查看目录和可用Git状态。当前不是Git仓库，记录事实，不为本轮文档任务擅自初始化。Git提交/推送遵循当前用户授权；禁止丢弃用户改动、force push、reset --hard或无必要删除。数据库/卷/备份重置必须校验明确目标，不能用删除pg_data或down -v当正常重启。

## 测试与阶段报告

按[test-cases.json](docs/development/test-cases.json)实施可执行测试，保留case_id/AC映射、fixture、模型模式、运行证据。测试替身仅APP_ENV=test；真实分支缺账号写blocked。提交/回读故障用真实PG和显式屏障，不能用同Session缓存或外层回滚替代真实提交。运行适合改动的检查；通过后无新问题不反复扩大测试。

每阶段创建reports下报告，更新progress的local/external/overall；失败、未运行、未纳入分别标识。报告要包含改动/契约版本、实际命令/退出码、测试子项、数据/模型模式、证据路径、剩余风险和下一动作；禁止把计划/安装成功当业务通过。报告不含密钥、数据库密码/完整URL或无关个人内容。

每个里程碑按「确认范围 → 实施 → 运行检查 → 修复并复验 → 记录交接」推进。检查失败时保留失败证据并修复，外部条件缺失时标记对应分支 blocked。阶段收尾或中断前，在 Documentation 记录决定、变化和可恢复的下一动作，阶段状态与详细输出分别链接 progress 和报告。

## 启动与测试命令

以下为**待创建工程后的命令约定，本轮未验证应用运行**。D0首次生成锁需实际解析依赖并记录，锁存在后才运行冻结命令。数据库与模型环境由操作者受控提供，不把密码写入命令历史。

```text
# backend目录
uv sync --frozen --group dev --group prepare
uv run --frozen --no-sync pytest tests/unit
uv run --frozen --no-sync pytest tests/integration tests/api
uv run --frozen --no-sync pytest tests/model_contract -m live
uv run --frozen --no-sync uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1

# frontend目录
npm ci
npm run typecheck
npm run test -- --run
npm run build
npm run dev

# 根目录，D1后才有维护封装；D4后才有根E2E工程
pwsh -File scripts/manage.ps1 -Action Init
npm run test:e2e
docker compose up -d --wait db
docker compose up -d app
```

live测试需ALLOW_REAL_MODEL_TESTS=true和已通过probe的profile。无模型可MODEL_MODE=disabled做只读诊断，不能冒充AI成功；seed/迁移只加载数据库配置。实际部署、恢复、依赖和阶段验收命令以已实现runbook与报告更新，遇到不可行处修订对应设计/契约并记录原因。
