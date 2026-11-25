"""调用 DeepSeek 从 JD 抽取技能（Day 4 第一版）。

用法：from backend.extractor.extract import extract_skills
      skills = extract_skills(jd_text)  -> list[Skill]
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = "deepseek-chat"


@dataclass
class Skill:
    """一条技能抽取结果（对应计划 skills 表的字段）。"""

    name: str
    category: str  # 模型 / 框架 / 工程 / 软技能
    level: str     # 了解 / 熟悉 / 精通
    required: bool  # 必选 True / 加分 False


SYSTEM_PROMPT = """你是招聘 JD 技能解析专家。给定一条职位描述（JD），抽取该岗位要求的技能，并：
1. 把技能名标准化（例如「熟悉大模型」「用过 langchain」→ 大模型 / LangChain）；
2. 归类到：模型 / 框架 / 工程 / 软技能 四类之一；
3. 判定要求程度：了解 / 熟悉 / 精通；
4. 判定是否必选：true=必选（明确要求、负责、精通、掌握），false=加分（优先、加分、了解、可选、有经验者优先）。

只输出一个 JSON 对象，不要输出任何其它文字，格式：
{"skills": [{"name": "技能名", "category": "模型", "level": "熟悉", "required": true}]}

示例输入：「负责大语言模型微调与部署，熟悉 PyTorch 和 Transformers；了解 RAG，有 Agent 开发经验者优先；具备良好沟通能力。」
示例输出：
{"skills": [
  {"name": "大语言模型", "category": "模型", "level": "熟悉", "required": true},
  {"name": "PyTorch", "category": "框架", "level": "熟悉", "required": true},
  {"name": "Transformers", "category": "框架", "level": "熟悉", "required": true},
  {"name": "RAG", "category": "模型", "level": "了解", "required": false},
  {"name": "Agent", "category": "模型", "level": "了解", "required": false},
  {"name": "沟通能力", "category": "软技能", "level": "熟悉", "required": true}
]}"""


def _client() -> OpenAI:
    if not API_KEY:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY，请在项目根目录 .env 里配置")
    # 国内直连，不走系统代理（Clash），避免被绕到国外节点导致超时
    http_client = httpx.Client(trust_env=False, timeout=60)
    return OpenAI(api_key=API_KEY, base_url=BASE_URL, http_client=http_client)


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "是", "必选")
    return bool(value)


def extract_skills(jd_text: str) -> list[Skill]:
    """从一条 JD 文本抽取技能列表。"""
    client = _client()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": jd_text},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = resp.choices[0].message.content
    data = json.loads(content or "{}")

    skills: list[Skill] = []
    for item in data.get("skills", []):
        name = (item.get("name") or "").strip()
        if not name:
            continue
        skills.append(
            Skill(
                name=name,
                category=(item.get("category") or "").strip(),
                level=(item.get("level") or "").strip(),
                required=_to_bool(item.get("required", False)),
            )
        )
    return skills
