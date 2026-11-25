"""Day 4 验证：从 jobs 表取 3 条 JD，跑技能抽取并打印。"""

from __future__ import annotations

from sqlalchemy import select

from backend.db.database import SessionLocal
from backend.db.models import Job
from backend.extractor.extract import extract_skills


def main() -> None:
    with SessionLocal() as session:
        jobs = session.execute(select(Job).order_by(Job.id).limit(3)).scalars().all()

    print(f"共取到 {len(jobs)} 条 JD\n")
    for j in jobs:
        print(f"===== [{j.title}] @ {j.company} (id={j.id}) =====")
        skills = extract_skills(j.jd_text)
        if not skills:
            print("  （没抽出技能）")
        for s in skills:
            print(f"  - {s.name} | {s.category} | {s.level} | 必选={s.required}")
        print()


if __name__ == "__main__":
    main()
