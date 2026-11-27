"""Day 9：给 FastAPI 接口用的统计函数（返回 JSON 友好结构）。"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import func, select

from backend.db.database import SessionLocal, engine
from backend.db.models import Job, Skill


def _jobs_count() -> int:
    with SessionLocal() as s:
        return int(s.execute(select(func.count()).select_from(Job)).scalar_one())


def top_skills(limit: int = 10, tier: str = "all") -> list[dict]:
    """技能 Top N + 出现率。tier: all / 大厂 / 小厂。"""
    if tier == "all":
        df = pd.read_sql_query("SELECT name, job_id FROM skills", engine)
        total = _jobs_count()
    else:
        df = pd.read_sql_query(
            "SELECT s.name, s.job_id, j.company_tier "
            "FROM skills s JOIN jobs j ON s.job_id = j.id",
            engine,
        )
        df = df[df["company_tier"] == tier]
        total = int(df["job_id"].nunique())

    appear = df.groupby("name")["job_id"].nunique().rename("count").reset_index()
    appear["rate"] = appear["count"] / total if total else 0
    appear = appear.sort_values(["count", "name"], ascending=[False, True]).head(limit)
    return [
        {"name": r["name"], "count": int(r["count"]), "rate": round(float(r["rate"]), 4)}
        for _, r in appear.iterrows()
    ]


def compare(limit: int = 10) -> dict[str, list[dict]]:
    """大厂 vs 小厂 技能 Top 对比。"""
    return {"大厂": top_skills(limit, "大厂"), "小厂": top_skills(limit, "小厂")}


def skill_level(name: str) -> dict:
    """某技能的 了解/熟悉/精通 分布。"""
    with SessionLocal() as s:
        rows = s.execute(
            select(Skill.level, func.count())
            .where(Skill.name == name)
            .group_by(Skill.level)
        ).all()
    total = sum(c for _, c in rows)
    dist = [
        {"level": lv, "count": c, "rate": round(c / total, 4) if total else 0.0}
        for lv, c in rows
    ]
    return {"name": name, "total": total, "distribution": dist}


def level_distribution() -> dict:
    """整体门槛分布（所有技能按 了解/熟悉/精通 计数）。"""
    with SessionLocal() as s:
        rows = s.execute(
            select(Skill.level, func.count())
            .group_by(Skill.level)
            .order_by(func.count().desc())
        ).all()
    total = sum(c for _, c in rows)
    dist = [
        {"level": lv, "count": c, "rate": round(c / total, 4) if total else 0.0}
        for lv, c in rows
    ]
    return {"total": total, "distribution": dist}


def meta() -> dict:
    """数据时点、样本量、来源（前端脚注用）。"""
    with SessionLocal() as s:
        jobs = int(s.execute(select(func.count()).select_from(Job)).scalar_one())
        skills = int(s.execute(select(func.count()).select_from(Skill)).scalar_one())
        latest = s.execute(select(func.max(Job.crawled_at))).scalar_one()
    return {
        "source": "牛客网（nowcoder.com）招聘职位列表，2026-11 快照",
        "jobs_count": jobs,
        "skills_count": skills,
        "crawled_at": latest.isoformat() if latest else None,
    }
