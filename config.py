import os
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# Telegram Bot 核心配置
# =========================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# =========================================================
# Antigravity (agy) 引擎配置
# =========================================================
AGY_BIN_PATH = os.getenv("AGY_BIN_PATH", "/root/.local/bin/agy").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.8-flash-high").strip()
AGENT_MODE = os.getenv("AGENT_MODE", "chat").strip().lower()

# =========================================================
# 安全与权限控制 (Default-Deny 零信任设计)
# =========================================================
# 白名单 Telegram User ID。未配置白名单时，默认拒绝所有人访问以防服务器被提权控制。
_allowed = os.getenv("ALLOWED_USER_IDS", "").strip()
ALLOWED_USER_IDS = set(int(uid.strip()) for uid in _allowed.split(",") if uid.strip().isdigit())

# 是否允许公开安全对话 (仅当 ALLOWED_USER_IDS 为空且此项明确设为 true 时开放 chat 模式；agent 模式永不开放公开访问)
ALLOW_PUBLIC_CHAT = os.getenv("ALLOW_PUBLIC_CHAT", "false").strip().lower() in ("true", "1", "yes")

# 超时设置（默认 5 分钟）
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "300"))

# =========================================================
# 并发与资源保护
# =========================================================
# 全局最大并发任务数（防止并发拉起多个 agy 导致 VPS 内存或配额耗尽）
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "2"))

# =========================================================
# 备用 AI 引擎配置 (OpenAI 兼容协议，用于 agy 故障时的无缝高可用兜底)
# =========================================================
ENABLE_FALLBACK = os.getenv("ENABLE_FALLBACK", "true").strip().lower() in ("true", "1", "yes")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gpt-4o-mini").strip()
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "你是一个部署在 Linux 服务器上的通用云端 AI 助手，请提供准确、高效、专业的回答。"
).strip()
MAX_HISTORY_ROUNDS = int(os.getenv("MAX_HISTORY_ROUNDS", "10"))

