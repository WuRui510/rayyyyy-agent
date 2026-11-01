"""生成 TPC-H sf=0.1 规模的测试数据。

仿 TPC-H 的数据分布，不是官方 dbgen 的输出——但你需要的三样（表结构严格一致、
数据量到线、分布合理）都有，而且不需要 C 编译器。

固定随机种子 -> 每次生成的数据完全相同。W8 做「优化前 vs 优化后」对比表时，
这一点很关键：数据变了，耗时就没有可比性。

输出：data/<表名>.tbl，'|' 分隔、无尾随分隔符，可直接被 COPY 导入。

用法：
    py gen_data.py
"""

import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
OUT = Path(__file__).parent / "data"

# ---------- sf=0.1 的行数（对齐 dbgen 实际产出）----------
N_REGION = 5
N_NATION = 25
N_SUPPLIER = 1_000
N_CUSTOMER = 15_000
N_PART = 20_000
N_PARTSUPP = 80_000
N_ORDERS = 150_000

D0 = date(1992, 1, 1)
SPAN = 2557  # 1992-01-01 → 1998-12-31

REGIONS = ["AFRICA", "AMERICA", "ASIA", "EUROPE", "MIDDLE EAST"]
NATIONS = [
    "ALGERIA", "ARGENTINA", "BRAZIL", "CANADA", "EGYPT", "ETHIOPIA", "FRANCE",
    "GERMANY", "INDIA", "INDONESIA", "IRAN", "IRAQ", "JAPAN", "JORDAN", "KENYA",
    "MOROCCO", "MOZAMBIQUE", "PERU", "CHINA", "ROMANIA", "SAUDI ARABIA",
    "VIETNAM", "RUSSIA", "UNITED KINGDOM", "UNITED STATES",
]
SEGMENTS = ["AUTOMOBILE", "BUILDING", "FURNITURE", "MACHINERY", "HOUSEHOLD"]
PRIORITIES = ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"]
SHIPMODES = ["REG AIR", "AIR", "RAIL", "SHIP", "TRUCK", "MAIL", "FOB"]
SHIPINSTRUCT = ["DELIVER IN PERSON", "COLLECT COD", "NONE", "TAKE BACK RETURN"]
CONTAINERS = ["SM CASE", "SM BOX", "MED BAG", "MED BOX", "LG CASE", "LG DRUM"]
COLORS = ["almond", "antique", "aquamarine", "azure", "beige", "bisque", "black"]
TYPES = ["ANODIZED", "BURNISHED", "PLATED", "POLISHED", "BRUSHED"]
METALS = ["TIN", "STEEL", "BRASS", "COPPER", "NICKEL"]

rnd = random.Random(SEED)


def word(n):
    return "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz ") for _ in range(n)).strip() or "x"


def money(x):
    return f"{x:.2f}"


def d2s(d):
    return d.isoformat()


