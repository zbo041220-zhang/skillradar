"""Day 6：用 pandas 统计技能出现率 Top N。

出现率 = 提到该技能的 JD 数 / 总 JD 数。
"""

from __future__ import annotations

import pandas as pd

from backend.db.database import engine


def top_skills(n: int = 10) -> tuple[pd.DataFrame, int]:
    """返回 (Top n 技能 DataFrame, 总 JD 数)。

    DataFrame 列：name、job_count（出现在多少个 JD 里）、rate（出现率）。
    """
    skills_df = pd.read_sql_query("SELECT name, job_id FROM skills", engine)
    total_jobs = int(
        pd.read_sql_query("SELECT count(*) AS c FROM jobs", engine)["c"].iloc[0]
    )

    appear = (
        skills_df.groupby("name")["job_id"]
        .nunique()
        .rename("job_count")
        .reset_index()
    )
    appear["rate"] = appear["job_count"] / total_jobs
    appear = appear.sort_values(
        ["job_count", "name"], ascending=[False, True]
    ).reset_index(drop=True)
    return appear.head(n), total_jobs


def print_top(n: int = 10) -> None:
    top, total = top_skills(n)
    print(f"共 {total} 条 JD，Top {len(top)} 技能：")
    print(f"{'排名':<4}{'技能':<22}{'出现岗位数':<10}{'出现率':<8}")
    for i, (_, row) in enumerate(top.iterrows(), 1):
        print(f"{i:<4}{row['name']:<22}{row['job_count']:<10}{row['rate']:.1%}")


if __name__ == "__main__":
    print_top(10)
