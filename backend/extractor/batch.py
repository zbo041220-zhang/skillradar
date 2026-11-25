"""Day 5 批量抽取：对 jobs 表所有 JD 跑 extract_skills，写入 skills 表。

用法：python -m backend.extractor.batch
"""

from __future__ import annotations

from sqlalchemy import delete, select

from backend.db.database import SessionLocal
from backend.db.models import Job, Skill
from backend.extractor.extract import extract_skills


def run_batch() -> tuple[int, int]:
    """清空 skills 后，对每条 JD 抽取技能并写入。返回 (JD 数, 技能数)。"""
    with SessionLocal() as session:
        jobs = session.execute(select(Job).order_by(Job.id)).scalars().all()
        # 清空旧结果，保证可重复运行
        session.execute(delete(Skill))
        total_skills = 0
        for j in jobs:
            for s in extract_skills(j.jd_text):
                session.add(
                    Skill(
                        job_id=j.id,
                        name=s.name,
                        category=s.category,
                        level=s.level,
                        required=s.required,
                    )
                )
                total_skills += 1
        session.commit()
    return len(jobs), total_skills


if __name__ == "__main__":
    n_jobs, n_skills = run_batch()
    print(f"处理 {n_jobs} 条 JD，抽取 {n_skills} 条技能")
