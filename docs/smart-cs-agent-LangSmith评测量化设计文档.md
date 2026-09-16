# smart-cs-agent · LangSmith 评测量化 · 设计

> **仓库**：`smart-cs-agent`（缩写 **SCA**）  
> **功能**：基于 LangSmith 的场景评测与指标沉淀（召回 / 路由 / 有据回答 / 延迟）  
> **文档类型**：功能设计 + 行动方案（L）  
> **状态**：待实现  
> **日期**：2026-09-15  
> **文件名**：`smart-cs-agent-LangSmith评测量化设计文档.md`  
> **关联**：  
> - [业务知识库与RAG调优设计文档](smart-cs-agent-业务知识库与RAG调优设计文档.md)（§5.3 必答题、§10 手测、§12 留痕）  
> - [多轮对话接入RAG设计文档](smart-cs-agent-多轮对话接入RAG设计文档.md)（路由 + 条件检索）  
> - [00-产品与范围](00-产品与范围.md) · [03-验收与手测](03-验收与手测.md) · [04-决策记录](04-决策记录.md)  
> - 题集真源（实现后）：`evals/cases_v1.csv`

---

## 0. 命名与维度

沿用：`{仓库名}-{功能}-设计文档.md`。

维度：背景 / 题集是否够全 / LangSmith 怎么用 / 指标定义 / 主流程 / 分期行动 / 完成定义 / 风险 / 留痕。

---

## 1. 背景与问题

### 现状

| 项 | 状态 |
|----|------|
| 智答云 canon + raw | 已落地；ingest 约 **129** chunks |
| 切分 | `CHUNK_SIZE=500` / `OVERLAP=100` |
| 路由 + 条件 RAG | 已落地 |
| `.env` LangSmith | 已预留 `LANGSMITH_TRACING` / `API_KEY` / `PROJECT=smart-cs-agent` |
| 量化 | **缺**：固定题集、打分口径、LangSmith 使用步骤、可写进简历的百分比 |

### 问题

1. 不知道 LangSmith 在本项目里「具体点哪里、跑什么」；  
2. 不清楚 §5.3 的 22 题 + FAQ35 **够不够、全不全**；  
3. 没有统一表结构，手测结果无法沉淀为可复现指标。

### 本设计立场

- **先有可打分的题集，再用 LangSmith 留痕与看延迟**；不是先上复杂自动评测平台。  
- 题集以设计文档 §5.3 为骨架，补 Tool/边界/口语，目标 **32～40 条**（简历够用）。  
- 一期以 **人工对照 + Trace 观测** 为主；LLM-as-judge 可选、非必须。

---

## 2. 目标与非目标

### 目标

| ID | 目标 |
|----|------|
| G1 | 明确题集规模与覆盖矩阵，回答「够不够、全不全」 |
| G2 | 给出本仓库可用的 **LangSmith 上手路径**（环境 → Trace → Dataset → 跑题 → 读数） |
| G3 | 定义 4 个核心指标：召回命中率、意图准确率、有据回答率、端到端延迟（P50/P95） |
| G4 | 产出可勾选行动清单；结果回写知识库设计文档 §12 与本文件留痕 |
| G5 | 题集落盘 `evals/cases_v1.csv`，与 §5.3 / FAQ 可追溯 |

### 非目标（本期）

| ID | 不做 |
|----|------|
| N1 | 自建评测微服务 / CI 强制卡点 |
| N2 | Rerank、Hybrid 检索（知识库设计已否决） |
| N3 | 线上真实用户流量 A/B |
| N4 | 必须上 LLM-as-judge（可选附录） |
| N5 | 把 LangSmith 写成「唯一验收方式」（无 Key 时仍可用 CSV 人工打分） |

---

## 3. 题够不够、全不全？（结论先行）

### 3.1 结论

