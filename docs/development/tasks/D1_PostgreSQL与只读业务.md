# D1 PostgreSQL与只读业务

版本：1.0｜初始状态：未开始（D7未纳入）。命令均为待实施后验证，当前没有业务运行通过记录。

## 阶段目标

建真实PostgreSQL schema、受限角色、一次seed与确定性当前查询，为AI工具提供可信事实。

## 前置依赖

D0.local=passed；PostgreSQL 18可运行或可先准备其文件，缺PG不能关闭本地门。

## 对应需求

FR-003/004/005/013基础、DR-001—DR-011、NFR-002/003/006/008。

## 开发任务

- 实现bootstrap两角色、harness schema、Alembic初始迁移、全表/部分唯一/复合FK/JSONB/时区/列级权限及grant-runtime。
- 读取原始明细生成business/rules/manifest规范化文件，Decimal核对并一次装载；保留原始材料hash，不覆盖当前状态。
- 实现Identity/Repository、整数分/月区间/空白判定/策略纯函数、金额/明细/搜索/适用规则只读服务及HTTP。
- 完成manage.ps1初始化维护连接try/finally与退出码保护；配置专用TEST_DATABASE_URL与测试维护连接，禁止回落演示库。

## 创建或修改的主要代码文件

- deploy/postgres/init-roles.sh；backend/alembic.ini、migrations/env.py、versions/0001_initial.py
- backend/app/infrastructure/database/engine.py、models.py、unit_of_work.py；app/core/identity.py
- backend/app/modules/ledger/{policies,repository,service,schemas}.py；knowledge/{repository,policies,schemas}.py；api/routers/identity.py、ledger.py
- scripts/prepare_seed.py、reset_test_data.py、manage.ps1；data/seed/business.json、rules.json、manifest.json；backend/app/cli.py
- backend/tests/integration/test_schema.py、test_roles.py、test_seed.py、test_totals.py；tests/api/test_read_acl.py；tests/conftest.py

## 接口任务

me、invoices/search、invoice详情、totals、bank-transactions、purpose-check、rules的确定性读取；严格按http-operations的JSON/错误，原生权限拒绝无伪零。

## 数据库与事务任务

首个真实迁移覆盖所有05/12字段含scope_company_ids/last_change_origin_json；固定search_path与alembic表schema，应用账号无DDL/禁写列。

## 必需测试

TC001/002/005/006/007完整；TC009/011/027确定性子项；TC052角色/schema部分；TC013读权限部分。TC002记忆可由合法fixture直接插入，非真实模型历史。

## 本地验收标准

真实PG冻结依赖下迁移/seed/grant成功；四组金额及零记录、日期边界、seed保护、列级权限、唯一约束通过；原文件hash不变。

## 真实模型或外部验收门

无模型门；PG连接、角色与类型必须实际通过；备份恢复分支随D6补全TC052。

## 阶段交付文件

迁移与规范化seed、只读API/服务、数据库/权限测试和数据核验报告；D1阶段报告。

## 可能阻塞及处理

PG/角色初始化/容器网络不可用时记录EXT-ENV；仍可写纯policy/前端与schema，但不以模拟数据库通过集成门。

共用契约：[架构12](../../architecture/12_开发实施契约补充.md)、[测试规范](../04_测试与验收规范.md)、[状态入口](../progress.md)、[报告规范](../reports/README.md)。阶段完成须有真实命令/结果和证据，不以文件存在代替功能通过。
