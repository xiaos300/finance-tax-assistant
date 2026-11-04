# 阶段报告与证据目录

本目录已有的source_manifest是复审前19份来源的hash，review_validation是设计文档校验结果；它们不是软件运行验收。现已有 [D0实现报告](2026-11-03_D0_baseline.md)及同名证据目录，失败复验记录在D0_attempt1/2/3；D1—D7未实施。

后续每阶段使用`<日期>_<阶段>_<短标识>.md`，需要大量证据时配同名目录。报告最少包含以下实际内容，不能仅填空模板：

1. 用户授权范围、阶段、需求/契约版本，Git commit或source_tree_hash。
2. 完成行为与实际修改文件，API/数据库迁移/依赖影响。
3. 每条实际执行命令、工作目录、退出码及必要环境版本；未执行命令不要混入结果。
4. TC/子项和AC对应、fixture/seed hash、模型none/stub/real及profile标识，passed/failed/blocked/not_run/not_in_scope。
5. 证据路径及turn/invocation/call/operation关联，提交/回读事实与敏感信息扫描；程序事实与模型措辞分开。
6. local/external/overall门逐项结论，仍缺条件、风险、下一可独立推进任务与progress更新链接。

summary.json字段和通过规则见[测试规范](../04_测试与验收规范.md)。报告禁止真实token/模型密钥/数据库密码或完整敏感URL。真实模型缺失写blocked，本地替身通过也不能冒充live；设计修订只标设计完成，不能关闭软件测试。
