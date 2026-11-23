"""建表脚本：python -m backend.db.init_db"""

from __future__ import annotations

from . import models  # noqa: F401  # 导入以注册模型
from .database import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("建表完成")
