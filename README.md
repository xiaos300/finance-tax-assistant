# 财税 Harness · D0

当前仅完成工程与配置基线。网页显示准备状态；后端仅提供健康检查。数据库业务、迁移、角色、seed、模型调用及 Harness 尚未实现。D0 后停止，D1 需用户另行授权。

运行环境：Windows，Python 3.13、Node 24。精确工具及依赖版本、锁哈希和实测状态见 [D0 报告](docs/development/reports/2026-11-03_D0_baseline.md)。PowerShell 7 的 `pwsh` 若不可用，可用 Windows PowerShell 5.1 执行本阶段脚本。`npm.ps1` 被执行策略阻止时使用 `npm.cmd`，无需修改系统执行策略。

从项目根目录执行安装（本机 uv 局部安装在 `.tools/bin/uv.exe`；其他机器可使用已有 uv 替换该路径）：

```powershell
python -m pip install --target .tools uv==0.13.7
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
$env:npm_config_cache = Join-Path (Get-Location) '.cache/npm'
Set-Location backend
../.tools/bin/uv.exe sync --frozen --group dev --group prepare
../.tools/bin/uv.exe run --frozen --no-sync pytest tests/unit
Set-Location ../frontend
npm.cmd ci
npm.cmd run typecheck
npm.cmd run test -- --run
npm.cmd run build
```

首次开发已使用 `uv lock` 和 `npm.cmd install` 实际生成锁；后续安装使用冻结命令，不在启动时重新解析。缓存、虚拟环境和 node_modules 仅本地使用，不进入构建上下文或提交包。

在项目根复制 `.env.example` 为 `.env`，或在受控终端设置变量。配置固定读取根 `.env`，环境变量优先，不随当前工作目录寻找配置。示例凭证全部为空。D0 诊断只需 `APP_ENV=development` 和 `MODEL_MODE=disabled`，无须数据库或模型账号。

后端（在 backend 目录）：

```powershell
$env:APP_ENV = 'development'
$env:MODEL_MODE = 'disabled'
../.tools/bin/uv.exe run --frozen --no-sync uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

前端在另一个终端的 frontend 目录运行 `npm.cmd run dev`，浏览器访问终端显示的回环地址。Vite 将 `/api` 代理至 `127.0.0.1:8000`。构建输出在 `frontend/dist`，本阶段尚无演示静态托管或 Compose 部署。当前 Windows/Node 组合在 Vite 默认清空已有输出时出现进程异常，build 包装器先校验整个 dist 无链接、路径不越界，再逐项清理生成文件并构建，避免遗留旧产物；不要把手工文件放入 dist。

健康检查为 `GET /api/v1/health/live`（200、alive）和 `GET /api/v1/health/ready`（503、not_ready）。D0 未实现数据库准备验证，ready 始终明确返回 `database_prepared=false`，不会连接数据库或暗中创建数据。D1 必须用真实准备检查替换此保守响应，后续按契约增加单实例锁等条件。响应包含服务端生成的 request_id。

数据库配置独立于模型：`DATABASE_URL` 只接受 `postgresql+psycopg`、明确主机/数据库/用户；维护入口只读 `MIGRATION_DATABASE_URL`，缺失时不会回落到应用连接。角色密码由操作者受控提供，特殊字符须 URL 编码，禁止把真实连接写入命令行、报告和聊天。D0 不连接、不迁移、不 seed。维护入口配置校验（项目根）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/manage.ps1 -Action InspectConfig
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_environment.ps1
```

`InspectConfig` 成功退出 0，配置缺失/非法退出 2；Init/Seed/GrantRuntime 明确退出 3，等待 D1。环境探测只输出版本，不输出变量值，缺可选运行时退出 2；这不等于数据库或 Docker server 可用性验证。这里的 Bypass 仅用于本次脚本进程，不修改系统策略。

`MODEL_MODE` 分为 disabled/live/test_stub。disabled 忽略空的 live 数值，不调用模型；test_stub 仅 APP_ENV=test 可配置，当前未实现替身或 AI 功能；demo 未指定模式时默认 live。live 校验 HTTPS、必填配置及 token 预算，当前尚无供应商适配或 probe，配置合法不等于模型已验收。D0 不实现聊天接口；TC051 的 disabled 聊天 503/无伪轮子项留到 D2。

秘密与边界检查：`python scripts/verify_baseline.py` 扫描源码和前端 dist，生成脱敏结果与源码哈希。它不替代 D6 发布包核验。原始 materials 和五份 requirements 不修改，项目未初始化 Git。
