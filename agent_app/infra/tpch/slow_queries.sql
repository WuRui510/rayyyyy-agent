-- W2 选定的 3 条慢查询候选
--
-- 用途：W4 诊断能力的输入 / W7 优化的靶子 / W8 对比表的行。
-- 基线数据：2026-11-04 采集，PostgreSQL 16.15，lineitem 599,735 行（108 MB）
-- 注意：耗时受缓存状态影响。容器刚重启时 Buffer 全 read，会明显偏慢；
--       连续跑几次后大部分命中缓存，数字会下降。做对比表时每次都要记 Buffers。
--
-- 三条覆盖三种不同的瓶颈形态：
--   A 缺索引（过滤）      —— Seq Scan 全表只为找出 225 行
--   B 表达式阻止索引      —— 列被函数包裹，建了索引也用不上
--   C 缺索引（排序）      —— 全表扫 + top-N heapsort


-- ============================================================
-- A. 高选择性过滤，但没有索引
--    基线 28.4 ms
--    信号：Parallel Seq Scan / Rows Removed by Filter 599,511 / read=6960
--    为什么慢：扫 11544 页（整个表）只返回 225 行，比例 2665:1
--    优化方向：CREATE INDEX ON lineitem(l_shipdate)
--    预期：能走 Index Scan，只读几十页，降到 1 ms 量级
-- ============================================================
SELECT count(*), sum(l_extendedprice)
FROM lineitem
WHERE l_shipdate = DATE '1998-01-15';


-- ============================================================
-- B. 函数包裹列 —— 索引杀手（本项目最有教学价值的一条）
--    基线 36.8 ms
--    信号：Parallel Seq Scan on orders / Rows Removed by Filter 74,126
--          Filter: date_trunc('month', o_orderdate) = ...
--    为什么慢：即使建了 CREATE INDEX ON orders(o_orderdate)，也用不上，
--              因为 WHERE 里比较的是 date_trunc(...) 的结果，不是原列。
--    优化方向：**两步，只有建索引不够**
--              ① 改写 SQL 成范围查询：
--                 WHERE o_orderdate >= DATE '1997-06-01'
--                   AND o_orderdate <  DATE '1997-07-01'
--              ② 再建索引 ON orders(o_orderdate)
--    这条是「多轮优化」的核心案例：第一轮建索引无效，Agent 必须看
--    EXPLAIN 发现还是 Seq Scan，才会想到去改 SQL 而不是继续加索引。
-- ============================================================
SELECT count(*)
FROM orders
WHERE date_trunc('month', o_orderdate) = DATE '1997-06-01';


-- ============================================================
-- C. ORDER BY + LIMIT，但没有排序索引
--    基线 89.5 ms（三条里最慢，优化空间也最大）
--    信号：Parallel Seq Scan on lineitem + Sort (top-N heapsort)
--    为什么慢：为了取最大的 10 个，扫了全部 60 万行再排序
--    优化方向：CREATE INDEX ON lineitem(l_extendedprice DESC)
--              索引本身是有序的，走 Index Scan backward 只需读 10 行
--    预期：降到 0.2 ms 量级（约 400 倍）—— 三条里对比表最漂亮的一条
-- ============================================================
SELECT l_orderkey, l_partkey, l_extendedprice
FROM lineitem
ORDER BY l_extendedprice DESC
LIMIT 10;


-- ============================================================
-- 被淘汰的候选（记录下来，避免以后重复试）
-- ============================================================
--
-- ✗ l_shipdate <= DATE '1998-09-02'（101.9 ms）
--   看着慢，但 Rows Removed by Filter 只有 14,422 —— 93% 的行都留下了。
--   选择性这么差，加索引反而更慢，全表扫本来就是最优计划。
--   教训：判断「该不该建索引」看的是选择性，不是耗时。
--
-- ✗ EXISTS 半连接（TPC-H Q4 原版，18.9 ms）
--   不够慢，而且 Buffers: shared hit=23647 全是缓存命中，没读盘。
--   在 60 万行这个量级下，它已经跑得挺好。
--
-- ✗ lineitem JOIN part 的 Hash Join（115.5 ms）
--   绝对耗时够慢，但优化路径不清晰：大表 join 小表时 Hash Join 本来就是
--   优选项，加 l_partkey 索引也未必会被选中。
--   不适合当「优化前后对比」的案例，因为可能优化不动。
