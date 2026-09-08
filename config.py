import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Antigravity CLI 二进制路径
AGY_BIN_PATH = os.getenv("AGY_BIN_PATH", "/root/.local/bin/agy").strip()

# 使用的内置模型名称 (如 gemini-3.8-flash-high, gemini-3.7-flash-high, claude-sonnet-4-6 等)
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.8-flash-high").strip()

# 运行模式: chat (纯对话助手模式，安全) 或 agent (允许在服务器执行命令与写代码)
AGENT_MODE = os.getenv("AGENT_MODE", "chat").strip().lower()

# 白名单 Telegram User ID（只允许这些人使用）。留空表示所有人均可使用。
_allowed = os.getenv("ALLOWED_USER_IDS", "").strip()
ALLOWED_USER_IDS = set(int(uid.strip()) for uid in _allowed.split(",") if uid.strip().isdigit())

# 超时设置（默认 5 分钟）
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "300"))
