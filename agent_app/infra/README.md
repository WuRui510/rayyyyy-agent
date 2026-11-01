# 场景层 · 基础设施

这个目录存放**环境与数据**相关的东西。换场景时整个替换。

| 文件 | 用途 |
|---|---|
| `docker-compose.yml` | 起一个 PostgreSQL 副本库 |
| `init_db.sh` | 建库 + 导入 TPC-H 数据 |
| `README.md` | 本文件 |

---

## 为什么用 Docker

Agent 会执行 `CREATE INDEX`、`DROP INDEX` 这类**写操作**。

**它只能操作一个临时的、可随时丢弃的数据库副本**——绝不能碰任何真实数据。

Docker 容器天然满足：起一个 → 随便折腾 → `docker compose down -v` 一键清空。

---

## 计划（W2 才动手）

```bash
cd infra
docker compose up -d          # 起 Postgres
./init_db.sh                  # 建库 + 导入 TPC-H (sf=0.1)
```

**规模选择**：先用 `scale factor 0.1`（约 60 万行）跑通全流程，够诊断。
如果效果不错，W8 再放大到 `1`（约 600 万行）——**数据量上去，优化空间才明显**。

---

## ⚠️ 注意

- 端口**不要用 5432**（可能和你本机的 Postgres 冲突），用 `55432`
- 数据卷用完要清：`docker compose down -v`
- `.env` 里的 `PG_DSN` 要指向这个容器

---

## W2 的具体步骤（提前看一眼，心里有数）

1. 装 Docker Desktop（如果没有）
2. `docker compose up -d`
3. 下载 TPC-H 的 `dbgen` 工具，生成数据
4. 用 `\copy` 把数据导入
5. 写一个 `baseline.py`：给一条 SQL，跑一次，记录耗时 + `EXPLAIN ANALYZE` 输出

**这一步可能卡住你半天。** 如果卡住超过 2 小时，先用 SQLite 跑通流程，W3 再换 Postgres（工具层接口不变）。
