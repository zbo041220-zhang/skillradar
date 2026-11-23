"""SQLAlchemy 数据模型。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Job(Base):
    """职位表（对应计划第 5 节的 jobs 表）。"""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    # 大厂 / 小厂：Day 7 用静态名单回填，Day 3 先留空
    company_tier: Mapped[str | None] = mapped_column(Text, nullable=True)
    jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
