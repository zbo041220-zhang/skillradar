# AGENTS.md — SkillRadar

## 这个项目是什么

《AI 岗位技能雷达》：爬招聘 JD → LLM 抽取技能 → pandas 分析 → FastAPI + Vue 展示 → 公网部署。
**求职作品**，不是要长期运营的产品。

## 先读什么

1. **`PROJECT_PLAN.md`** —— 唯一施工口径：定位、技术栈、数据模型、API、决策记录、15 天计划、验收标准。
2. **本文件** —— 纪律与环境。

冲突时以 `PROJECT_PLAN.md` 为准；文档没写的，问用户，不要自己发明。

## 工作方式

- **一天一个目标**，做完当天 commit 一次
- 目标与验收标准见 `PROJECT_PLAN.md` 第 9 节
- 某天卡住超过 2 小时 → 跳过，先做后面的，别死磕
- 要改计划（加功能、改技术选型）先说明理由，等用户确认

## 硬性边界（MVP）

**做**：一个页面 —— 技能 Top10 榜单 + 大厂/小厂对比 + 门槛分布 + 数据来源脚注。

**不做**：登录注册、搜索、后台管理、日更、面经模块、「趋势」（单次快照做不了）。

## 开发环境（2026-11-21 确认）

| 项 | 状态 |
|---|---|
| Python | 3.13.7 |
| uvicorn | 0.50.0（已装） |
| PostgreSQL | **18**，装在 `D:\PostgreSQL`，服务名 `postgresql-x64-18`（运行中） |
| psql | 不在 PATH，用 `D:\PostgreSQL\bin\psql.exe` |
| 数据库连接 | 待建库时确认（用户提供密码） |
| Node / npm | v24.19.0 / 12.0.2 |
| LLM | DeepSeek API（OpenAI 兼容），key 放 `.env`，**绝不提交** |
| git 代理 | `http://127.0.0.1:7897`（Clash）。Clash 关了 push 会失败 |
| 仓库 | https://github.com/zbo041220-zhang/skillradar |

**代理取消命令**（Clash 关闭时用）：
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

## 代码约定

- Python 函数写类型标注；目录按 `crawler / extractor / analyzer / db / api` 分层
- 原始 JD 数据放 `backend/data/`（已在 `.gitignore`）
- 一个 commit 只做一件事，message 用 `feat: / fix: / docs: / chore:`

## 交流

- **中文**
- 用户是初学者（Vue 不熟），**一步一步来**，别一次给几百行代码
- 先给最小可运行版本，跑通再迭代
- 报错信息优先于猜测：先看日志，再改代码

## 当前状态

Day 0 完成：仓库已建、计划已定稿、git 已配代理。
下一次从 **Day 1（搭骨架）** 开始。
