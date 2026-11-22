"""牛客网（nowcoder.com）职位爬虫 —— Day 2。

数据来源：社招职位列表页的服务端渲染数据 ``window.__INITIAL_STATE__``。
一个列表页即可拿到职位标题、公司名与完整 JD（岗位职责 + 岗位要求），
不需要单独请求详情页。

说明：国内站点直连即可，因此用 ``trust_env=False`` 跳过系统代理（Clash），
避免把国内请求绕去代理导致超时。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

FULLTIME_LIST_URL = "https://www.nowcoder.com/jobs/fulltime/center"

HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


@dataclass
class Job:
    """一条职位记录（Day 2 的中间结果，尚未入库）。"""

    company: str
    title: str
    jd_text: str
    url: str = ""


def _extract_initial_state(html: str) -> dict:
    """从页面 HTML 中解析 ``window.__INITIAL_STATE__`` 这个 JSON 对象。"""
    marker = "window.__INITIAL_STATE__="
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    raw = html[start:end].strip().rstrip(";").strip()
    return json.JSONDecoder().raw_decode(raw)[0]


def _company_name(data: dict) -> str:
    """从职位 data 中取公司名，兼容不同字段位置。"""
    rec = data.get("recommendInternCompany") or {}
    if isinstance(rec, dict):
        name = rec.get("companyName") or rec.get("companyShortName")
        if name:
            return name
    user = data.get("user") or {}
    for ident in user.get("identity") or []:
        if isinstance(ident, dict) and ident.get("companyName"):
            return ident["companyName"]
    return ""


def fetch_jobs(limit: int = 20) -> list[Job]:
    """抓取社招列表页，返回前 ``limit`` 条有效职位。"""
    resp = httpx.get(
        FULLTIME_LIST_URL,
        headers=HEADERS,
        timeout=20,
        follow_redirects=True,
        trust_env=False,
    )
    resp.raise_for_status()

    state = _extract_initial_state(resp.text)
    job_list = state["store"]["fulltimeCenter"]["jobList"]

    jobs: list[Job] = []
    for item in job_list:
        data = item.get("data") or {}
        title = data.get("jobName")
        if not title:  # 广告位 / 占位卡，没有真实职位
            continue

        ext = json.loads(data.get("ext") or "{}")
        parts = [
            (ext.get("infos") or "").strip(),
            (ext.get("requirements") or "").strip(),
        ]
        jd_text = "\n".join(p for p in parts if p)
        if not jd_text:  # 没有 JD 正文，跳过
            continue

        job_id = data.get("id")
        jobs.append(
            Job(
                company=_company_name(data),
                title=title,
                jd_text=jd_text,
                url=f"https://www.nowcoder.com/jobs/detail/{job_id}" if job_id else "",
            )
        )
        if len(jobs) >= limit:
            break

    return jobs


if __name__ == "__main__":
    result = fetch_jobs(limit=5)
    print(f"抓取到 {len(result)} 条有效 JD\n")
    for idx, job in enumerate(result, 1):
        print(f"===== 第 {idx} 条 =====")
        print(f"公司: {job.company}")
        print(f"岗位: {job.title}")
        print(f"链接: {job.url}")
        print(f"JD:\n{job.jd_text}")
        print()
