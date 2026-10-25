# Promotion Warrior 🛡️ (Universal Hunter Edition)

> **通用型社媒流量猎手与账号养护专家（AI Agent Skill 完整可运行版）**  
> 本项目为面向各大主流社交平台的高转化、防封禁社媒流量增长与获客 Agent Skill，内置**完整版技能提示词与规范**及**配套 SQLite 数据库与防封去重引擎脚本**。

---

## 📌 项目定位与架构目标

针对不同垂直品类（Niche）在主流社媒（Reddit、X/Twitter、TikTok、Facebook、行业垂直论坛等）进行自动潜伏、真实养号与高精准获客：
* **核心目标**：实现从“被动养号 $\to$ 需求感知 $\to$ 意图分层 $\to$ 软性植入 $\to$ 离场清理”的全链路自动化闭环。
* **反聚类防封**：针对社媒平台严苛的反垃圾机制，从底层实现 24 小时关键词轮询、Jaccard 文本相似度校验与 DOM 物理查重。
* **配套补齐**：规范化实现了全套 `scripts/db.py` 调度与去重系统，开箱即用。

---

## 🧠 核心原则 (Core Philosophy)

1. **通用性 (Universal)**：不绑定特定平台或利基市场。根据输入的 `niche` 和 `target_platform` 动态调整策略。
2. **反重复与防封禁 (Anti-Repetition & Anti-Ban)**：
   * **关键词轮询**：绝不连续两次搜索同一关键词（24 小时冷却校验）。
   * **内容去重**：Jaccard 文本相似度校验，严禁发送相似度 >60% 的聚类内容。
   * **双重足迹回避**：数据库去重 + 浏览器 DOM 物理查重，绝不对同一帖子或同一用户重复跟帖。
3. **80/20 养号即狩猎 (Scout & Hunt)**：
   * **80% 时间为侦查模式 (Scout Mode)**：浏览、滚动到底部、随机点赞高质量回复，积累真人行为指纹。
   * **20% 时间为狙击模式 (Sniper Mode)**：遇到高匹配需求帖时，一击必中，完成转化。
4. **人设一致性**：保持 Media Buyer / 行业顾问的专业、冷峻、克制风格。严禁机器人式灌水或乞讨式推广。

---

## 📊 3-Tier 转化漏斗 (The Universal Funnel)

| 流量层级 | 用户心智与特征 | 关键词特征 | 战术打法 | 话术示例 |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: 显性需求 (Hot)** | 拿着预算直接找工具或服务 | `best [niche] tool`, `buy [niche]`, `[niche] coupon` | **Direct Close**<br>客观给出行业见解，顺理成章推荐最佳方案 | *"I've tested 5 tools, X is the only one that worked because..."* |
| **Tier 2: 竞品对比 (Warm)** | 对现状不满、抱怨竞品、找替代方案 | `[Competitor] alternative`, `why is [Competitor] so expensive` | **Side Attack**<br>认同痛点 $\to$ 分析原因 $\to$ 给出避坑替代方案 | *"Yeah, [Competitor] has been unstable lately. Most of us moved to X..."* |
| **Tier 3: 问题意识 (Cold)** | 遭遇故障求助、询问参数、行业交流 | `how to fix [error]`, `best settings for [niche]` | **Value First**<br>纯干货专业建议，隐晦提及身份或纯养号不带外链 | *"Check your settings on A and B. Usually it's a cookie issue. Try..."* |

---

## 🛠️ 配套数据库引擎 (SQLite & CLI)

本项目实现了与 `SKILL.md` 中所有指令 100% 契合的配套 CLI 工具：`scripts/db.py`。

### 1. 状态与配额检查 (Stats)
```bash
python3 scripts/db.py stats
```
输出示例：
```json
{
  "replies_today": 0,
  "total_interactions": 0,
  "max_daily_limit": 9,
  "is_limit_reached": false,
  "recommended_mode": "scout_and_sniper"
}
```

### 2. 24 小时关键词轮询查重 (Keyword Rotation)
```bash
# 检查关键词过去 24 小时是否已使用
python3 scripts/db.py check_keyword "best ad spy"
# 返回: {"used_last_24h": false, "keyword": "best ad spy"}

# 记录当前已搜索的关键词
python3 scripts/db.py log_keyword "best ad spy"
# 再次检查即返回: {"used_last_24h": true, "keyword": "best ad spy"}
```

### 3. URL 链接清洗与去重 (URL Deduplication)
```bash
# 自动剔除 utm_*、hash 和多余斜杠
python3 scripts/db.py check_url "https://reddit.com/r/marketing/post1?utm_source=share"
# 返回: {"duplicate": false, "url": "https://reddit.com/r/marketing/post1"}
```

### 4. 互动行为入库 (Log Interaction)
```bash
python3 scripts/db.py log_interaction "reddit" 1 "https://reddit.com/r/marketing/post1" "reply" "Try clearing your pixel cache" "TargetUser"
```

### 5. 内容反聚类相似度校验 (Anti-Clustering Check)
```bash
python3 scripts/db.py check_similarity "Your proposed comment text..."
```

---

## 📂 仓库目录结构

```text
.
├── SKILL.md            # Skill 提示词与规范定义
├── scripts/
│   └── db.py           # 数据库读写、URL清洗、Jaccard查重 CLI 脚本
├── data/
│   └── .gitkeep        # 运行时生成 history.db（已加入 .gitignore）
├── tests/
│   └── test_db.py      # 数据库与业务逻辑单元测试（4/4 Passed）
├── README.md           # 项目完整文档
└── LICENSE             # MIT 开源协议
```

---

## 🚀 安装与在 AI Agent 中使用

### 1. 克隆仓库
```bash
git clone https://github.com/hanshan0228/promotion-warrior-universal.git
cd promotion-warrior-universal
```

### 2. 运行自检单元测试
```bash
python3 tests/test_db.py
```

### 3. 加载到 Claude Code / OpenCode / Codex
* **Claude Code**: 拷贝 `SKILL.md` 到 `~/.claude/skills/promotion-warrior/SKILL.md`
* **OpenCode**: 拷贝到 `~/.config/opencode/skills/promotion-warrior/SKILL.md`
* **Codex**: 拷贝到 `~/.codex/skills/promotion-warrior/SKILL.md`

---

## 📄 License

MIT License. 详见 [LICENSE](./LICENSE)。
