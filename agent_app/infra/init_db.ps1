# TPC-H 数据导入脚本（Windows PowerShell）
#
# 用法：
#   1. 先起容器：docker compose up -d
#   2. 再跑本脚本：pwsh ./init_db.ps1
#
# ⚠️ 本脚本是【骨架 + 步骤说明】，W2 你需要自己补完实际的 dbgen 调用。
#    TPC-H 的 dbgen 需要编译，是最容易卡住的一步 —— 卡超过 2 小时就用 SQLite 兜底。

$ErrorActionPreference = "Stop"
$PG_CONTAINER = "agent_app_pg"
$SF = "0.1"   # scale factor：0.1 ≈ 60 万行；1 ≈ 600 万行

Write-Host "== 1. 检查容器 ==" -ForegroundColor Cyan
$running = docker ps --filter "name=$PG_CONTAINER" --format "{{.Names}}"
if ($running -ne $PG_CONTAINER) {
    throw "容器没起来，先运行：docker compose up -d"
}
Write-Host "OK: $PG_CONTAINER 正在运行"

Write-Host "`n== 2. 生成 TPC-H 数据 ==" -ForegroundColor Cyan
# TODO(W2)：下载并编译 dbgen，然后生成数据
#   期望目录结构：
#       infra/tpch/dbgen        （编译出来的可执行文件，Linux 下用 WSL 或容器里跑）
#       infra/tpch/data/*.tbl   （8 个 .tbl 文件：customer / lineitem / orders / part ...）
#   参考：https://github.com/electrum/tpch-dbgen
Write-Host "  [TODO] 这一步需要手动完成，见 infra/README.md"
if (-not (Test-Path "./tpch/data")) {
    Write-Host "  跳过：./tpch/data 不存在" -ForegroundColor Yellow
    exit 0
}

Write-Host "`n== 3. 建表 ==" -ForegroundColor Cyan
# TODO(W2)：把 DDL 灌进去
#   Get-Content ./tpch/schema.sql -Raw | docker exec -i $PG_CONTAINER psql -U agent -d tpch

Write-Host "`n== 4. 导入数据 ==" -ForegroundColor Cyan
# TODO(W2)：用 \copy 导入 8 个 .tbl（注意顺序：先父表后子表，避免外键报错）
#   docker exec -i $PG_CONTAINER psql -U agent -d tpch -c "\copy customer FROM '/data/customer.tbl' WITH (FORMAT csv, DELIMITER '|')"

Write-Host "`n== 5. 收集统计信息 ==" -ForegroundColor Cyan
# ⚠️ 这一步不能省！没有统计信息，优化器会做出很差的计划
docker exec $PG_CONTAINER psql -U agent -d tpch -c "ANALYZE;" | Out-Null
Write-Host "OK: ANALYZE 完成"

Write-Host "`n== 6. 自检 ==" -ForegroundColor Cyan
docker exec $PG_CONTAINER psql -U agent -d tpch -c "\dt"
docker exec $PG_CONTAINER psql -U agent -d tpch -t -c "SELECT COUNT(*) FROM orders;"

Write-Host "`n完成。连接串：" -ForegroundColor Green
Write-Host "postgresql://agent:agent_dev_pw@localhost:55432/tpch"
