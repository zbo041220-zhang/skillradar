"""Day 7：大厂/小厂对比 + 门槛（level）分布。

公司分级：静态名单标大厂，其余标小厂（计划第 5 节）。
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import select

from backend.db.database import SessionLocal, engine
from backend.db.models import Job

BIG_COMPANIES = [
    "腾讯", "字节", "阿里", "百度", "快手", "美团", "小米", "华为",
    "京东", "网易", "拼多多", "滴滴", "小红书", "蚂蚁", "哔哩哔哩",
    "携程", "微博", "商汤", "旷视", "科大讯飞", "大疆", "蔚来", "小鹏",
    "理想", "比亚迪", "海康威视", "中兴", "联想", "OPPO", "vivo", "荣耀",
]


def classify_tiers() -> tuple[int, int]:
    """按静态名单给 jobs 填 company_tier，返回 (大厂数, 小厂数)。"""
    big = small = 0
    with SessionLocal() as session:
        jobs = session.execute(select(Job)).scalars().all()
        for j in jobs:
            j.company_tier = (
                "大厂" if any(k in j.company for k in BIG_COMPANIES) else "小厂"
            )
            if j.company_tier == "大厂":
                big += 1
            else:
                small += 1
        session.commit()
    return big, small


def top_skills_by_tier(n: int = 10) -> dict[str, tuple[pd.DataFrame, int]]:
    """返回 {大厂/小厂: (Top n 技能 DataFrame, 该组 JD 数)}。"""
    df = pd.read_sql_query(
        "SELECT s.name, s.job_id, j.company_tier "
        "FROM skills s JOIN jobs j ON s.job_id = j.id",
        engine,
    )
    result: dict[str, tuple[pd.DataFrame, int]] = {}
    for tier in ("大厂", "小厂"):
        tier_df = df[df["company_tier"] == tier]
        total = int(tier_df["job_id"].nunique())
        appear = (
            tier_df.groupby("name")["job_id"]
            .nunique()
            .rename("job_count")
            .reset_index()
        )
        appear["rate"] = appear["job_count"] / total if total else 0
        appear = appear.sort_values(
            ["job_count", "name"], ascending=[False, True]
        ).head(n).reset_index(drop=True)
        result[tier] = (appear, total)
    return result


def level_distribution() -> pd.DataFrame:
    """技能按 level 分布（门槛）。"""
    return pd.read_sql_query(
        "SELECT level, count(*) AS cnt FROM skills GROUP BY level ORDER BY cnt DESC",
        engine,
    )


def print_report(n: int = 10) -> None:
    big, small = classify_tiers()
    print(f"公司分级：大厂 {big} 家，小厂 {small} 家\n")

    tiers = top_skills_by_tier(n)
    for tier in ("大厂", "小厂"):
        top, total = tiers[tier]
        print(f"===== {tier} Top {n}（共 {total} 条 JD）=====")
        print(f"{'排名':<4}{'技能':<22}{'出现岗位数':<10}{'出现率':<8}")
        for i, (_, row) in enumerate(top.iterrows(), 1):
            print(f"{i:<4}{row['name']:<22}{row['job_count']:<10}{row['rate']:.1%}")
        print()

    print("===== 门槛分布（level）=====")
    lv = level_distribution()
    total = int(lv["cnt"].sum())
    for _, row in lv.iterrows():
        print(f"  {row['level']:<6}{row['cnt']:<6}{row['cnt'] / total:.1%}")


if __name__ == "__main__":
    print_report(10)
