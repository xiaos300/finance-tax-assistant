# D2 只读Harness与网页

版本：1.0｜初始状态：未开始（D7未纳入）。命令均为待实施后验证，当前没有业务运行通过记录。

## 阶段目标

接通统一只读模型工具循环、会话与最小网页，完成知识CLI；不给模型暴露可写工具。

## 前置依赖

D1.local=passed；可用FakeModel继续本地分支，live模型是独立external门。

## 对应需求

FR-001/002/003/004/005/012/013/014/015/016，BR-001/007/012。

## 开发任务

- 实现ModelGateway协议、单个供应商适配器占位能力边界/FakeModel、probe报告与精确wire证据；真实适配只在获得服务证据后完成。
- 实现Conversation接收/幂等/版本/行锁/独占运行，单实例锁与中断恢复骨架；范围解析、只读Dispatcher、预算及FinalPlan事实渲染。
- 实现知识导入/list/revise/disable，正文/策略/范围/证据同事务；当前检查共享规则与发票快照。
- 建凭证/欢迎单选/跳过/聊天/事实卡片/本轮状态/最小证据页；前端生成ID并保留刷新恢复指针，不持久存凭证。

## 创建或修改的主要代码文件

- backend/app/infrastructure/model/{gateway,http_adapter,capabilities,fake}.py；infrastructure/database/singleton.py
- backend/app/modules/conversation/{service,state,repository,schemas}.py；harness/{runner,scope,tools,result_guard,schemas}.py；context/{builder,budget}.py
- backend/app/modules/knowledge/service.py；evidence/{service,repository,schemas}.py；api/routers/sessions.py、evidence.py；core/redaction.py
- frontend/src/pages/{HomePage,ChatPage,TurnEvidencePage}.vue；api/{client,contracts,sessions,ledger}.ts；stores/identity.ts、sessions.ts、drafts.ts；features/conversation基础组件
- backend/tests/model_contract/test_read_loop.py、tests/api/test_turns.py、tests/integration/test_rules.py；frontend/tests/conversation.spec.ts

## 接口任务

sessions、messages、turn创建/查询/取消、evidence；typed DTO/202/错误与同ID恢复；只读工具注册，save/propose在此阶段不得可执行。

## 数据库与事务任务

原始schema上实现会话/轮/消息/事件事务，先owner/已存在ID后hash/版本；advisory单实例连接生命周期；知识修订原子。

## 必需测试

TC003/004/008/009/011/025/026/027/046/051/053；TC057本阶段只验已实现的只读/会话/健康/202子项，写和记忆子项分别等D3/D4，D5才关闭整项。使用FakeModel及真实PG，TC004/003等live分支缺账号记blocked。

## 本地验收标准

同一runner完成查询/追问/规则检查；版本/幂等与未知工具拒绝；知识CLI实际可用；网页选择/跳过/查询正常；本地用例通过。

## 真实模型或外部验收门

真实profile及native tools probe、未预置表达/组合查询通过才external=passed；否则local_passed，允许依赖本地门的D3实现。

## 阶段交付文件

只读可运行应用、CLI、真实/替身证据分开的报告、API/TS契约快照；D2阶段报告。

## 可能阻塞及处理

模型账号/端点/预算缺失只阻塞live；数据库回归失败则先修，不推进依赖该事实的写工具。

共用契约：[架构12](../../architecture/12_开发实施契约补充.md)、[测试规范](../04_测试与验收规范.md)、[状态入口](../progress.md)、[报告规范](../reports/README.md)。阶段完成须有真实命令/结果和证据，不以文件存在代替功能通过。