| 问题 | 结论 |
|------|------|
| **§5.3 的 22 题够不够？** | **作骨架够，单独量化偏紧**。缺口语变体、天气/MCP、HITL、降级等工程题。 |
| **FAQ 35 条够不够？** | **作答案素材够**；不能直接当评测集（缺 intent/need_rag/工具期望字段）。 |
| **本期推荐规模** | **36 条**（下表固定清单）：政策 22 + 工程/边界 8 + 口语补强 6。 |
| **何时加到 50+？** | 面试深挖、或召回/意图指标不稳需要对抗题时再扩。 |

### 3.2 覆盖矩阵（必须勾满才算「全」）

| 桶 | 最少条数 | 覆盖什么 | 本期安排 |
|----|----------|----------|----------|
| B1 产品/套餐 | ≥3 | DOC01/02 | §5.3 #1～4 |
| B2 额度 | ≥3 | DOC03 | #5～7 + 口语「额度超了还能用吗」 |
| B3 成员权限 | ≥3 | DOC04 | #8～10 |
| B4 发票 | ≥2 | DOC05 | #11～12 |
| B5 退款 | ≥3 | DOC06 | #13～15 |
| B6 数据保留 | ≥2 | DOC07 | #16～17 |
| B7 企业/SLA/工单 | ≥3 | DOC08/09 | #18～20 |
| B8 边界防抢 Tool | ≥2 | ORD + 特批承诺 | #21～22 |
| B9 天气 | ≥1 | weather Tool | 补 |
| B10 路由防误检 | ≥1 | 单号 need_rag=false | 与 #21 合并可再加 ORD001 |
| B11 闲聊/记忆（可选） | ≥1 | chitchat | 补 1 条即可 |
| B12 MCP/HITL（可选） | ≥1 | 有 Key 再测 | 标记依赖环境 |

**判定「全」**：B1～B10 每桶 ≥ 最少条数；B11/B12 有则加分，无则简历不写 MCP 指标。

### 3.3 本期固定 36 条清单（实现时写入 CSV）

> 期望字段：`intent` / `need_rag` / `gold_keywords`（有据判定） / `expect_tool`（可空）

