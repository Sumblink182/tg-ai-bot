# Telegram ↔ Antigravity (Gemini 3.8 Flash) AI 智能助理机器人

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots/api)
[![Gemini](https://img.shields.io/badge/Model-Gemini%203.8%20Flash%20(High)-orange.svg)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个将 **Telegram 机器人** 与本地 **Google Antigravity CLI (`agy`)** 深度集成的智能对话与远程运维网关。

搭载 **Gemini 3.8 Flash (High)** 深度推理大模型，**完全无需购买第三方 API Key**，支持原生多轮上下文记忆，并配备严格的白名单鉴权机制与系统级常驻服务守护。

---

## ✨ 核心特性

- 💡 **免第三方 API Key**：直接复用本地 Antigravity CLI 已授权的内置引擎与云端大模型，零外部 API 计费。
- 🧠 **原生多轮上下文记忆**：基于 `conversation_id` 自动管理对话上下文，随时使用 `/clear` 开启全新话题。
- 🛡️ **严格白名单访问控制**：支持 `ALLOWED_USER_IDS` 绑定机主数字 ID，杜绝未授权人员盗刷 VPS 资源。
- 🔄 **生产级 systemd 守护**：开机自动拉起、崩溃自愈、断线重连消息不丢失。
- ⚡ **长文本切片与优雅降级**：超长消息自动按 4000 字符切分，Telegram Markdown 语法异常时自动平滑降级为纯文本输出。
- 🛠️ **双运行模式**：
  - `chat`：纯对话安全模式（推荐，仅推理问答）。
  - `agent`：全功能运维模式（支持通过 Telegram 命令让 Agent 自动操作 VPS 终端与读写文件）。

---

## 📂 项目结构

```text
├── agy_engine.py       # Antigravity CLI 子进程调度引擎与 session 管理
├── bot.py              # Telegram 机器人交互主程序
├── config.py           # 环境变量与配置加载
├── requirements.txt    # 项目依赖
├── start.sh            # 一键后台启动脚本
├── stop.sh             # 一键后台停止脚本
├── status.sh           # 运行状态与最近日志查看脚本
├── tg-ai-bot.service   # systemd 系统服务定义
├── .env.example        # 配置文件示例
└── README.md           # 本文档
```

---

## 🚀 快速开始

### 1. 环境准备
- Linux 服务器（推荐 Ubuntu 22.04 / 24.04 或 Debian）
- Python 3.12+
- 已安装并完成认证的 [Google Antigravity CLI](https://antigravity.google) (`agy`)

```bash
git clone <你的仓库地址>
cd tg-ai-bot
```

### 2. 安装依赖
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 3. 配置环境变量
复制配置文件模板：
```bash
cp .env.example .env
nano .env
```

主要配置项说明：
```env
# 从 Telegram @BotFather 获取的 Token (必填)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Antigravity CLI 路径
AGY_BIN_PATH=/root/.local/bin/agy

# 使用的模型名称
MODEL_NAME=gemini-3.8-flash-high

# 运行模式: chat (安全对话) 或 agent (全功能 Agent)
AGENT_MODE=chat

# 白名单 User ID (强烈建议填写你的 Telegram 数字 ID)
ALLOWED_USER_IDS=8808188711
```

### 4. 启动运行

#### 方式 A：通过脚本启停
```bash
./start.sh    # 后台启动
./status.sh   # 检查状态
./stop.sh     # 停止服务
```

#### 方式 B：通过 systemd 常驻守护（推荐）
```bash
cp tg-ai-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now tg-ai-bot

# 监控实时日志
journalctl -u tg-ai-bot -f
```

---

## 🤖 Telegram 指令速查

| 指令 | 说明 |
| :--- | :--- |
| `/start` | 启动机器人并显示欢迎信息与功能说明 |
| `/clear` 或 `/reset` | 清除当前会话的上下文记忆，开启新话题 |
| `/status` | 查看当前连接状态、后端模型与活跃会话 ID |
| `/id` | 获取当前用户的 Telegram 数字 ID（用于白名单配置） |
| `/help` | 查看详细帮助菜单 |

---

## 🔒 安全说明
本项目遵循严格的安全设计，`.env` 配置文件与运行时 `sessions.json` 已被 `.gitignore` 全面排除，请勿将包含真实 Bot Token 的文件提交至公开代码仓库。

---

## 📄 开源许可证
本项目基于 [MIT License](LICENSE) 开源。
