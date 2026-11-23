"""把牛客爬取的数据写入 jobs 表：python -m backend.db.load_jobs"""

from __future__ import annotations

from ..crawler.nowcoder import fetch_jobs
from .database import SessionLocal
from .models import Job


def load(limit: int = 20) -> int:
    """抓取牛客社招列表，写入 jobs 表，返回写入条数。"""
    jobs = fetch_jobs(limit=limit)
    with SessionLocal() as session:
        count = 0
        for j in jobs:
            session.add(Job(company=j.company, title=j.title, jd_text=j.jd_text))
            count += 1
        session.commit()
    return count


if __name__ == "__main__":
    n = load(limit=20)
    print(f"已写入 {n} 条到 jobs 表")