| id | 用户问题 | intent | need_rag | expect_tool | gold_keywords（含其一即可偏 Pass） | 来源 |
|----|----------|--------|----------|-------------|--------------------------------------|------|
| E01 | 智答云是做什么的？面向哪些客户？ | knowledge | true | | 知识管理；问答；团队 | §5.3#1 |
| E02 | 有哪些标准套餐？试用多久？ | knowledge | true | | 试用；基础；专业；企业；14 | §5.3#2 |
| E03 | 基础版和专业版分别多少钱？成员上限多少？ | knowledge | true | | 99；199；10；50 | §5.3#3 |
| E04 | 企业版是否一定支持私有化部署？ | knowledge | true | | 可选；单独签约；不是默认 | §5.3#4 |
| E05 | 基础版月度 API 额度多少？超额后会停用吗？ | knowledge | true | | 10000；不会停用；阶梯 | §5.3#5 |
| E06 | AI 问答额度和 API 额度是分开的吗？ | knowledge | true | | 分开；互不挪用 | §5.3#6 |
| E07 | 额度超了怎么恢复？会自动扣费续用吗？ | knowledge | true | | 重置；升级；AI 不自动；API 计费 | §5.3#7 |
| E08 | 基础版支持多少个正式成员？ | knowledge | true | | 10；已激活 | §5.3#8 |
| E09 | 外部协作者是否占用正式成员名额？ | knowledge | true | | 不占用；20；100 | §5.3#9 |
| E10 | 管理员能否删除审计日志？ | knowledge | true | | 不能；清空审计 | §5.3#10 |
| E11 | 是否支持专票？多久能开出来？ | knowledge | true | | 专票；1～3；工作日 | §5.3#11 |
| E12 | 发票抬头开错了怎么办？ | knowledge | true | | 红字；修改；工单 | §5.3#12 |
| E13 | 什么情况可以全额退款？什么情况不退？ | knowledge | true | | 7；自然日；10%；50% | §5.3#13 |
| E14 | 为什么我申请退款被拒了？ | knowledge | true | | 7；50%；红字；升级 | §5.3#14 |
| E15 | 退款多久能到账？ | knowledge | true | | 3～7；工作日 | §5.3#15 |
| E16 | 试用版到期后数据会立刻删除吗？ | knowledge | true | | 不会立刻；冻结；30 | §5.3#16 |
| E17 | 账号注销后数据怎么处理？ | knowledge | true | | 注销；所有者；转让 | §5.3#17 |
| E18 | 企业版有没有专属客户成功经理？有没有 SLA？ | knowledge | true | | CSM；合同；SLA | §5.3#18 |
| E19 | 普通工单和紧急问题大概多久响应？ | knowledge | true | | 1 个工作日；4 小时 | §5.3#19 |
| E20 | 知识库里的 SLA 能否直接当合同赔偿标准？ | knowledge | true | | 不能；合同为准 | §5.3#20 |
| E21 | 查一下订单 ORD002 | order | **false** | lookup_order | （状态以 Tool 为准） | §5.3#21 |
| E22 | 能不能多留一年数据并破例全额退？ | knowledge | true | | 无此承诺；人工；审批 | §5.3#22 |
| E23 | 额度超了还能用吗？ | knowledge | true | | API；AI；OCR；看类型 | 口语 |
| E24 | 基础版 API 超额后会停用吗？ | knowledge | true | | 不会；阶梯计费 | FAQ |
| E25 | 未使用的 AI 次数下个月还能用吗？ | knowledge | true | | 不结转；自然月 | FAQ |
| E26 | 专业版多少钱一个月？ | knowledge | true | | 199 | 口语 |
| E27 | 已开专票还想退款怎么办？ | knowledge | true | | 先红字；后退款 | 发票深化 |
| E28 | 北京今天天气怎么样 | weather | false | get_weather | （真实天气 Tool） | 工程 |
| E29 | 查订单 ORD001 状态 | order | false | lookup_order | | 防误检 |
| E30 | 工单 T001 处理到哪了 | ticket | false | lookup_ticket | | 防误检 |
| E31 | U001 还剩多少额度 | account | false | lookup_account | | 防误检+Tool |
| E32 | 你好 | chitchat | false | | 寒暄即可 | 闲聊 |
| E33 | 我想免费加人突破套餐上限 | knowledge/unknown | true | | 无承诺；人工 | 对抗 |
| E34 | SSO 改完角色为什么没马上生效？ | knowledge | true | | 15 分钟 | FAQ |
| E35 | （可选）搜索一下 AI 新闻 | mcp_news | false | search_google_news | 依赖 SERPER | 可选 |
| E36 | （可选）把报告发邮件到指定邮箱（HITL 确认） | mcp_news | false | send_email…+HITL | 依赖 SMTP；须确认提示 | 可选 |

**够用判定**：E01～E34 全部可跑且打分 → 足够写简历；E35～E36 环境具备再计入 MCP 指标。

---

## 4. LangSmith 怎么用（本仓库专用）

> 官方控制台：https://smith.langchain.com  
> 本仓项目名建议：`smart-cs-agent`（与 `.env` 的 `LANGSMITH_PROJECT` 一致）

### 4.1 一次配好环境

根目录 `.env`：

```env
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=smart-cs-agent
```

说明：

1. LangChain / LangGraph 在设置上述变量后，**调用模型时会自动上报 Trace**（本仓无需改业务代码即可看到对话链）。  
2. API Key 只放本地 `.env`，**禁止提交 git、禁止贴进设计文档正文**。  
3. 关闭追踪：`LANGSMITH_TRACING=false`。

### 4.2 你会用到的 4 个界面概念

| 概念 | 是什么 | 本方案怎么用 |
|------|--------|--------------|
| **Project** | 一组 Trace 的命名空间 | 固定 `smart-cs-agent` |
| **Trace** | 一次调用的树（模型、工具、耗时） | 每答一题产生 1～N 条；筛选 tag |
| **Dataset** | 输入/期望输出的题集 | 把 `evals/cases_v1.csv` 导入或手建 |
| **Experiment / Evaluation** | 对 Dataset 跑 Agent 并打分 | 一期可人工打分；二期再挂自动评价器 |

