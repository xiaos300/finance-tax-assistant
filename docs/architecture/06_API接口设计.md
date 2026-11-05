# API接口设计

版本：1.2｜日期：2026-11-01｜契约依据：[模块](04_模块与分层架构设计.md)、[PostgreSQL数据模型](05_数据库与数据架构设计.md)。D1 确定性只读接口已有代码，真实 PostgreSQL 运行仍待验收，见[D1 报告](../development/reports/2026-11-04_D1.md)；其他接口仍为后续阶段设计。示例ID和文本只表达结构。HTTP DTO与逐工具完整参数/返回以[实施补充](12_开发实施契约补充.md)及其contracts目录为编码依据；下文保留业务说明和示例。

## 1. HTTP通用契约

- 基路径`/api/v1`，资源小写复数、连字符连接。除`GET /health/live`与`GET /health/ready`外均需`Authorization: Bearer <演示凭证>`；身份从服务端映射。CLI不经过这些HTTP接口。
- 所有会话资源必须session.user_id等于可信用户；所有企业资源执行时require_company(read/write)。模型和客户端无可覆盖的user_id/can_write字段。
- JSON UTF-8；Pydantic `extra='forbid'`，拒绝未知字段。金额为元字符串如`"1000.00"`，日期`2026-09-01`，业务月`2026-09`，时间UTC RFC3339如`2026-11-01T02:00:00Z`，前端可显示北京时间。
- 所有成功响应为`{"data": ..., "request_id":"..."}`；错误统一见下。ID按字符串，不把F002转数值。未提交修改字段保持原值；purpose/note明确null表示清空，不与省略混同。
- 分页列表统一`{items:[],next_cursor:null}`，limit默认20、最大100是可配置工程初值；cursor为不透明稳定排序键，非法/不匹配过滤器返回422。新发票搜索变化需重新搜索，不承诺跨写入快照分页。
- GET无业务写副作用。HTTP调用超时不能推断业务失败。除安全GET外fetch不自动重试；重复发送轮次必须复用client_turn_id与同一payload。
- MVP无文件上传接口、无发票直接PATCH、无银行写接口、无权限管理或知识写HTTP接口。消息引用只传复合键；规则管理为CLI，证据查看是JSON，可人工保存必要记录。

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "当前身份无权执行此操作",
    "details": {},
    "retryable": false,
    "turn_id": null
  },
  "request_id": "req-example"
}
```

| HTTP码 | 统一用途/主要code | 客户端处理 |
| --- | --- | --- |
| 200 | 查询、更新、删除确认，幂等重放终态 | 按data事实展示 |
| 201 | 新会话；新轮正常执行到终态（可含业务部分完成） | 保存ID与结果 |
| 202 | 已运行轮的重复POST、取消请求已登记 | 仅查询原轮，不能再启动 |
| 400 | 非法JSON语法 | 更正请求 |
| 401 | UNAUTHENTICATED | 清凭证，重新输入 |
| 403 | FORBIDDEN | 不展示受限企业信息 |
| 404 | RESOURCE_NOT_FOUND/SESSION_NOT_FOUND/MEMORY_NOT_FOUND | 无权限查看的他人资源同样返回404，避免枚举 |
| 409 | IDEMPOTENCY_CONFLICT/TURN_IN_PROGRESS/SESSION_VERSION_CONFLICT/MEMORY_VERSION_CONFLICT/STALE_DATA/TASK_CONFLICT | 保留草稿，查最新状态；需要时澄清 |
| 413 | REQUEST_TOO_LARGE | 提示拆分消息/引用，不能截断后默默写 |
| 422 | VALIDATION_ERROR/INVALID_MONTH/ILLEGAL_FIELD | 字段级错误；不进入业务执行 |
| 429 | BUSY | 全局模型并发名额已用，未接收新轮；提示稍后原样重试 |
| 500/503 | STORAGE_UNAVAILABLE/EVIDENCE_UNAVAILABLE/NOT_READY/MODEL_NOT_CONFIGURED | 不显示零值/成功；如有turn_id先查询；disabled模式不创建虚假执行轮 |
| 502/504 | MODEL_UNAVAILABLE/MODEL_PROTOCOL_ERROR/MODEL_TIMEOUT | 如已接收轮则附turn_id，取结构化结果；不重放业务写 |

可正常回答的“缺少信息/规则缺失/不支持8月检查”作为结构化业务结果，不必全部变为服务器故障。代码与SQL错误详情只记受控运维日志，API不回传堆栈/凭证。

## 2. 身份、会话与范围

以下接口全部默认需要上述Bearer。`expected_version`表示目标资源row_version；`session_version`是提交时会话版本。所有非GET都记录request_id，写后可查实际结果。

| 名称/方法路径 | 模块/需求 | 输入与输出 | 特有错误/幂等 |
| --- | --- | --- | --- |
| GET `/me` | Identity；FR-001、NFR-002 | 无参数→user_id/name、授权companies[{company_id,name,can_write}] | 401；不返回无权企业 |
| GET `/sessions` | Conversation；FR-001/011 | cursor/limit→本人会话摘要分页 | 401/422；重复只读 |
| POST `/sessions` | Conversation；FR-001/011 | `{default_company_id:null或C001,scope_action:"skip"或"select"}`→session_id/default_company_id/row_version、可见任务提示/偏好建议 | 403/422；select必须非空、skip必须null。新建不恢复执行或写数据 |
| GET `/sessions/{session_id}` | Conversation；FR-001 | →默认企业、row_version、result_focus、active_turn_id | 404；所有权校验 |
| PATCH `/sessions/{session_id}/default-company` | Conversation；FR-001 | `{company_id:null或C002,expected_version:1}`→新默认和版本 | 403/409；相同值无有效修改；已有运行轮返回409，避免并行切换 |
| GET `/sessions/{session_id}/messages` | Conversation；FR-002/004 | cursor/limit→message_id/turn_id/role/content/invoice_references/created_at | 404/422；历史引用标为历史标签 |

新会话响应示意：

同轮内的明确自然语言切换可由ConversationStatePort带当前turn_id更新版本；上表PATCH拒绝的是另一并发界面请求，不拒绝本轮已经验证的切换指令。set_default_company不再回调submit_turn。

```json
{
  "data": {
    "session_id": "11111111-1111-4111-8111-111111111111",
    "default_company_id": null,
    "row_version": 1,
    "task_hints": [],
    "preferred_company_suggestion": "C001"
  },
  "request_id": "req-session"
}
```

default_company_id仍为空；偏好建议只在用户有权企业内显示，不自动替代跳过。任务提示只返回本用户匹配范围的task_id/月份/目标摘要，无自动续办。自然语言“切换到乙”由同一Harness调用内部set_default_company，返回结果中的session_state使顶部同步，不绕过版本/权限验证。

## 3. 对话轮执行与连接恢复

### 3.1 POST `/sessions/{session_id}/turns`

模块Conversation/Harness；FR-002—FR-011、FR-013—FR-016；NFR-003/007/009。可信身份与会话所有权必须匹配，引用逐条read校验，写权限在实际写工具再次检查。

```json
{
  "client_turn_id": "22222222-2222-4222-8222-222222222222",
  "session_version": 1,
  "text": "把这张用途填为客户资料打印",
  "invoice_references": [
    {"company_id": "C002", "invoice_id": "F002"}
  ]
}
```

文字可为空但此时必须有至少一引用；只发引用不会修改业务。引用复合去重，客户端附带用途/金额/身份等未知字段直接422。多票内容对应不清或文字甲引用乙时返回needs_input且无写入；同一企业多票明确相同内容可逐项处理；跨企业写集合要求拆分，不新增跨企业批量修改。

首次请求接收后立即持久化running轮与user消息，请求内执行模型循环；正常终态返回201。相同client_turn_id和request_hash：原轮running→202及状态URL；终态→200原结果；不同payload→409。不生成第二个轮/消息/操作。先查已有ID再比较新的会话版本，避免已完成轮因session_version变化无法恢复。一个会话已有其他running轮则409；全局忙碌在新轮接收前429。

终态TurnResult示例（假定用户已对C002/F002明确授权，默认企业原为C001）：

```json
{
  "data": {
    "turn_id": "22222222-2222-4222-8222-222222222222",
    "status": "completed",
    "outcome": "answered",
    "answer": "乙企业F002用途已保存并回读核实为“客户资料打印”。",
    "session_state": {"default_company_id": "C001", "row_version": 2},
    "scope": {"company_id": "C002", "business_month": "2026-09", "source": "invoice_reference"},
    "facts": [],
    "writes": [
      {
        "operation_id": "33333333-3333-4333-8333-333333333333",
        "company_id": "C002",
        "invoice_id": "F002",
        "state": "verified",
        "actual": {"purpose": "客户资料打印"},
        "verified_at": "2026-11-01T02:00:01Z",
        "error_code": null
      }
    ],
    "rule_refs": [],
    "remaining": null,
    "error": null,
    "evidence_url": "/api/v1/sessions/11111111-1111-4111-8111-111111111111/turns/22222222-2222-4222-8222-222222222222/evidence"
  },
  "request_id": "req-turn"
}
```

单票保存若没有整月继续检查目标，remaining可null，不臆造整月完成。business_month只在可从该票或有效上下文明确时填写；其他请求可null。scope字段未解析时整体可null。result_focus更新可能使会话row_version递增，但default_company_id不变。

`status`统一running/completed/failed/interrupted/cancelled；`outcome`为answered/needs_input/partial/failed/cancelled，running时为null。needs_input是正常完成一次追问，不代表轮仍占运行名额。write状态与任务状态不同，见05。

模型/存储异常发生在接收后：返回502/504/503错误和turn_id，尽力持久化failed结果；如票据已保存，把事实卡片保存在result_json，不因最终文本失败丢失成功写事实。客户端查询轮可看到partial结果或待核验；崩溃导致无法记终态则下次启动置interrupted。

### 3.2 查询和取消

| 方法路径 | 模块/需求 | 请求/响应 | 错误与重复处理 |
| --- | --- | --- | --- |
| GET `/sessions/{session_id}/turns/{turn_id}` | Conversation；FR-007/015 | 无body→TurnResult或running状态，running时answer/result为空，附cancel_requested | 404/503；只查询，不重启执行 |
| POST `/sessions/{session_id}/turns/{turn_id}/cancel` | Conversation/Harness；NFR-003工程机制 | 无body→cancel_requested、当前status、已知writes；running返回202，终态返回200 | 重复幂等；不撤销已提交写入，不把取消等同回滚 |
| GET `/write-operations/{operation_id}` | Ledger；FR-007 | 无body→原用户本人操作的state/目标/actual/error_code | 404/403/503；仅查账本，不能触发再次写入 |
| GET `/sessions/{session_id}/turns/{turn_id}/evidence` | Evidence；FR-015 | cursor/limit→EvidencePage，关联模型、规则、记忆、工具和回读 | 所有权及全部scope校验；404/403，未授权不泄露payload |

取消检查点：每次模型返回后、每个工具前、写事务提交前。正在提交的单票事务允许原子结束，随后回读并说明已提交结果，不承诺撤销。浏览器Abort只中断观察；有意取消必须调用上述端点。GET恢复轮询初始1秒，退避至3秒，终态/退出/401停止；这些是工程默认值而非响应SLA。原轮超时也不可用新UUID盲重试写入。

## 4. 当前数据查询与引用搜索

| 方法路径 | 模块/需求 | 参数及返回字段 | 错误/权限 |
| --- | --- | --- | --- |
| GET `/invoices/search` | Ledger；FR-004 | q可空，company_id/business_month可选，cursor/limit→企业/票号/日期/金额/销售方/项目/row_version | 默认在全部授权企业搜索，未选默认不阻塞；显式受限企业403；失败不返回空列表 |
| GET `/companies/{company_id}/invoices/{invoice_id}` | Ledger；FR-004 | →InvoiceDetail完整已定义字段，amount为元字符串 | read；找不到404，无权403，不信搜索快照 |
| GET `/companies/{company_id}/bank-transactions` | Ledger；FR-004 | business_month必填、cursor/limit→流水明细 | read；422/403/503；无新增/编辑/删除 |
| GET `/companies/{company_id}/totals` | Ledger；FR-003/013 | business_month必填，metrics可选逗号枚举invoice_total/bank_expense/bank_income→各金额/计数、口径、rule_refs | read；成功无记录0.00并empty=true；规则不足可返回事实但标依据不足，不捏造引用 |
| GET `/companies/{company_id}/purpose-check` | Ledger/Knowledge；FR-005/013 | business_month必填→check_status/missing/count/rule_refs | read；非2026-09返回unsupported，缺规则insufficient_rules，冲突rule_conflict，均不返回合规清单 |
| GET `/companies/{company_id}/rules` | Knowledge；FR-013 | business_month/topic必填→resolution_status和匹配规则名称/版本/revision/正文/范围 | read；missing/conflict正常业务状态，停用版不作为适用依据；管理查看停用版用CLI |

search的省略企业表示授权范围内候选搜索，不表示用户已请求所有企业业务统计。q按票号/销售方/项目匹配，不查外部网站；选中只改草稿。响应示例：

```json
{
  "data": {
    "items": [
      {"company_id": "C001", "company_name": "甲企业", "invoice_id": "F002", "invoice_date": "2026-09-02", "amount": "1000.00", "seller": "示例销售方", "item_name": "示例票面项目", "row_version": 1}
    ],
    "next_cursor": null
  },
  "request_id": "req-search"
}
```

上例日期/销售方/金额用于表达字段，不作为官方F002记录值或测试预期。真实响应必须从当前库读取。

金额成功示例（初始C001/2026-09）：

```json
{
  "data": {
    "company_id": "C001", "business_month": "2026-09", "currency": "CNY",
    "invoice_total": {"amount": "9622.06", "record_count": 10, "empty": false},
    "bank_expense": {"amount": "7180.74", "record_count": 8, "empty": false},
    "bank_income": {"amount": "13000.50", "record_count": 4, "empty": false},
    "basis_status": "resolved",
    "rule_refs": [{"rule_id": "R001", "name": "金额统计说明", "version": "1.0", "revision": 1}]
  },
  "request_id": "req-totals"
}
```

purpose-check成功时`check_status="checked"`，missing为[{company_id,invoice_id,amount,purpose,note}]，count为条数，附规则RuleRef和queried_at。资料不足/冲突/不支持时missing与count均null，不能用空数组表示全部已填。查询故障HTTP503，无data伪零。无目的检查缺项不等同真实财税“合规”，答复限定模拟填写规则。

## 5. 记忆管理接口

所有接口只操作本人且仍有read权限的企业；U002虽不能写发票，仍可管理自己的C001记忆。更正或删除记忆不授权业务写入。创建任务与偏好通过Harness工具，使明确意愿可关联当前turn_id；网页提供查看、更正、删除即可，不新增管理后台。

| 方法路径 | 模块/需求 | 请求及响应 | 错误/幂等 |
| --- | --- | --- | --- |
| GET `/companies/{company_id}/memories` | Memory；FR-008—FR-011 | kind可选、cursor/limit→MemoryPage：items含kind区分Task/Preference、next_cursor、memory_revision | 403/503；企业明确，不要求默认企业 |
| PATCH `/companies/{company_id}/tasks/{task_id}` | Memory；FR-010 | `{expected_version,goal?,business_month?,status?}`→MemoryWriteResult(item为当前Task、deleted=false、memory_revision) | 404/409/422；status仅active/awaiting_input/completed/cancelled，verify_pending不可由用户直接伪造；归属不可改 |
| DELETE `/companies/{company_id}/tasks/{task_id}` | Memory；FR-010 | query expected_version必填→`{deleted:true,memory_revision}` | 已删除返回404，不再变更revision；旧版本409；前端确认删除语义但不添加业务审批 |
| PATCH `/companies/{company_id}/preferences/{preference_id}` | Memory；FR-009/010 | `{expected_version,content}`→MemoryWriteResult(item为当前Preference、deleted=false、memory_revision) | key/company/user不可改；冲突409；更正default_company内容不能跨归属企业 |
| DELETE `/companies/{company_id}/preferences/{preference_id}` | Memory；FR-010 | expected_version必填→`{deleted:true,memory_revision}` | 404/409；后续Context不再使用旧偏好 |

Task公开字段：task_id/company_id/goal/business_month/status/progress/row_version/updated_at。Preference公开字段：preference_id/company_id/preference_key/content/row_version/updated_at。API层将progress_json映射progress，不混用“曾完成数量”和当前缺填计数。

所有任务更正使用同一状态机：有关联待核验操作时，不能把status直接更正为completed来冒充核验成功，应先核验或明确取消跟踪；取消/删除记忆也不改变原操作账本。用户修订goal/月后，progress里的旧当前清单失效，重新读取才能给新结论。直接PATCH只管理记忆，不能触发票据写入。

## 6. 模型工具契约（内部函数，不是HTTP端点）

每个调用由ModelGateway转成`{call_id,name,arguments}`，Dispatcher在本轮ExecutionContext内执行。统一结果`{ok,code,data,rule_refs,operation_id}`；工具未知/非法schema拒绝。模型不提供user_id、token、数据库连接目标/凭证或SQL。工具名称在源代码注册表唯一。

| 工具名 | 主要参数 | 输出/前置条件 | 需求 |
| --- | --- | --- | --- |
| resolve_scope | company候选、month、source、source_message_id、引用键、当前文本证据位置 | 程序验证ResolvedScope或needs_input，不等于写授权 | FR-001/002/014 |
| get_totals | company_id,business_month,metrics | 同HTTP汇总，read | FR-003 |
| find_invoices / get_invoice | q/可选企业月，或复合键 | 当前候选/明细，read | FR-004 |
| list_bank_transactions | company_id,business_month,cursor | 当前明细，read | FR-004 |
| get_rules / check_purpose | company_id,business_month,topic（仅get_rules） | RuleResolution/CheckResult，read | FR-005/013 |
| propose_invoice_edit | company_id,invoice_id,changes,action_evidence,content_evidence或explicit_clear | 先验证当前消息意图、内容与对象，再由服务端构造CurrentTurnEditIntent；冲突追问 | FR-006 |
| save_invoice_fields | intent_handle（服务端本轮短期句柄） | apply_edit+独立回读WriteResult；handle仅本轮有效，执行时write校验 | FR-006/007 |
| verify_write | operation_id | 只重新查原操作及当前值，不重写；所有权/read校验 | FR-007；不实现FR-017自动续跑 |
| get_memories / remember_task / remember_preference | 已明确company_id，目标/月或偏好内容与当前明确意愿证据 | 本人记忆；冲突澄清 | FR-008/009/011 |
| correct_memory / delete_memory | kind,id,company_id,expected_version,更正值或删除意图 | 新记忆/删除及revision；不能修改发票 | FR-010 |
| set_default_company | company_id或null，明确切换/清除意图位置 | 状态端口更新session并记录事件，失败不伪报 | FR-001 |

intent_handle只用于本进程本轮关联，不是安全凭证；可在实际模型输入证据中记录opaque标识，但必须绑定当前user/session/turn/目标/内容/revision/期限，历史标识不能重放授权。参数与完整返回schema见contracts/tools.json。工具循环若模型多次请求同票不同内容，不直接第二次写，要求澄清/新轮明确更正；同票同内容复用同操作。新版本规则与当前数据在实际检查/执行时重新取，不信搜索或记忆快照。

## 7. 本机CLI能力契约

命令为下一阶段建议实现，当前未创建可运行CLI。知识CLI由持有维护账号的本机操作者执行，不接受普通聊天触发；连接从受控环境 MIGRATION_DATABASE_URL 读取，维护命令使用finance_tax_migrator，Web使用finance_tax_app。操作者核对脱敏的host/port/dbname，记录actor=operator、来源与差异；不在命令行参数或日志中传明文数据库密码。

```text
python -m app.cli seed --business data/seed/business.json --rules data/seed/rules.json
python -m app.cli rules import <rules.json>
python -m app.cli rules list [--include-disabled]
python -m app.cli rules revise R002 2.0 --file <revision.json> --expected-revision 1
python -m app.cli rules disable R002 2.0 --expected-revision 2
python -m app.cli inspect
python -m app.cli backup --output <backup.dump>
python -m app.cli restore --input <backup.dump>
python -m app.cli grant-runtime
python -m app.cli probe-model
python -m app.cli create-demo-tokens
```

import重复同hash幂等，相异同版本冲突；revise/disable的expected_revision防覆盖；失败明确非零退出码且不得部分导入。规则故障试验先配置独立测试数据库连接。backup/restore封装pg_dump/pg_restore，数据库URL中的SQLAlchemy驱动名先转换为原生libpq连接参数，密码通过受控子进程环境或受保护passfile提供，不原样传`postgresql+psycopg`给命令行工具；restore仅允许运维明确选择的新建空库且不得等于正在服务的演示目标，恢复后校验schema/数据并重新授权。create-demo-tokens只在显式命令执行时向操作者输出新凭证，不由服务器启动日志自动输出，不生成在提交包中的凭证文件。没有业务Excel导入HTTP入口。

grant-runtime仅限维护账号，按05固定白名单幂等设置运行角色权限；首次迁移与逻辑备份恢复后执行，不接受模型/客户端提交任意GRANT或角色名。

## 8. 健康接口

GET `/health/live`公开返回`data.status="alive"`，只反映进程；GET `/health/ready`检查数据库可读、schema与seed标记、静态包和配置，成功200/失败503，均采用通用响应封装。只给安全检查项名称及布尔值，不返回数据库绝对路径、用户/权限或凭证。模型可达性由显式CLI probe处理，health不付费调用模型。模块为基础设施/Router，关联NFR-006/009，无业务写入。

2026-11-04 D1 部署命名与测试保护补充已获批准，完整边界见[本轮批准记录](../../Documentation.md#d1-正式实施批准--2026-11-04)。本节名称调整不变更正式业务需求或机器接口。