def write(name, rows):
    """写一个 .tbl 文件，返回行数。"""
    p = OUT / f"{name}.tbl"
    n = 0
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write("|".join(r))
            f.write("\n")
            n += 1
    print(f"  {name:<10} {n:>8,} 行  ->  {p.name}")
    return n


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"生成 TPC-H sf=0.1 数据到 {OUT}\n")

    # ---------- region / nation ----------
    write("region", (
        [str(i + 1), REGIONS[i], word(30)] for i in range(N_REGION)
    ))
    write("nation", (
        [str(i + 1), NATIONS[i], str(i // 5 + 1), word(40)] for i in range(N_NATION)
    ))

    # ---------- part（先把零售价存下来，lineitem 要用）----------
    prices = [0.0] * (N_PART + 1)

    def part_rows():
        for i in range(1, N_PART + 1):
            price = round(rnd.uniform(900, 2000), 2)
            prices[i] = price
            brand = f"Brand#{rnd.randint(1, 5)}{rnd.randint(1, 5)}"
            yield [
                str(i),
                f"{rnd.choice(COLORS)} {rnd.choice(METALS)} {rnd.choice(TYPES)} part {i}",
                f"Manufacturer#{rnd.randint(1, 5)}",
                brand,
                f"{rnd.choice(TYPES)} {rnd.choice(METALS)}",
                str(rnd.randint(1, 50)),
                rnd.choice(CONTAINERS),
                money(price),
                word(20),
            ]

    write("part", part_rows())

    # ---------- supplier ----------
    write("supplier", (
        [
            str(i),
            f"Supplier#{i:09d}",
            word(30),
            str(rnd.randint(1, N_NATION)),
            f"{rnd.randint(10, 99)}-{rnd.randint(100, 999)}-{rnd.randint(100, 999)}-{rnd.randint(1000, 9999)}",
            money(round(rnd.uniform(-999, 9999), 2)),
            word(60),
        ]
        for i in range(1, N_SUPPLIER + 1)
    ))

    # ---------- partsupp ----------
    def partsupp_rows():
        seen = set()
        while len(seen) < N_PARTSUPP:
            p = rnd.randint(1, N_PART)
            s = rnd.randint(1, N_SUPPLIER)
            if (p, s) in seen:
                continue
            seen.add((p, s))
            yield [
                str(p), str(s), str(rnd.randint(1, 9999)),
                money(round(prices[p] * rnd.uniform(0.5, 1.0), 2)), word(50),
            ]

    write("partsupp", partsupp_rows())

    # ---------- customer ----------
    write("customer", (
        [
            str(i),
            f"Customer#{i:09d}",
            word(30),
            str(rnd.randint(1, N_NATION)),
            f"{rnd.randint(10, 99)}-{rnd.randint(100, 999)}-{rnd.randint(100, 999)}-{rnd.randint(1000, 9999)}",
            money(round(rnd.uniform(-999, 9999), 2)),
            rnd.choice(SEGMENTS),
            word(50),
        ]
        for i in range(1, N_CUSTOMER + 1)
    ))

    # ---------- orders + lineitem（同一次遍历，订单总额要等明细算完）----------
    disc_choices = [i / 100 for i in range(0, 11)]   # 0.00 ~ 0.10
    tax_choices = [i / 100 for i in range(0, 9)]     # 0.00 ~ 0.08

    def orders_and_lineitem():
        for okey in range(1, N_ORDERS + 1):
            odate = D0 + timedelta(days=rnd.randint(0, SPAN))
            total = 0.0
            rows = []
            for ln in range(1, rnd.randint(1, 7) + 1):
                pkey = rnd.randint(1, N_PART)
                skey = rnd.randint(1, N_SUPPLIER)
                qty = rnd.randint(1, 50)
                ext = qty * prices[pkey]
                disc = rnd.choice(disc_choices)
                tax = rnd.choice(tax_choices)
                total += ext * (1 - disc) * (1 + tax)

                ship = odate + timedelta(days=rnd.randint(1, 121))
                commit = ship + timedelta(days=rnd.randint(1, 60))
                receipt = commit + timedelta(days=rnd.randint(1, 30))

                if ship < date(1995, 1, 1):
                    retflag, status = "R", "F"
                elif ship < date(1998, 1, 1):
                    retflag, status = "A", "F"
                else:
                    retflag, status = "N", "O"

                rows.append([
                    str(okey), str(pkey), str(skey), str(ln),
                    money(qty), money(round(ext, 2)), money(disc), money(tax),
                    retflag, status, d2s(ship), d2s(commit), d2s(receipt),
                    rnd.choice(SHIPINSTRUCT), rnd.choice(SHIPMODES), word(25),
                ])

            order = [
                str(okey),
                str(rnd.randint(1, N_CUSTOMER)),
                "O" if okey % 3 == 0 else "F",
                money(round(total, 2)),
                d2s(odate),
                rnd.choice(PRIORITIES),
                f"Clerk#{rnd.randint(1, 1000):09d}",
                "0",
                word(30),
            ]
            yield order, rows

    orders_path = OUT / "orders.tbl"
    lineitem_path = OUT / "lineitem.tbl"
    n_orders = n_lines = 0
    with open(orders_path, "w", encoding="utf-8", newline="\n") as fo, \
         open(lineitem_path, "w", encoding="utf-8", newline="\n") as fl:
        for order, rows in orders_and_lineitem():
            fo.write("|".join(order) + "\n")
            n_orders += 1
            for r in rows:
                fl.write("|".join(r) + "\n")
                n_lines += 1
    print(f"  {'orders':<10} {n_orders:>8,} 行  ->  orders.tbl")
    print(f"  {'lineitem':<10} {n_lines:>8,} 行  ->  lineitem.tbl")

    print("\n完成。下一步见 infra/README.md 的「导入」一节。")


if __name__ == "__main__":
    main()