### 4.3 推荐上手路径（不写复杂 SDK 也能完成一期）

```text
① 确认 .env 追踪已开
② 终端跑：uv run python -m app.main --no-mcp
③ 按 cases 表逐题输入（每题可 /clear 避免串上下文）
④ 打开 LangSmith → Project「smart-cs-agent」→ 看到 Traces
⑤ 每条 Trace 记下：latency、是否调了工具、是否报错
⑥ 对照 CSV 人工填：intent对不对 / 召回有据 / Pass
⑦ 汇总出 3～4 个百分比 + P50/P95，写入本设计 §10 与知识库设计 §12
```

**可选加强（二期）**：

1. 在 LangSmith UI **Create Dataset**，名称 `sca-eval-v1`，把 E01～E34 的 `question` 做成 inputs。  
2. 用 SDK/`langchain` evaluator 批量跑（需另开实现任务，**本期不强制**）。  
3. 给每次评测 run 打 tag：`eval-v1`、`date=YYYYMMDD`，方便过滤。

### 4.4 Trace 里重点看什么

| 看点 | 对应指标 |
|------|----------|
| 整段耗时 | 端到端延迟 |
| 是否出现 tool 调用及名称 | 工具选择是否正确 |
| 错误 / 重试跨度 | 稳定性 |
| 输入里是否拼了检索片段（或上游路由日志） | 是否走了 RAG（配合终端 `need_rag=` 日志） |

> 路由日志目前在**终端打印**（`intent=` / `need_rag=`）。打分以终端为准；Trace 补延迟与工具。

### 4.5 无 LangSmith 时的降级

仍用同一张 CSV 人工打分，简历写「自建 N 条评测集」；不写 LangSmith 延迟即可。**题集与指标定义不变。**

---

## 5. 指标定义（统一打分口径）

### 5.1 召回命中率（仅 policy 题，E01～E20、E23～E27、E33～E34）

对每题执行 `retrieve(question)`（或看对话前注入片段）：

- **Pass**：Top-K 片段中出现 `gold_keywords` 至少 1 个关键组  
- **Fail**：未出现或明显跑题  

\[
\text{召回命中率} = \frac{\text{Pass}}{\text{政策题条数}}
\]

### 5.2 意图准确率（几乎全表）

对照终端路由日志的 `intent` 与表内期望（允许 `unknown`↔`knowledge` 在 need_rag=true 时记 **Partial**，汇总时可 0.5 或单独统计）。

### 5.3 业务防误检率（E21、E28～E31）

期望 `need_rag=false` 的题中，实际为 false 的比例。目标：**100%**。

### 5.4 有据回答率（政策题）

人工读最终答复：

- **Pass**：关键数字/结论与 canon 一致，且能在检索片段或知识库中找到依据  
- **Partial**：方向对但缺条件  
- **Fail**：编造或与 canon 冲突  

有据率只把 Pass 计入分子（Partial 可另报）。

### 5.5 工具正确率（E21、E28～E31、可选 E35～E36）

期望工具被调用（或 HITL 提示出现）；错类工具 → Fail。

### 5.6 延迟（LangSmith）

对 `eval-v1` 过滤后的 Trace：报告 **P50 / P95**（注明本地演示环境）。

### 5.7 简历建议只写 2～4 个数

示例模板（数字实测后填）：

> 自建 34 条场景评测（覆盖政策/路由/Tool）；意图准确率 xx%；单号类 need_rag=false 100%；政策有据率 xx%；LangSmith Trace P95 ≈ ys。

---

## 6. 主流程（每轮评测）

```text
准备：Milvus 已 ingest（129）+ demo_db + .env（模型 + LangSmith）
  → 打开 cases_v1.csv
  →（可选）LangSmith Project 确认有新 Trace
  → For 每题:
        /clear
        输入 question
        记录：路由日志、工具行、最终答、Trace latency
        填：route_ok / rag_hit / grounded / tool_ok
  → 汇总指标
  → 回写本设计 §10 + 知识库设计 §12 + 决策记录一行
```

