"""BOSS直聘 半手动爬虫（Playwright CDP 附加到你的 Chrome，自动检测模式）。

为什么「附加」而不是让 Playwright 自己开浏览器：
让 Playwright 开的浏览器带自动化痕迹，BOSS 直聘会识别出来、页面反复跳转。
附加到你手动打开的 Chrome（调试端口）后，浏览器是 100% 真实的，Playwright
只负责从外面读页面、抽数据。

自动检测模式：脚本连上 Chrome 后，每 2 秒检查一次页面，一旦发现职位卡片
就立即抽取并保存，不用手动卡时机。

使用步骤（需要两个终端窗口）：
  终端 A（启动调试 Chrome，会弹出干净的 Chrome 窗口）：
      & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=D:\chrome-cdp
  在这个 Chrome 里：登录 BOSS直聘（建议扫码登录）→ 搜索「大模型」→
  让职位列表加载出来，保持这个页面在最前面。

  终端 B（跑本脚本）：
      cd D:\SkillRadar_project
      .\.venv\Scripts\python.exe backend\crawler\boss_playwright.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import Browser, Page, sync_playwright

CDP_URL = "http://127.0.0.1:9222"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "boss_jobs.json"
WAIT_SECONDS = 120


def _first_text(page: Page, selectors: list[str]) -> str:
    """依次尝试多个选择器，返回第一个非空文本；都失败返回空串。"""
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el is None:
                continue
            text = el.inner_text().strip()
            if text:
                return text
        except Exception:  # noqa: BLE001
            continue
    return ""


def extract_cards(page: Page) -> list[dict[str, str]]:
    """抽取列表页的职位卡片（标题/公司/薪资/地区/简介）。"""
    cards = page.query_selector_all(
        "li.job-card-wrapper, .job-list-box li, ul.job-list-box li"
    )
    results: list[dict[str, str]] = []
    for card in cards:
        title = _first_text(card, [".job-name", ".job-title", ".name"])  # type: ignore[arg-type]
        company = _first_text(card, [".company-name", ".boss-name"])  # type: ignore[arg-type]
        salary = _first_text(card, [".salary"])  # type: ignore[arg-type]
        area = _first_text(card, [".job-area"])  # type: ignore[arg-type]
        desc = _first_text(card, [".info-desc", ".job-info"])  # type: ignore[arg-type]
        if title:
            results.append(
                {
                    "title": title,
                    "company": company,
                    "salary": salary,
                    "area": area,
                    "desc": desc,
                }
            )
    return results


def find_boss_page(browser: Browser) -> Page | None:
    """在当前 Chrome 里找 BOSS直聘页面（每次现找，防止旧页面对象失效）。"""
    for ctx in browser.contexts:
        for pg in ctx.pages:
            try:
                if "zhipin.com" in pg.url:
                    return pg
            except Exception:  # noqa: BLE001
                continue
    return None


def extract_and_save(page: Page) -> list[dict[str, str]]:
    """保存当前页面 HTML 并抽取职位卡片。"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    html_path = OUT_PATH.parent / "boss_page.html"
    html_path.write_text(page.content(), encoding="utf-8")

    jobs = extract_cards(page)
    print(f"共抽取到 {len(jobs)} 条职位：")
    for j in jobs:
        print(f"  - {j['title']} | {j['company']} | {j['salary']} | {j['area']}")

    OUT_PATH.write_text(
        json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n页面 HTML 已存到 {html_path}")
    print(f"结果已保存到 {OUT_PATH}")
    return jobs


def main() -> None:
    # 临时目录指到 D 盘：本机 C:\...\Temp 有权限问题（mkdtemp EPERM）
    _tmp_dir = Path(__file__).resolve().parents[2] / ".tmp"
    _tmp_dir.mkdir(exist_ok=True)
    os.environ["TMP"] = str(_tmp_dir)
    os.environ["TEMP"] = str(_tmp_dir)
    tempfile.tempdir = str(_tmp_dir)

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception:  # noqa: BLE001
            print("=" * 60)
            print("没有连上调试模式的 Chrome。请先在另一个终端运行：")
            print(f'  & "{CHROME_PATH}" --remote-debugging-port=9222 --user-data-dir=D:\\chrome-cdp')
            print()
            print("然后在这个 Chrome 里：登录 BOSS直聘 → 搜「大模型」→ 等列表加载。")
            print("保持 Chrome 开着，重新运行本脚本。")
            sys.exit(1)

        print("=" * 60)
        print("已连上你的 Chrome。")
        print("请把 BOSS直聘的「职位列表页」保持在浏览器最前面。")
        print(f"脚本会自动检测，一旦发现职位卡片立即抽取（最多等 {WAIT_SECONDS} 秒）...")

        deadline = time.time() + WAIT_SECONDS
        while time.time() < deadline:
            page = find_boss_page(browser)
            if page is None:
                print("  [等待] 还没找到 BOSS 页面...")
                time.sleep(2)
                continue
            try:
                if extract_cards(page):
                    try:
                        extract_and_save(page)
                        return
                    except Exception as e:  # noqa: BLE001
                        print(f"  [等待] 保存时出错（{type(e).__name__}），重试...")
                        continue
                print(f"  [等待] 当前页面没检测到职位卡片（{page.url[:70]}）")
            except Exception as e:  # noqa: BLE001
                print(f"  [等待] 检测出错（{type(e).__name__}），继续...")
            time.sleep(2)

        print("\n等待超时，没检测到职位列表。请确认：")
        print("  1) 已登录 BOSS直聘；")
        print("  2) 搜索页能看到职位卡片（不是空白/转圈/被踢回登录）；")
        print("  3) 调试 Chrome 还开着。")
        print("确认后重新运行脚本。")


if __name__ == "__main__":
    main()
