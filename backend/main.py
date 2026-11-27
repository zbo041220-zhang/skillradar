"""SkillRadar 后端入口（FastAPI）。

运行：在项目根目录执行
    .\\.venv\\Scripts\\python.exe -m uvicorn backend.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.analyzer.stats import compare, level_distribution, meta, skill_level, top_skills

app = FastAPI(title="SkillRadar", version="0.1.0")

# 允许前端（Vite dev 在 5173 端口）跨域访问；部署时再收紧
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def hello() -> dict[str, str]:
    """欢迎语，确认服务能跑起来。"""
    return {"message": "SkillRadar 后端已就绪"}


@app.get("/skills/top")
def skills_top(limit: int = 10, tier: str = "all") -> dict:
    """技能 Top N + 出现率。tier: all / 大厂 / 小厂。"""
    return {"data": top_skills(limit=limit, tier=tier)}


@app.get("/skills/compare")
def skills_compare(limit: int = 10) -> dict:
    """大厂 vs 小厂 技能 Top 对比。"""
    return {"data": compare(limit=limit)}


@app.get("/skills/level")
def skills_level(name: str | None = None) -> dict:
    """技能的 了解/熟悉/精通 分布；不带 name 时返回整体门槛分布。"""
    if name:
        return {"data": skill_level(name)}
    return {"data": level_distribution()}


@app.get("/meta")
def get_meta() -> dict:
    """数据时点、样本量、来源（前端脚注用）。"""
    return {"data": meta()}