---

## 7. 分期行动清单

### Phase A — 题集落盘

- [x] 创建目录 `evals/`  
- [x] 写入 `evals/cases_v1.csv`（E01～E36；E35～E36 标 optional）  
- [x] 自检覆盖矩阵 B1～B10 均满足最少条数  

### Phase B — LangSmith 连通

- [ ] 确认 `LANGSMITH_TRACING=true` 且 Key 有效  
- [ ] 跑 2 句对话，控制台能看到 Project 下新 Trace  
- [ ] 约定 tag：`eval-v1`（手工备注或后续脚本）  

### Phase C — 召回标定

- [ ] 对政策题跑 `retrieve`，算召回命中率  
- [ ] 按需微调 `MIN_SCORE` / `TOP_K`（改后须 `--recreate`）  
- [ ] 记录最终参数到知识库设计 §12  

### Phase D — 端到端打分

- [ ] `--no-mcp` 跑 E01～E34（E35～E36 按环境）  
- [ ] 填满 CSV 实际列；算意图 / 防误检 / 有据 / 工具  
- [ ] 从 LangSmith 取 P50/P95  

### Phase E — 留痕与简历句

- [ ] 更新本设计 §10 实测表  
- [ ] 更新知识库设计 Phase 5 勾选与 §12  
- [ ] 决策记录追加一行「评测 v1 结果」  

---

## 8. 完成定义（看见什么算做完）

| # | 看见什么 |
|---|----------|
| A | 存在 `evals/cases_v1.csv`，含 ≥34 条有效题与期望字段 |
| B | LangSmith 项目中有一批对应评测时间的 Traces（或文档注明降级未用 LS） |
| C | 写出至少：意图准确率、防误检率、有据率（召回率可选） |
| D | 知识库设计 §12 已更新参数与评测摘要 |
| E | 覆盖矩阵 B1～B10 无空桶 |

---

## 9. 风险与注意

| 风险 | 缓解 |
|------|------|
| 多轮串题导致记忆干扰 | 每题 `/clear` |
| LangSmith 费用/隐私 | 评测输入勿含真实客户隐私；可关 tracing |
| 只刷延迟不看有据 | 强制 grounded 人工列 |
| 题全是政策没有 Tool | 矩阵强制 B8～B10 |
| Key 泄露 | 仅 `.env`；轮换曾暴露的 Key |

---

## 10. 实测留痕（跑完后填）

| 项 | 值 |
|----|-----|
| 评测日期 | |
| 题集版本 | cases_v1 / N= |
| CHUNK / TOP_K / MIN_SCORE | 500 / 5 / 0.35（若有改填新值） |
| 召回命中率 | |
| 意图准确率 | |
| 业务防误检率 | |
| 有据回答率 | |
| 工具正确率 | |
| LangSmith P50 / P95 | |
| 主要失败题 id | |

---

## 11. 与知识库设计文档的关系

| 知识库设计 | 本方案 |
|------------|--------|
| §5.3 必答题 | → 本文件 E01～E22 |
| §10 手测 7 步 | → 嵌入 E05/E14/E09/E21/E28/E22 等，评测时一并覆盖 |
| Phase 5「30～50 条 + LangSmith」 | → 本文件落地为 36 条方案 + 操作步骤 |
| §12 留痕 | → Phase E 回写 |

---

## 12. 评审结论

- [ ] 同意本期题集 **36 条（有效至少 34）**，判定「够用且覆盖全」  
- [ ] 同意 LangSmith 一期以 **Trace 观测 + CSV 人工打分** 为主，不做强制自动 Evaluation  
- [ ] 同意指标集合：召回 / 意图 / 防误检 / 有据 /（延迟可选）  
- [ ] **批准进入 Phase A：生成 `evals/cases_v1.csv`**

评审备注：

```text
（填写）
```
