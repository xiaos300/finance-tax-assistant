# 财税 Harness · 项目与使用入口

第一次接触项目，先读第 1～4 节了解“做什么、做到哪里”；准备运行时读第 5～10 节。想理解代码为什么这样组织，再读[开发者指南](docs/开发者指南.md)。

**当前结论：D0、D1 已通过各自阶段验收；D1 已完成真实 PostgreSQL 测试及开发库准备。** 2026-11-05 完整测试 216 passed、0 failed、0 blocked，开发库 HTTP 只读检查通过，见[D1 最终交接报告](docs/development/reports/2026-11-05_D1.md)。本轮停止，不进入 D2。[当前进度](docs/development/progress.md)是阶段状态的统一入口。

## 1. 项目简介

这是一个面向模拟财税竞赛的助手项目。最终目标是让用户用自然语言查询发票和银行流水、检查发票用途是否缺失，并在用户本轮明确要求且有权限时，补充发票用途或备注，保存后重新读取核对。它还需要支持规则资料、任务记忆和执行记录。

Harness 指连接模型与程序工具的运行程序：模型负责理解问题和选择工具，程序负责检查权限、计算金额和访问数据库。这里处理的是比赛模拟资料，不执行真实记账、付款或税务申报。完整业务范围见[需求说明](docs/requirements/03_软件需求分析说明书.md#2-赛题目标评分与交付约束)。

**现在能看到的是工程准备网页和已提供代码的只读接口；聊天、模型工具循环与受控写入还没有开放。** 发票只能修改用途和备注的业务边界不变，银行资料始终只读。

## 2. 当前开发状态

| 阶段 | 通俗目标 | 当前状态 |
| --- | --- | --- |
| D0 工程与配置 | 搭好前后端工程、依赖和基本健康检查 | passed，已通过当期验收 |
| D1 数据库与只读业务 | 建立数据库基础，查询当前数据、金额和用途规则 | passed；真实测试及开发库准备、只读验证完成 |
| D2 只读 Harness 与网页 | 接入模型，完成统一的只读对话流程与网页 | not_started，未开始 |
| D3 受控写入 | 按当前明确要求保存并独立回读 | not_started |
| D4 记忆与完整交互 | 管理任务、偏好、引用和会话范围 | not_started |
| D5 回归与非功能验证 | 验证安全、并发、预算及完整功能 | not_started |
| D6 部署与交付 | 验证部署、备份恢复和演示交付 | not_started |
| D7 可选增强 | 另行选择的增强功能 | not_in_scope，未纳入 |

历史 D1 检查中，106 项不需要数据库的测试通过，47 项依赖真实 PostgreSQL 的集成/API 测试因缺连接凭证而跳过，并在阶段汇总中记为 blocked。**这不是“全部测试通过”。** 代码存在、静态检查通过、无数据库测试通过、真实数据库测试通过和阶段最终验收通过，是五件不同的事。具体依据见[D1 通俗说明及原始报告](docs/development/reports/2026-11-04_D1.md#非技术读者快速了解-d1)和[历史测试汇总](docs/development/reports/2026-11-04_D1/summary.json)。历史结果不回写；2026-11-05 的实际重跑结果另存于[本轮汇总](docs/development/reports/2026-11-05_D1_credentials/summary.json)。

最新[最终交接记录](docs/development/reports/2026-11-05_D1.md)：独立口令条件已满足，两个预建项目库按批准范围完成准备；169 项单元测试与 47 项真实集成/API 测试合计 216 项通过。历史[恢复记录](docs/development/reports/2026-11-04_D1_真实验收恢复.md)中的共用口令拒绝以及此前[149 单测/连接修复](docs/development/reports/2026-11-04_D1_IP地址校验修复.md)及[连接字段复核](docs/development/reports/2026-11-04_D1_连接配置复核.md)均保留为历史。

## 3. 项目技术栈

| 技术 | 在项目中的作用 |
| --- | --- |
| Vue 3、TypeScript | 编写网页及带类型检查的前端代码；当前页面仍是准备页 |
| Vite、Pinia | Vite 提供前端开发服务器和构建；Pinia 是已选的前端状态管理库 |
| Python 3.13、FastAPI | 编写后端；FastAPI 将 HTTP 请求交给相应 Python 函数 |
| Pydantic 2 | 验证数据形状、类型和取值，定义接口传输的数据对象 |
| PostgreSQL 18 | 持久保存发票、流水、规则及后续会话等数据 |
| SQLAlchemy 2.0、psycopg 3 | SQLAlchemy 组织数据库访问和事务；psycopg 是实际连接 PostgreSQL 的驱动 |
| Alembic | 按版本管理数据库表结构变化，避免每台机器手工建表 |
| uv、npm | 分别安装和运行后端、前端依赖；锁文件记录确定的依赖版本 |
| pytest | 执行后端测试，区分程序逻辑与真实数据库行为 |

这张表说明技术分工，不代表每项能力已经验收。Docker Compose 的 app+db 部署仍属于后续交付工作，当前优先复用本机 PostgreSQL。[开发者指南](docs/开发者指南.md#3-四个后端组件如何配合)进一步解释后端组件如何合作。

## 4. 项目目录结构

```text
项目根目录/
├── README.md                 本页：安装、配置、初始化、启动和排障
├── .env.example              配置字段示例；真实 .env 只留在本机
├── backend/
│   ├── app/api/              HTTP 路由、身份依赖和错误响应
│   ├── app/core/             配置、身份及共享数据对象
│   ├── app/modules/          发票/流水查询和规则等业务模块
│   ├── app/infrastructure/   数据库连接、表模型和维护实现
│   ├── migrations/           Alembic 迁移版本和首迁移 SQL
│   └── tests/                单元、真实数据库集成和 API 测试
├── frontend/                 网页源码、开发代理和前端构建
├── data/seed/                从官方材料整理出的初始数据 JSON
├── scripts/                  维护、数据准备及验收入口
├── materials/                官方原始材料，只读保留
└── docs/                     教学指南、需求、架构、计划与验收证据
```

`seed` 是“初始数据装载”；`migration` 是“表结构迁移”，两者不是同一操作。本机的 `.tools`、`.cache`、虚拟环境和 `var` 用于工具、缓存或运维文件，不应当作业务源码或交付数据。代码阅读路线见[指南第 8 节](docs/开发者指南.md#8-d1-接口与代码阅读路线)。

## 5. 环境准备

### 5.1 需要哪些软件

| 软件 | 版本与用途 | 本项目的已知情况 |
| --- | --- | --- |
| Python | 3.13 系列，运行后端；不要直接换成其他主次版本 | D0 使用 3.13.9 |
| Node.js / npm | Node 24 系列；npm 随 Node 环境提供，安装前端依赖 | D0 使用 Node 24.8.0、npm 11.6.0 |
| uv | 本机局部工具基线 0.13.7，按锁安装 Python 依赖 | 完整 D1 验收脚本目前固定使用 `.tools/bin/uv.exe` |
| PostgreSQL | 18 系列，提供真实数据库服务；客户端也优先同主版本 | 历史前检发现本机 18 服务及 18.6 客户端；认证尚未验证 |
| PowerShell | Windows PowerShell 5.1 可执行现有维护脚本；也可使用已有 PowerShell 7 终端 | 不需要为本项目改系统执行策略 |
| pgAdmin | 可选，用于操作者本机查看 PostgreSQL | 不代替项目维护脚本，也不从其存储中提取密码 |

已有软件先复用，不必重新安装 PostgreSQL。D1 不需要模型 API Key，也不以 Docker 是否可用代替原生数据库验证。精确依赖版本以[后端锁](backend/uv.lock)、[前端锁](frontend/package-lock.json)及[D0 安装证据](docs/development/reports/2026-11-03_D0_baseline.md#工具锁与可复现安装)为准。

### 5.2 安装项目依赖

**工作目录：项目根目录**，即能同时看到本页、backend、frontend 的目录。可用 `Get-Location` 查看当前位置；输出应是这个项目目录，否则先在编辑器中打开项目根目录终端。该命令只查看位置。

以下安装方式有 D0 历史证据；本次文档整理不重新安装。先保证局部 uv 存在，已有文件时跳过安装：

```powershell
if (-not (Test-Path -LiteralPath '.tools/bin/uv.exe')) {
    python -m pip install --target .tools uv==0.13.7
    if ($LASTEXITCODE -ne 0) { throw 'uv 安装失败，停止后续步骤。' }
}
```

作用：把 uv 安装到本项目工具目录。预期：退出 0，局部 uv 文件存在。失败：先看 Python/pip、下载网络及本机目录权限，不继续执行后面的安装。

仍从**项目根目录**开始执行：

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
$env:npm_config_cache = Join-Path (Get-Location) '.cache/npm'
Set-Location backend
../.tools/bin/uv.exe sync --frozen --group dev --group prepare
if ($LASTEXITCODE -ne 0) { throw '后端依赖安装失败，停止。' }
Set-Location ../frontend
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw '前端依赖安装失败，停止。' }
Set-Location ..
```

作用：安装锁定的后端运行/测试/数据准备依赖和前端依赖。预期：两次安装均退出 0，最后回到项目根目录。`--frozen` 和 `npm ci` 使用已有锁；不要为了让安装“通过”随意重建锁文件。失败时保留报错，按[第 10 节](#10-常见问题)处理，再从失败的目录恢复。

## 6. 环境变量配置

环境变量是程序启动时读取的配置项，例如“连接哪个数据库”。本项目支持根目录 `.env` 文件，也支持当前终端的进程环境；**进程环境优先**。例如测试终端设置的 APP_ENV=test 会覆盖 `.env` 中的 development，且不会自动影响另一个终端。实现见[config.py](backend/app/core/config.py)。

**工作目录：项目根目录。** 仅在 `.env` 不存在时创建：

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

作用：建立本机配置文件；预期：已有配置保持原样，新文件仍是空凭证示例。失败：检查工作目录和写权限，不使用覆盖选项。随后在本机编辑器填值，不把真实 `.env`、完整连接、密码或 Key 发到聊天、日志、命令历史和提交包中。

### 6.1 当前需要逐项理解的配置

| 字段 | 含义与何时需要 |
| --- | --- |
| APP_ENV | 运行环境。日常 development；测试必须 test；demo 留演示阶段使用 |
| MODEL_MODE | 模型模式。D1 明确用 disabled，不调用模型；test_stub 只允许 test，live 留后续实测 |
| ADMIN_DATABASE_URL | 初始化前的受控管理员连接，候选为 postgres 用户连接 postgres 系统库。只用于身份/实例查重和获准的新对象创建 |
| TEST_DATABASE_URL | 测试应用连接：finance_tax_app → finance_tax_test。测试中模拟正常应用访问 |
| TEST_MIGRATION_DATABASE_URL | 测试维护连接：finance_tax_migrator → finance_tax_test。准备测试结构和数据；必须与上一项同实例 |
| DATABASE_URL | 日常应用连接：finance_tax_app → finance_tax_dev。读取业务和检查数据库准备状态时需要 |
| MIGRATION_DATABASE_URL | 开发库维护连接：finance_tax_migrator → finance_tax_dev。仅显式迁移、初始装载、授权等维护使用 |
| DEMO_U001_TOKEN | 业务用户 U001 的随机 Bearer 凭证；至少 32 字符。U001 可访问甲、乙企业，并具有合法字段写权限，但 D1 没有业务写接口 |
| DEMO_U002_TOKEN | 业务用户 U002 的另一随机凭证；至少 32 字符且不同于上一项。U002 只读甲企业 |

数据库角色是 PostgreSQL 的身份和权限载体，这里的 app、migrator 都可以作为登录账号。Bearer 是放在 HTTP 请求头中的访问凭证。它不等于 PostgreSQL 密码：两个业务用户日常使用的数据库连接角色都是 finance_tax_app，企业权限仍由后端按业务用户逐次检查。健康接口不要求 Bearer；受保护的业务 API 要求两份演示凭证先配置完整。

数据库连接按“驱动://用户名:URL编码后的密码@主机:端口/数据库”的结构在**本机**填写，这只是结构说明，不是可直接复制的配置值。驱动为 `postgresql+psycopg`。密码中的 `@`、`:`、`/` 等字符要按 URL 规则编码，否则可能被当作连接结构的一部分。

本次原生适配只接受回环地址 127.0.0.1、localhost 或 ::1，端口 5432；localhost 会规范化为 127.0.0.1。管理员、测试和开发连接必须指向同一获准实例，双测试连接的地址一致。不能追加 query/service/hostaddr/多主机参数绕过目标检查；远程与 Compose 主机尚未验证。

管理员密码由实例操作者在本机受控提供；不要猜测或更改已有 postgres 密码，也不要提取 pgAdmin 保存密码。创建新角色前，在本机选定 app、migrator 两组独立密码并填好测试连接；BootstrapTest 会用它们创建新角色。同一个角色在测试库、开发库使用相同口令，两种角色之间口令不同。演示 token 也应由本机安全工具生成随机值，不用 U001、U002 这些编号代替。

### 6.2 其余字段何时处理

下面字段均来自 [.env.example](.env.example)，D1 通常保持默认或空值即可。

| 字段 | 作用与 D1 建议 |
| --- | --- |
| DB_POOL_SIZE | 连接池常规连接容量，默认 5；连接池用于复用连接 |
| DB_MAX_OVERFLOW | 超出常规容量可临时增加的连接数，默认 0 |
| DB_POOL_TIMEOUT_SECONDS | 等待池中可用连接的超时，默认 5 秒 |
| DB_CONNECT_TIMEOUT_SECONDS | 建立数据库连接的超时，默认 5 秒 |
| DB_LOCK_TIMEOUT_MS | 数据库等待锁的超时，默认 5000 毫秒 |
| DB_STATEMENT_TIMEOUT_MS | 数据库执行语句的超时，默认 15000 毫秒 |
| MODEL_ADAPTER | 后续模型适配器标识；D1 disabled 时可空 |
| MODEL_BASE_URL | 后续模型服务地址；live 模式要求 HTTPS，D1 可空 |
| MODEL_API_KEY | 后续模型鉴权秘密；D1 可空，不用于解除数据库阻塞 |
| MODEL_ID | 后续实际模型标识；D1 可空 |
| MODEL_CONTEXT_LIMIT | 后续模型上下文容量；D1 可空 |
| MAX_INPUT_TOKENS | 后续单次模型输入预算；D1 可空 |
| MAX_OUTPUT_TOKENS | 后续单次模型输出预算；D1 可空 |

## 7. 首次初始化

### 本机凭证与首次数据库准备

初始化是准备数据库对象、表结构、初始数据和权限；不是启动网页。顺序是：**只读检查 → 创建测试对象 → Init → Seed → GrantRuntime → Inspect → 真实测试 → 准备开发库**。每一步的概念解释见[指南第 6 节](docs/开发者指南.md#6-首次准备流程为什么分成这些步骤)。

**当前实例已于 2026-11-05 完成预建库准备、迁移、seed、授权和检查；日常使用直接到第 8 节。** 本节供新环境首次准备或排查使用；全新对象 Bootstrap 分支未在本轮执行，仍待真实验证。每条命令均在项目根目录执行，不要把整节一次粘贴运行。每条 native 命令执行后检查 `$LASTEXITCODE`，只有 0 才继续；PowerShell 不会自动因为上一条非零而停止。

**当前实例已有两个项目库和两个角色，不使用 BootstrapTest/BootstrapDev 重新创建。** 用户已在审阅差异后明确继续 D1，按[恢复决定](Documentation.md#d1-既有项目对象准备恢复--2026-11-04)完成显式 PrepareExistingTest/PrepareExistingDev，只补缺失 schema 和既定基础权限，保持 owner/密码不变，并如实记录 operator_precreated 来源。独立口令条件已满足，不把密码发到聊天、不伪造回执。以下首次准备入口不能当作已有数据实例的日常启动步骤。

安全边界：项目业务目标只允许 finance_tax_dev、finance_tax_test 和两种指定角色；管理员核验另用 postgres 系统库。两个业务库内都保留 harness schema，即名为 harness 的数据库内部命名空间，用来组织表。测试只允许 APP_ENV=test、精确 finance_tax_test、串行执行，不接受其他名字或 worker 后缀（并行测试进程常用的名称后缀），连接缺失不回落到开发库。tax_db 是保护对象，不连接其业务库、不改数据/结构/所有者（owner）或访问权限（ACL）、不作模板。已有同名对象先只读报告差异，不自动接管、改密码/owner 或删除重建。来源见[批准记录](Documentation.md#d1-正式实施批准--2026-11-04)。

### 7.1 先做只读检查

填好本机管理员与测试连接后，在**项目根目录**执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action InspectAdmin
```

作用：连接 postgres 系统库，核对候选管理员身份、PostgreSQL 实例及项目同名对象，不连接 tax_db 业务库。预期：退出 0，返回可审阅的身份、实例、角色和数据库目录信息。失败：停止后续步骤；检查受控凭证和实例，不把服务已启动当认证成功。同名对象即使看似一致，也先报告并审查。Bypass 只用于这个脚本进程，不改系统执行策略。

### 7.2 创建测试对象

只有上一步核验通过、确认项目两角色和两库没有预先存在且不存在旧创建回执时，才进入此步。仍在**项目根目录**：

本段 BootstrapTest 仅适用于将来的全新实例，**不是当前已预建实例的操作**。当前实例在独立凭证条件满足后，工作目录为项目根目录，使用明确记录的批准引用：

```powershell
$env:APP_ENV = 'test'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action PrepareExistingTest -ApprovalRef 'Documentation.md#d1-既有项目对象准备恢复--2026-11-04'
```

作用：先核验实际管理员/两角色身份、实例/OID、owner/编码、角色属性及空对象集合，再仅补缺失 harness 和基础最小权限。预期：退出 0、result 为 schema_and_base_permissions_prepared，回执标明操作者预建来源和已准备的测试库；2026-11-05 已实际退出 0。此步是首次准备，当前实例已完成，不要重复执行；已有数据会被保护检查拒绝。失败时停止，不改已有密码/owner，不删除旧对象。该显式准备成功后进入第 7.3 节；若是全新实例才使用下面 BootstrapTest 命令：

```powershell
$env:APP_ENV = 'test'
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action BootstrapTest
```

作用：创建 finance_tax_app、finance_tax_migrator、finance_tax_test，以及其中的 harness schema，并设置基础连接权限。预期：退出 0，输出创建对象名称，本机产生不含密码的 `var/bootstrap-receipt.json` 创建来源回执。此时尚没有业务表和业务数据。失败：停止；部分对象可能已经创建，不删除重跑，也不手工伪造/编辑回执来绕过检查，回到只读审查处理差异。

### 7.3 建表、装数据、授权并检查

以下每一步的**工作目录均为项目根目录**，沿用 APP_ENV=test。按行号顺序，一步成功再运行下一步：

| 步骤 | 命令 | 作用和预期结果（2026-11-05 已真实验证） |
| --- | --- | --- |
| 1. Init | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action Init -TestTarget` | 用维护账号执行首迁移，建立业务/技术表并记录结构版本；退出 0、result 为 migrated |
| 2. Seed | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action Seed -TestTarget` | 一次装入规范化初始数据；首次退出 0、result 为 loaded，同 hash 重跑为 verified_existing |
| 3. GrantRuntime | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action GrantRuntime -TestTarget` | 收敛并检查 app 的表/列/序列权限；退出 0、result 为 granted |
| 4. Inspect | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action Inspect -TestTarget` | 只读检查结构版本、初始数据指纹/基础键和有效权限；退出 0，返回 schema_revision 与 seed_hash |

任何一步非 0 都停止，不跳过或用管理员运行 app“解决”问题。维护入口退出 2 表示配置、目标或认证身份拒绝；退出 4 表示数据库操作失败，须保留输出并调查。Init 的 migrated 输出不能代替完整业务验收，Inspect 也不是全部测试。

初始资料应为 2 企业、2 用户、40 发票、48 流水和 5 个规则版本；数量依据为[规范化文件](data/seed/manifest.json)，真实入库与基础键/类型检查见[验收汇总](docs/development/reports/2026-11-05_D1_credentials/summary.json)的 TC001/002。同 hash Seed 不覆盖现有用途；异 hash、或无装载标记却已有部分业务数据时拒绝，不能用它重新灌掉当前状态。

### 7.4 运行测试库验收

**工作目录：项目根目录；作用：执行 D1 指定的串行测试并记录结果。此命令会在保护检查通过后重建测试库 harness schema 和 fixture（测试用的已知初始数据），已在本轮真实验证，不是纯查询。** 它不删除整个数据库、容器或卷，只能对获准的测试目标使用：

```powershell
backend/.venv/Scripts/python.exe scripts/verify_d1.py --output-dir docs/development/reports/2026-11-05_D1_credentials
```

预期：所有要求的真实数据库子项执行且通过，测试门才可能为 passed。脚本退出 2 表示仍 blocked，退出 1 表示汇总检查失败；只有退出 0 且实际测试门 passed、无失败/阻塞，才可继续开发库准备。它会记录新 attempt，并更新测试汇总；即使原始 pytest 返回 0，也要检查有没有跳过的真实测试。2026-11-05 结果为 216 passed、0 failed、0 blocked；旧 106/47 记录保留为历史，新环境仍须实际运行本关。

不要用 SQLite、其他数据库或改 APP_ENV 来绕过目标保护。显式测试重置不是日常步骤；目前没有理由执行它。数据清理只能在完整保护和已授权测试范围内进行。[测试规范](docs/development/04_测试与验收规范.md#2-可复现fixture)保留完整限制。

### 7.5 测试通过后才准备开发库

**当前实例已完成此步，日常启动直接到第 8 节，不要重新准备已有库。** 在新环境中真实测试门通过后，使用同一实例、同一角色的开发连接；程序还会核对本项目创建来源回执和实际通过的 summary。**工作目录：项目根目录**，每步退出 0 后才继续：

finance_tax_dev 已存在时，应使用以下已在本轮验证的显式预建库入口；仅在测试通过后执行，不能对同一个库再运行下面的全新建库入口：

```powershell
$env:APP_ENV = 'development'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action PrepareExistingDev -TestAcceptance docs/development/reports/2026-11-05_D1_credentials/summary.json -ApprovalRef 'Documentation.md#d1-既有项目对象准备恢复--2026-11-04'
```

作用：在通过的真实测试报告、既有来源记录、两角色登录和空开发库检查下，补齐开发库 schema 与基础权限；预期退出 0，仍不更改 owner/密码。失败停止；成功后执行本节下表 Init/Seed/GrantRuntime/Inspect。下列 BootstrapDev 只适用于原本由新建流程准备且开发库尚不存在的实例：

```powershell
$env:APP_ENV = 'development'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action BootstrapDev -TestAcceptance docs/development/reports/2026-11-05_D1_credentials/summary.json
```

作用：在前置核验通过后创建 finance_tax_dev 及 harness schema，复用本项目刚创建并核验过的角色，不改其密码。预期：退出 0，输出新开发库名称。失败：保留报告并停止；旧库冲突不能靠删除、改 owner 或改回执解决。

PrepareExistingDev 或 BootstrapDev 成功后，仍在**项目根目录**依次执行下表；这里不带 `-TestTarget`，所以目标是显式开发维护连接：

| 命令 | 作用与预期 | 失败处理 |
| --- | --- | --- |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action Init` | 开发库建表，退出 0、migrated | 停止，保留错误，不启动为已准备状态 |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action Seed` | 开发库首次装载，退出 0、loaded | 停止，不覆盖已有数据 |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action GrantRuntime` | 配置运行权限，退出 0、granted | 停止，不用 GRANT ALL 代替 |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action Inspect` | 检查准备结果，退出 0，返回结构版本和指纹 | 停止，调查具体未满足项 |

这组开发库步骤已真实通过；app 连接的开发库健康、身份、金额和越权 HTTP 检查见[结果](docs/development/reports/2026-11-05_D1_credentials/development-http.json)。验收使用仅在子进程有效的临时演示令牌；本机日常访问仍需按第 6 节配置两项独立演示令牌。测试门通过只是进入开发库准备的条件；开发库准备和交接未完成前，不能把 D1 最终状态写成 passed。D1 完成后仍需后续明确开发范围，本次不进入 D2。

## 8. 日常启动

| 情况 | 应该做什么 |
| --- | --- |
| 第一次、尚无依赖和数据库 | 按第 5～7 节准备；数据库未就绪也可先启动诊断，但业务不可据此验收 |
| 后续正常开机使用 | 检查 PostgreSQL 服务，启动前后端；不重复 Bootstrap、Init、Seed |
| 只想确认工程能启动 | 使用 development + disabled；缺数据库时预期 ready 为 503，不能当业务可用 |

### 8.1 后端终端

**工作目录：backend**。请从项目根目录进入 backend，或直接在该目录打开终端。不要在 frontend 终端执行这组命令：

```powershell
$env:UV_CACHE_DIR = Join-Path (Resolve-Path ..).Path '.cache/uv'
$env:APP_ENV = 'development'
$env:MODEL_MODE = 'disabled'
../.tools/bin/uv.exe run --frozen --no-sync uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

作用：用已安装依赖启动单进程 FastAPI 服务，保持终端运行。D0 有诊断启动历史；D1 的真实数据库准备成功仍待验证。预期：终端报告服务监听 127.0.0.1:8000，可访问健康和接口文档。失败：看终端报错；依赖缺失回第 5 节，配置错误回第 6 节，端口占用先核对旧进程。不要启动多个 app 进程来尝试排障。

### 8.2 前端终端

打开**另一个终端，工作目录：frontend**：

```powershell
npm.cmd run dev
```

作用：启动 Vite 开发服务器。预期：终端给出浏览器访问地址，页面显示“工程与配置基线”等准备信息；以实际显示地址为准。失败：检查 Node 版本、依赖和工作目录。页面目前尚未接上 D1 业务查询；看到准备页不代表数据库已连接。开发时 `/api` 请求会代理到后端 127.0.0.1:8000，配置见[vite.config.ts](frontend/vite.config.ts)。

停止：分别在两个服务终端按 Ctrl+C；重新启动重复本节，不删除数据库或卷，不重新灌初始数据。终端关闭后，该终端临时设置的环境变量也不会自动传给下次新终端。

## 9. 功能验证

### 9.1 分层确认，不只看网页

以下为**操作检查方法，未在本次文档任务中执行**。后端已启动后，在浏览器按表访问；无需终端工作目录，也不需要 Bearer：

| 地址/检查 | 预期与能说明的事情 | 不符合时怎么办 |
| --- | --- | --- |
| 前端终端显示的地址 | 显示当前准备网页，说明前端开发服务器在响应 | 检查 frontend 终端；不能仅凭页面文字判断后端状态 |
| `http://127.0.0.1:8000/api/v1/health/live` | HTTP 200、data.status 为 alive，说明后端能处理请求 | 连接失败先看后端进程、地址和端口 |
| `http://127.0.0.1:8000/api/v1/health/ready` | 当前已准备实例应为 HTTP 200、ready；数据库未准备时应为 503、not_ready | 若出现 503，检查目标、schema/seed/权限和服务日志，不把它改成固定成功 |
| `http://127.0.0.1:8000/docs` | 出现 Swagger 交互式接口说明页 | 检查后端；页面能打开不表示每个接口都执行过 |

ready 检查的是受限数据库连接、表结构版本、初始数据指纹/基础键和有效权限。它没有替你完成全部 D1 测试，也不证明演示 token 或 AI 已可用。**当前没有真实 ready=200 的验收证据。** 规范与实现见[健康接口](docs/architecture/06_API接口设计.md#8-健康接口)、[health.py](backend/app/api/routers/health.py)。

### 9.2 数据库准备后再验证业务接口

下面接口均为 GET，只读。数据库和两份演示 token 配置完成后，在本机 Swagger 页点击 Authorize，输入对应 token，再选择接口的 Try it out / Execute；不要把 token 放进 URL 或截图分享。所有业务请求以 `/api/v1` 为前缀。**这些接口的真实 PG/API 自动测试已通过；本机日常演示 token 仍需自行配置，验收临时 token 已随子进程退出失效：**

| 接口与参数 | 应核对什么 | 失败如何理解 |
| --- | --- | --- |
| `/me` | U001 返回甲、乙；U002 只返回甲 | 401 检查凭证；503 检查身份配置或数据库，不能当“没有企业” |
| `/companies/C001/totals`，business_month=2026-09 | 初始数据下发票 9622.06、支出 7180.74、收入 13000.50，金额是元字符串 | 这些是初始明细的验收预期，不是本次实测；异常不能用固定值补响应 |
| `/invoices/search`，q=F002 | 按当前身份过滤授权范围，同号票仍由企业+票号区分 | 无数据、无权限、存储故障需区分；不能仅靠前端筛选 |
| `/companies/C001/purpose-check`，business_month=2026-09 | 初始甲缺填 F002/F003/F004/F006/F009 | 必须来自当前数据和适用规则；只有备注仍算用途缺失 |
| 同一 purpose-check，business_month=2026-08 | unsupported，missing/count 为 null | 不能套用停用规则恢复八月用途检查 |
| U002 查询乙企业金额 | HTTP 403，不泄露乙企业金额 | 这是应有的权限拒绝，不是修成“返回 0” |

完整 D1 还要求流水、规则、日期边界、seed 保护、数据库列权限及提交后新连接回读等测试；以[D1 任务卡](docs/development/tasks/D1_PostgreSQL与只读业务.md#必需测试)和阶段证据为准，不以这几次手工请求关闭验收。

## 10. 常见问题

| 问题 | 先检查什么，怎样处理 |
| --- | --- |
| Windows 阻止 npm.ps1 | 本文使用 `npm.cmd`；先用此入口，不必更改系统执行策略 |
| 找不到 Python、Node 或 uv | 确认安装版本和当前终端可见路径；uv 可用本文的项目局部路径。不要把全局其他版本当已验证版本 |
| uv 下载失败或依赖不全 | 检查网络、缓存目录和文件权限，保留原始错误；离线验收只在缓存完整时可用。不随意删锁或升级依赖 |
| npm 安装或构建失败 | 确认位于 frontend、Node 为 24 系列、锁文件存在；构建应走 package.json 的包装器，不手动换成其他清理命令 |
| 命令找不到 backend、frontend 或脚本 | 每个新终端独立选择工作目录；先回本文对应步骤标注的目录 |
| PostgreSQL 服务运行，但连接被拒绝 | 服务运行只说明进程可能在；仍要核验地址、实例、管理员身份和认证。不要改 pg_hba.conf 或 tax_db ACL 绕过 |
| psql 不在 PATH | 服务可能仍已安装；客户端通常在安装目录的 bin 下，以实际安装位置为准，不据此重装/重置数据库 |
| InspectConfig 成功，却不能查询 | 它只检查配置结构，没有认证 SQL；继续按首次准备流程，不把它当数据库通过 |
| 维护退出 2 / 4 | 2 先查配置/目标/身份，4 查操作失败原因；停止后续步骤，不盲目重跑写操作 |
| 提示同名对象或来源回执不匹配 | 保留只读差异报告，暂停相关维护；不接管旧库，不编辑回执、改 owner、改密码或删除重建 |
| 地址返回 127.0.0.1/32 却被认为不匹配 | 该主机地址表示差异已修复并回归；不同 IP 或端口仍拒绝。若继续拒绝，检查缺失 schema、owner 或角色条件，不跳过完整保护 |
| ResetTest 与普通重启有什么区别 | ResetTest 是显式测试 schema 重建入口，只限完整保护通过且已授权的 finance_tax_test；会影响测试数据，不是普通重启。本次不执行重置，不能将阅读本文当作重置授权 |
| API 返回 503 | 先看 error.code；身份未完整配置可能为 NOT_READY，读取不可用可能为 STORAGE_UNAVAILABLE；都不代表金额是 0 |
| 后端 8000 端口被占用 | 先确认占用者是不是本项目旧服务，正确停止后再启动；若改端口需同步前端代理配置，文档本身不代改 |
| 测试显示 skipped，pytest 却退出 0 | 真实 PG 分支在阶段汇总中仍是 blocked；看完整验收脚本结果，不只看绿色退出 |
| 重启后网页仍显示 D0 | 当前 App.vue 是静态准备页，不会读取数据库状态；用第 9 节检查，不能据页面文字判断 D1 是否完成 |

前端构建包装器会检查并清理生成的 dist；不要把手工文件放进该目录。原始材料、需求和历史测试证据均保留，不以删除数据库、容器或数据卷作为正常重启方法。

## 11. 技术文档导航

本页是安装、配置、首次准备、启动、验证和排障的**唯一操作入口**。指南讲原理，报告保存历史证据；不要在多个文档维护另一套现行命令。

| 想了解什么 | 从哪里读 |
| --- | --- |
| 先理解后端工程与数据库概念 | [开发者指南](docs/开发者指南.md) |
| 用通俗语言了解 D1 完成项和阻塞 | [D1 报告顶部说明](docs/development/reports/2026-11-04_D1.md#非技术读者快速了解-d1) |
| 当前阶段状态与恢复动作 | [progress](docs/development/progress.md)、[执行记录](Documentation.md) |
| 下一阶段计划和开发规则 | [开发导航](docs/development/00_开发导航.md)、[Plan](Plan.md)、[AGENTS](AGENTS.md) |
| 业务究竟要求什么 | [需求说明书](docs/requirements/03_软件需求分析说明书.md)、[追踪矩阵](docs/requirements/04_需求追踪矩阵.md) |
| 数据库、接口与实施约束 | [数据库设计](docs/architecture/05_数据库与数据架构设计.md)、[API 设计](docs/architecture/06_API接口设计.md)、[实施契约](docs/architecture/12_开发实施契约补充.md) |
| 接口的精确机器定义 | [JSON Schema](docs/architecture/contracts/contracts.schema.json)、[Tools](docs/architecture/contracts/tools.json)、[HTTP 映射](docs/architecture/contracts/http-operations.json) |
| 查真实测试记录与范围 | [D1 原报告](docs/development/reports/2026-11-04_D1.md)、[测试规范](docs/development/04_测试与验收规范.md)、[用例清单](docs/development/test-cases.json) |
