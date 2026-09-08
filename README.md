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
  💡 <b>零 API 成本</b> | 🧠 <b>原生深度推理</b> | 🛠️ <b>全自主代码/数据/系统接管</b> | 🛡️ <b>白名单防盗刷</b> | ⚡ <b>内存仅 ~20MB</b>
</p>

---

## ⚡ 极速一键安装 (One-click Install)

在你的 Linux VPS（Ubuntu / Debian）上直接运行以下命令，即可在 1 分钟内全自动安装、配置并守护启动：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Sumblink182/tg-ai-bot/main/install.sh)
```

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

## 🎭 双模式无缝切换 (`/mode`)

| 模式 | 指令 | 说明 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **全功能 Agent 模式** | `/mode agent` | 激活宿主机 Shell、文件读写、编译器与网络操作权 | 远程开发、数据抓取、自动化脚本与运维干活 |
| **纯对话安全模式** | `/mode chat` | 仅进行深度思考与推理问答，严格隔离系统命令 | 日常学术查资料、文本翻译、灵感脑暴、聊天 |

---

## 📊 为什么选择本项目？（四维对比）

| 对比维度 | 传统 Telegram 聊天机器人 | 本地部署 Hermes 方案 | 闭源沙盒 Pi / 网页 Agent | 本项目 (tg-ai-bot) |
| :--- | :--- | :--- | :--- | :--- |
| **真实系统权限** | ❌ 只能给文字建议 | 需繁重 Docker 和显卡 | ❌ 仅限虚拟网页沙盒，碰不到你的服务器 | 🛠️ **直接握有宿主机真实最高执行权** |
| **硬件与成本** | 需持续购买 API Key 额度 | 需几万元的显卡 (4090/A100) | 每月 $20+ 订阅费 | 💡 **完全免费！20MB 内存小鸡即可起飞** |
| **模型推理智商** | 多为 gpt-3.5 或小参数模型 | 较小开源模型，复杂任务易幻觉 | 偏日常闲聊，缺乏工程训练 | ⚡ **Google 最新 Gemini 3.8 Flash (High)** |
| **移动端触达** | 仅能在聊天框闲聊 | 无法脱离工作站电脑 | 独立 App 或网页，工作流割裂 | 📱 **随时随地 Telegram 即时通讯窗口下发任务** |

---

## 🤖 常用 Telegram 指令速查

| 指令 | 说明 |
| :--- | :--- |
| `/start` | 启动智能体并展示全能功能概览 |
| `/mode` | 查看当前模式；输入 `/mode agent` 或 `/mode chat` 进行无缝切换 |
| `/clear` 或 `/reset` | 清除当前上下文记忆，开启新任务 |
| `/status` | 查看当前连接状态、后端模型与活跃会话 ID |
| `/id` | 获取当前用户的 Telegram 数字 ID（用于白名单配置） |
| `/help` | 查看详细帮助与说明指南 |

---

## 🚀 手动部署教程

### 1. 环境准备
- Linux 操作系统（Ubuntu 22.04 / 24.04、Debian 12+）
- Python 3.10+
- 已在系统中完成认证的 [Google Antigravity CLI](https://antigravity.google) (`agy`)

```bash
git clone https://github.com/Sumblink182/tg-ai-bot.git
cd tg-ai-bot
```

### 2. 初始化环境与安装依赖
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp .env.example .env
nano .env
```
配置项说明：
```env
# 必填：从 @BotFather 获取的 Bot Token
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ

# 必填推荐：只允许你自己的 Telegram 数字 ID (防他人越权)
ALLOWED_USER_IDS=8808188711

# 选填：默认使用的模型
MODEL_NAME=gemini-3.8-flash-high

# 选填：全局默认运行模式 (chat 或 agent)
AGENT_MODE=chat
```

### 4. 注册菜单并启动常驻
```bash
# 注册 Telegram 官方底部 Menu 按钮
./venv/bin/python3 setup_menu.py

# 注册为 systemd 开机自启服务
cp tg-ai-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now tg-ai-bot

# 监控实时状态
systemctl status tg-ai-bot
journalctl -u tg-ai-bot -f
```

---

## 🔒 隐私与安全性保障
- 生产环境务必配置 `ALLOWED_USER_IDS`，确保只有你个人的 Telegram 账号能够向 Agent 下发宿主机执行指令。
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
