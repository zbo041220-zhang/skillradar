"""SkillRadar 后端入口（Day 1：最小可运行 hello 接口）。"""

from fastapi import FastAPI

app = FastAPI(title="SkillRadar", version="0.1.0")


@app.get("/")
def hello() -> dict[str, str]:
    """Day 1 验收用：返回一句欢迎语，确认服务能跑起来。"""
    return {"message": "SkillRadar 后端已就绪"}
