# 书法评测唯一约束：历史数据升级手册

适用范围：新增 `evaluations.attempt_id` 与 `evaluations.homework_id` 唯一索引后的第一次升级。**合并 GitHub PR 不等于完成数据库升级。** API 启动时会自动执行 `alembic upgrade head`；如果历史上存在同一份作业的多条评测，它会拒绝创建唯一索引，服务不会假装迁移成功。

## 操作前

1. 明确将要升级的真实数据库与 `DATABASE_URL`；不要把测试、演示、生产数据库弄混。
2. **停止所有 API 进程、定时作业与后台评测写入器**。确保本次维护期间不会再写 `evaluations`、`review` 或图片。
3. 对数据库和书法作业上传目录制作**可以验证恢复**的独立备份。保留回滚点，记录当前 Alembic 版本；不要在没有备份时执行 `--apply`。
4. 完整代码须包含本目录的 `scripts/reconcile_evaluations.py`。运行这个脚本**不需要启动 Web 服务**；先处理旧数据，最后才允许重启 API。

## 只读审计、人工选择

在 `api-server/` 目录中：

```bash
python scripts/reconcile_evaluations.py --output duplicate-plan.json
```

若存在重复项，返回码为 2 是**有意的告警**，并非文件写入失败。JSON 中每一组 `homework_id` 有 `ids`、必要摘要和每行的 SHA-256 内容指纹；`keep_id: null` 表示尚无人做出选择。

针对每组，先在**只读数据库查询**中核对其完整评分、状态、来源、批阅关联和图片引用，人工填写一个已列出的 `keep_id`。不能机械选择最高分、最新时间，也不应该为了绕过迁移删除历史成绩。

如果存在其他表通过外键指向 `evaluations`，本工具会拒绝处理。应先设计关联数据迁移并单独验收，禁止强行取消外键校验。

## 明确批准并归档

所有 `keep_id` 已确定，备份已验证、应用写入全部停止后：

```bash
python scripts/reconcile_evaluations.py --plan duplicate-plan.json --apply --backup-confirmed --writers-stopped
```

- 脚本重新检查**全部冲突组、行 ID、每条记录完整内容指纹**；如果审计后评分或评语发生变化，拒绝旧计划。
- 将未保留行的**全部字段**写入数据库表 `evaluations_legacy_archive`，再从业务表移走；归档插入、原表移走和保留行校验属于同一个数据库事务。出现插入冲突等异常时，事务回滚。
- 历史归档表含评语、图片路径等敏感信息，必须与业务数据库执行相同的访问控制和备份策略。
- `--writers-stopped` 和 `--backup-confirmed` 是操作者声明，不是自动验证或分布式锁。SQLite 不提供与 MySQL 相同的行级锁；**脱机维护是硬前提**。

无冲突时不需要 `--apply`。

## 执行迁移与验收

```bash
alembic upgrade head
```

核对 Alembic 版本、唯一索引存在、每个 `homework_id` 在现役评测表中至多有一行，并抽查选定保留行和归档快照。之后才恢复 API 服务，测试首次评测、强制重评、失败恢复、结果图片读取。若任一步失败，保持服务停止并基于维护前备份恢复，不要反复执行不清楚结果的脚本。

**禁止把 `Base.metadata.create_all()` 当成迁移修复手段**：它不会修改已有表的唯一索引或字段。新版 API 在任何环境都不会对 Alembic 错误静默回退。

## 不处理的范围

本操作不是用户历史评分清空，也不是自动的后台数据清理；归档仍保留原始 ID、JSON、评语和图片引用。恢复被归档的某条评测需要单独制定恢复/回滚方案（包括先取消唯一索引并核实外键），本脚本**不提供直接恢复写入**。旧评测图片也不会被这个工具删除。
