"""把牛客爬取的数据写入 jobs 表（按 公司+岗位 去重）。

用法：python -m backend.db.load_jobs
"""

from __future__ import annotations

from sqlalchemy import select

from ..crawler.nowcoder import gather_jobs
from .database import SessionLocal
from .models import Job


def load(target: int = 100) -> int:
    """凑约 target 条 JD 写入 jobs 表，跳过已存在的（公司+岗位 相同），返回新增条数。"""
    jobs = gather_jobs(target=target)
    with SessionLocal() as session:
        existing = {
            (j.company, j.title) for j in session.execute(select(Job)).scalars().all()
        }
        added = 0
        for j in jobs:
            key = (j.company, j.title)
            if key in existing:
                continue
            session.add(Job(company=j.company, title=j.title, jd_text=j.jd_text))
            existing.add(key)
            added += 1
        session.commit()
    return added


if __name__ == "__main__":
    n = load(target=100)
    print(f"新增 {n} 条到 jobs 表")
