# 🤖 Telegram ↔ Cloud Autonomous AI Agent (Gemini 3.8 Flash)

<p align="center">
  <a href="https://github.com/Sumblink182/tg-ai-bot/stargazers"><img src="https://img.shields.io/github/stars/Sumblink182/tg-ai-bot?color=yellow&logo=github" alt="GitHub Stars"></a>
  <a href="https://github.com/Sumblink182/tg-ai-bot/network/members"><img src="https://img.shields.io/github/forks/Sumblink182/tg-ai-bot?color=blue&logo=github" alt="GitHub Forks"></a>
  <a href="https://github.com/Sumblink182/tg-ai-bot/issues"><img src="https://img.shields.io/github/issues/Sumblink182/tg-ai-bot?color=red" alt="GitHub Issues"></a>
  <a href="https://core.telegram.org/bots/api"><img src="https://img.shields.io/badge/Telegram-Bot%20API-blue.svg?logo=telegram" alt="Telegram Bot API"></a>
  <a href="https://deepmind.google/technologies/gemini/"><img src="https://img.shields.io/badge/Model-Gemini%203.8%20Flash%20(High)-orange.svg?logo=google" alt="Gemini 3.8 Flash"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
</p>

<p align="center">
  <b>你的 24 小时云端驻留通用自主智能体 (Personal Autonomous Agent)。</b><br>
  以 Linux 服务器为物理具身与手脚，以 Telegram 为随身交互中枢。<br>
  💡 <b>零 API 成本</b> | 🧠 <b>原生深度推理</b> | 🛠️ <b>全自主代码/数据/系统接管</b> | 🛡️ <b>100% 私有化自建</b> | ⚡ <b>内存仅 ~20MB</b>
</p>

---

## 🛡️ 100% 私有化自建架构 (Self-Hosted & Privacy First)

