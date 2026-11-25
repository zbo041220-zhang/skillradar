"""牛客网（nowcoder.com）职位爬虫。

数据来源（都能拿到标题 + 公司 + 完整 JD）：
1. 列表页 SSR 的 ``window.__INITIAL_STATE__``：社招 / 实习 / 校招各第 1 页；
2. ``ai-recommend-job`` 接口：推荐流，每页 5 条，可翻页。

说明：国内站点直连即可，用 ``trust_env=False`` 跳过系统代理（Clash）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

FULLTIME_LIST_URL = "https://www.nowcoder.com/jobs/fulltime/center"
RECOMMEND_URL = "https://www.nowcoder.com/np-api/u/job/ai-recommend-job"

# 三个列表页（第 1 页 SSR 各约 20 条）
LIST_URLS = [
    "https://www.nowcoder.com/jobs/fulltime/center",
    "https://www.nowcoder.com/jobs/intern/center",
    "https://www.nowcoder.com/jobs/school/jobs",
]

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
    """一条职位记录。"""

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


def _parse_job_item(data: dict) -> Job | None:
    """把一条职位 data 转成 Job；广告位/空位/无 JD 返回 None。"""
    title = data.get("jobName")
    if not title:
        return None
    ext = json.loads(data.get("ext") or "{}")
    parts = [
        (ext.get("infos") or "").strip(),
        (ext.get("requirements") or "").strip(),
    ]
    jd_text = "\n".join(p for p in parts if p)
    if not jd_text:
        return None
    job_id = data.get("id")
    return Job(
        company=_company_name(data),
        title=title,
        jd_text=jd_text,
        url=f"https://www.nowcoder.com/jobs/detail/{job_id}" if job_id else "",
    )


def _job_list_from_state(state: dict) -> list[dict]:
    """从 __INITIAL_STATE__ 里找到职位列表（兼容 fulltimeCenter/interCenter/schoolCenter 等键）。"""
    store = state.get("store") or {}
    for val in store.values():
        if isinstance(val, dict) and isinstance(val.get("jobList"), list):
            return val["jobList"]
    return []


def fetch_list(url: str, limit: int = 20) -> list[Job]:
    """抓取一个列表页（SSR），返回有效职位。任何异常都返回空列表。"""
    try:
        resp = httpx.get(
            url, headers=HEADERS, timeout=20, follow_redirects=True, trust_env=False
        )
        resp.raise_for_status()
        state = _extract_initial_state(resp.text)
    except Exception:  # noqa: BLE001
        return []
    jobs: list[Job] = []
    for item in _job_list_from_state(state):
        job = _parse_job_item(item.get("data") or {})
        if job:
            jobs.append(job)
            if len(jobs) >= limit:
                break
    return jobs


def fetch_recommend(pages: int = 20) -> list[Job]:
    """抓取 ai-recommend-job 推荐流（每页约 5 条）。"""
    jobs: list[Job] = []
    rec_headers = {
        **HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Referer": FULLTIME_LIST_URL,
    }
    for page in range(1, pages + 1):
        try:
            resp = httpx.get(
                RECOMMEND_URL,
                headers=rec_headers,
                params={"recruitType": 3, "page": page, "pageSize": 20},
                timeout=20,
                follow_redirects=True,
                trust_env=False,
            )
            data = resp.json()
        except Exception:  # noqa: BLE001
            continue
        for item in data.get("data") or []:
            job = _parse_job_item(item)
            if job:
                jobs.append(job)
    return jobs


def gather_jobs(target: int = 100) -> list[Job]:
    """多来源凑数据，按 url 去重，返回至多 target 条。"""
    seen: set[str] = set()
    jobs: list[Job] = []

    def add(candidates: list[Job]) -> bool:
        for j in candidates:
            key = j.url or f"{j.company}|{j.title}"
            if key in seen:
                continue
            seen.add(key)
            jobs.append(j)
            if len(jobs) >= target:
                return True
        return False

    for url in LIST_URLS:
        if add(fetch_list(url)):
            return jobs[:target]
    add(fetch_recommend(pages=20))
    return jobs[:target]


def fetch_jobs(limit: int = 20) -> list[Job]:
    """兼容旧接口：抓社招列表。"""
    return fetch_list(FULLTIME_LIST_URL, limit=limit)


if __name__ == "__main__":
    result = gather_jobs(target=100)
    print(f"共凑到 {len(result)} 条有效 JD")
    for idx, job in enumerate(result[:5], 1):
        print(f"  {idx}. [{job.title}] @ {job.company}")