> [!IMPORTANT]
> **关于部署形态说明**：
> 本项目为 **100% 独立开源私有化架构**，**无任何中心化第三方服务器收集你的数据**。
> 每位使用者都在自己的 Linux VPS 上运行专属进程，并通过 Telegram [@BotFather](https://t.me/BotFather) 绑定属于自己的独立 Bot Token 与白名单 ID。
> 你的会话历史、系统命令与数据隐私完全封闭在自己的服务器内部，拥有绝对的数据主权！

```mermaid
graph LR
    subgraph 独立私有环境 A
        UserA[用户 A (Telegram)] --> BotA[用户 A 专属机器人] --> VPSA[用户 A 的 VPS 宿主机]
    end

    subgraph 独立私有环境 B
        UserB[用户 B (Telegram)] --> BotB[用户 B 专属机器人] --> VPSB[用户 B 的 VPS 宿主机]
    end

    subgraph 独立私有环境 C
        UserC[用户 C (Telegram)] --> BotC[用户 C 专属机器人] --> VPSC[用户 C 的 VPS 宿主机]
    end
```

---

## 📋 极简前置准备（Prerequisites，仅需 1 分钟）

在运行一键安装脚本前，只需完成以下两项极简准备：

### 1️⃣ 安装并认证 Google Antigravity CLI
本项目复用 Antigravity 原生免 API Key 调取 **Gemini 3.8 Flash** 并赋予系统执行力。在你的 Linux 终端执行：
```bash
# 安装官方 CLI 客户端
curl -fsSL https://antigravity.google/install.sh | bash

# 终端输入 agy 完成一次 Google 账号认证登录（终端会打印授权链接，浏览器点一下即可）
agy
```

### 2️⃣ 获取你的专属 Telegram Bot Token
1. 在 Telegram 搜索 [@BotFather](https://t.me/BotFather) 并发送 `/newbot`。
2. 按照提示输入机器人名字和用户名（以 `bot` 结尾）。
3. 复制生成的 HTTP API Token（形如 `123456789:ABCdef...`）。

---

## ⚡ 极速一键自建安装 (One-click Install)

完成上述前置后，在你的 Linux VPS（Ubuntu / Debian）上直接执行：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Sumblink182/tg-ai-bot/main/install.sh)
```
根据交互提示粘贴你的 Bot Token，脚本将自动完成依赖安装、环境配置与 systemd 开机自启守护！

---

## 🌟 核心理念：从“聊天玩具”到“全能云端具身 Agent”

市面上绝大多数 Telegram AI 机器人只是“纸上谈兵的聊天玩具”，只能给出文字建议，却无法替你完成任何真实的计算机任务。

而本项目通过将 **Google Antigravity (`agy`)** 深度桥接到 Telegram，赋予了 **Gemini 3.8 Flash** 真实的宿主机最高操作权！

- **Linux VPS** 是它的物理具身：提供完整 Shell、编译器、文件系统与高速千兆网络；
- **Telegram** 是你的随身脑机接口：人在外面，手机上发一句自然语言，它在云端全自主**理解、规划、写代码、查网络、处理数据并交付结果**！

```mermaid
graph TD
    User([你在手机 Telegram 发送复合任务]) --> TG[tg-ai-bot 路由中枢]
    TG --> AGY[Google Gemini 3.8 Flash 深度推理引擎]

    subgraph 云端自主智能体 (Autonomous Agent) 核心能力矩阵
        AGY --> C1[1. 自主全栈研发: 编写项目/配置依赖/部署 Web 服务]
        AGY --> C2[2. 全网情报搜集: 爬虫抓取/价格监控/论文资讯提炼]
        AGY --> C3[3. 数据管道清洗: 统计分析/日志清洗/大文件处理]
        AGY --> C4[4. 跨云与自动化: 定时任务/自动备份/API 联动]
        AGY --> C5[5. 基础设施治理: 硬件巡检/日志排障/故障自动自愈]
    end

    C1 --> Finish[自主执行、检验复测并结构化回传 Telegram]
    C2 --> Finish
    C3 --> Finish
    C4 --> Finish
    C5 --> Finish
    Finish --> User
```

---

## 🚀 通用 Agent 的五大实战应用场景

只要在 Telegram 中切换到 `/mode agent`，你可以随时随地向它下发各类复杂工程任务：

### 1. 💻 自主全栈研发 (Autonomous Developer)
- **你在 TG 发送**：*“帮我用 Python FastAPI 写一个实时展示 BTC 价格和汇率的轻量 Web 页面，跑在 8080 端口”*
- **Agent 行动**：新建项目目录 -> 编写代码 -> 自动安装 `fastapi` 与 `uvicorn` -> 启动服务 -> 本地 `curl` 自测正常 -> 回传访问链接。

### 2. 📡 全网情报搜集与监控 (Intelligence & Scraper)
- **你在 TG 发送**：*“写个脚本每天早上 8 点抓取 GitHub Trending Python 榜单前 5 个热门项目，精炼总结它们的功能发到我的 Telegram”*
- **Agent 行动**：编写爬虫逻辑 -> 调试通过 -> 写入 crontab 定时器 -> 每天准时往 Telegram 播报。

### 3. 📊 数据管道与重型计算 (Data Pipeline)
- **你在 TG 发送**：*“帮我分析系统访问日志里访问量最高的 Top 10 IP，查出它们的归属地并统计报错占比”*
- **Agent 行动**：使用 awk / python 极速解析日志 -> 并发查询 IP 地理接口 -> 几秒内输出清晰整洁的 Markdown 数据表。

### 4. 🔄 跨云自动化中枢 (Cloud Automator)
- **你在 TG 发送**：*“写个每天凌晨将 `/backup` 压缩加密并同步到远程网盘的脚本”*
- **Agent 行动**：编写备份归档逻辑 -> 安装配置 rclone -> 设置自愈重试机制 -> 汇报确认。

### 5. 🛡️ 基础设施自愈运维 (Infrastructure & DevOps)
- **你在 TG 发送**：*“帮我看看当前 VPS 磁盘空间和内存使用，顺便查查 nginx 为什么报 502”*
- **Agent 行动**：执行 `df -h` 与 `free -m` 提取数值 -> 读取 nginx error.log 定位挂掉的端口 -> 自动重启拉起服务 -> 输出完整健康体检报告。

---

## 🎭 双模式与二次确认体系 (`/mode`)

| 模式 | 指令 | 说明 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **全功能 Agent 模式** | `/mode agent confirm` | 激活宿主机 Shell、文件读写与网络操作权（**强制二次确认 + 白名单校验**） | 远程开发、数据抓取、自动化脚本与运维干活 |
| **纯对话安全模式** | `/mode chat` | 仅进行深度思考与推理问答，严格物理隔离系统命令 | 日常学术查资料、文本翻译、灵感脑暴、聊天 |

> [!NOTE]
> 出于安全防护，若直接发送 `/mode agent`，机器人将主动发出高危警示并要求输入 `/mode agent confirm` 进行二次确认；未配置在白名单中的访客严禁开启 Agent 模式。

---

## 🛡️ 企业级工程与安全加固设计

为保障服务器长期无人值守运行的极致稳定性与安全性，本项目实施了多项系统级加固：

### 1. 🔒 零信任白名单安全防线 (Default-Deny)
- **默认全面锁定**：未在 `.env` 中配置 `ALLOWED_USER_IDS` 时，系统进入默认全员拦截锁定状态（仅开放 `/id` 供管理员查看自身 ID），坚决杜绝“空白名单=全员放行”的隐患。
- **Agent 模式硬隔离**：即便开启了公开对话选项，高危的 Agent 宿主机模式也**永远**只对白名单管理员开放。

### 2. 👤 运行身份降权与进程隔离 (Least Privilege)
- **专用低权限用户**：安装脚本默认配置 `tgbot` 独立系统用户运行服务，避免 root 权限直连外部引发越权风险。
- **systemd 提权拦截**：服务配置默认启用 `NoNewPrivileges=true`，严格锁死子进程提权路径。

### 3. 🚦 多级并发限流与熔断保护 (Resource & Concurrency Guard)
- **Per-Chat 独占锁**：同一会话内严格串行化处理，防止快速连发消息拉起多个进程导致会话记忆错乱。
- **全局并发上限**：通过 `MAX_CONCURRENT_TASKS`（默认 2）限制全局并发 agy 子进程数，防止多请求并发打爆 VPS 内存与 CPU。
- **一键终止任务 (`/cancel`)**：遇到死循环、长时间网络阻塞或意外卡顿的任务，可随时发送 `/cancel` 强制终止对应子进程。

### 4. ⚡ 双引擎高可用 HA 降级兜底 (Agy + OpenAI 兼容后端)
- **主引擎**：Google Antigravity (`agy`)，提供原生零成本 Gemini 3.8 Flash 推理与宿主机具身操作。
- **备用引擎**：内置 OpenAI 兼容客户端（支持 OpenAI / DeepSeek / Claude / Ollama 等）。当主引擎因网络波动、配额超限或环境异常无法响应时，在对话模式下自动无缝平滑兜底！

### 5. 📝 智能 Markdown 代码块切分与透明会话自愈
- **代码块语法闭合**：突破 Telegram 4096 字符硬切造成的代码块语法破坏问题，在分段截断时自动闭合当前 chunk 的代码块并在下一段重新开起，排版绝不混乱。
- **精准会话失效重试**：告别脆弱的简单字符串匹配，采用严格正则捕获会话过期并自动无感新建会话发起重试，体验丝滑。

---

## 📊 为什么选择本项目？（四维对比）

| 对比维度 | 传统 Telegram 聊天机器人 | 本地部署 Hermes 方案 | 闭源沙盒 Pi / 网页 Agent | 本项目 (tg-ai-bot) |
| :--- | :--- | :--- | :--- | :--- |
| **真实系统权限** | ❌ 只能给文字建议 | 需繁重 Docker 和显卡 | ❌ 仅限虚拟网页沙盒，碰不到你的服务器 | 🛠️ **可控的宿主机具身执行权（带二次确认与白名单）** |
| **硬件与成本** | 需持续购买 API Key 额度 | 需几万元的显卡 (4090/A100) | 每月 $20+ 订阅费 | 💡 **完全免费！20MB 内存小鸡即可起飞** |
| **安全与隔离** | 普遍缺少防护 | 需复杂容器配置 | 封闭在第三方厂商服务器 | 🛡️ **Default-Deny 零信任、专用降权用户与并发熔断** |
| **模型推理智商** | 多为 gpt-3.5 或小参数模型 | 较小开源模型，复杂任务易幻觉 | 偏日常闲聊，缺乏工程训练 | ⚡ **Google 最新 Gemini 3.8 Flash (High)** |
| **移动端触达** | 仅能在聊天框闲聊 | 无法脱离工作站电脑 | 独立 App 或网页，工作流割裂 | 📱 **随时随地 Telegram 即时通讯窗口下发任务** |

---

## 🤖 常用 Telegram 指令速查

| 指令 | 说明 |
| :--- | :--- |
| `/start` | 启动智能体并展示全能功能概览 |
| `/mode` | 查看当前模式；输入 `/mode agent confirm` 或 `/mode chat` 进行切换 |
| `/cancel` 或 `/stop` | 强制终止当前正在运行的后台任务 |
| `/clear` 或 `/reset` | 清除当前上下文记忆（主引擎与备用引擎同步清理），开启新任务 |
| `/status` | 查看系统运行状态、主机运行身份、**Gemini 各模型实时额度与重置倒计时**、双引擎状态 |
| `/restart` 或 `/reload` | 热重启 Bot 守护进程并重载最新代码（仅白名单管理员） |
| `/id` | 获取当前用户的 Telegram 数字 ID（用于白名单配置） |
| `/help` | 查看详细帮助与说明指南 |

---

## 🔒 隐私与安全性保障
- 生产环境务必配置 `ALLOWED_USER_IDS`，确保只有你个人的 Telegram 账号能够向 Agent 下发指令。
- 真实的 `.env` 配置文件与运行时 `sessions.json` 已被 `.gitignore` 全面排除，绝不会上传到公开代码仓库。

---

## ⭐ Star History

<p align="center">
  <a href="https://star-history.com/#Sumblink182/tg-ai-bot&Date">
    <img src="https://api.star-history.com/svg?repos=Sumblink182/tg-ai-bot&type=Date" alt="Star History Chart">
  </a>
</p>

---

## 📄 开源许可证
本项目基于 [MIT License](./LICENSE) 开源发布。

