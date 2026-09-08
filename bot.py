import asyncio
import getpass
import logging
import os
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import config
from agy_engine import agy_engine
from ai_service import ai_service

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_user_auth(user_id: int) -> tuple[bool, str]:
    """
    检查用户授权状态 (零信任 Default-Deny 设计)
    返回: (is_authorized: bool, reason: str)
    """
    if config.ALLOWED_USER_IDS:
        if user_id in config.ALLOWED_USER_IDS:
            return True, "whitelisted"
        return False, "unauthorized"

    # ALLOWED_USER_IDS 为空
    if config.ALLOW_PUBLIC_CHAT:
        return True, "public_chat"
    return False, "whitelist_empty"

def is_user_allowed(user_id: int) -> bool:
    allowed, _ = get_user_auth(user_id)
    return allowed

def smart_split_markdown(text: str, max_chunk_size: int = 3800) -> list[str]:
    """
    智能分段长文本，防止 Telegram 4096 字符上限拦截，
    并在切分处维护 Markdown 代码块 (```) 的开闭状态，避免代码块被切断导致排版崩坏。
    """
    if not text or len(text) <= max_chunk_size:
        return [text] if text else []

    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_len = 0
    in_code = False
    code_lang = ""

    for line in lines:
        stripped = line.strip()
        is_fence = stripped.startswith("```")
        line_len = len(line) + 1

        # 单行超长情况
        if line_len > max_chunk_size:
            if current_chunk:
                if in_code:
                    current_chunk.append("```")
                chunks.append("\n".join(current_chunk))
                current_chunk = [f"```{code_lang}"] if in_code else []
                current_len = len(current_chunk[0]) + 1 if in_code else 0

            step = max_chunk_size - 100
            for i in range(0, len(line), step):
                part = line[i:i + step]
                if in_code:
                    chunks.append(f"```{code_lang}\n{part}\n```")
                else:
                    chunks.append(part)
            continue

        if current_len + line_len > max_chunk_size and current_chunk:
            if in_code:
                current_chunk.append("```")
                chunks.append("\n".join(current_chunk))
                current_chunk = [f"```{code_lang}"]
                current_len = len(current_chunk[0]) + 1
            else:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0

        if is_fence:
            if in_code:
                in_code = False
                code_lang = ""
            else:
                in_code = True
                code_lang = stripped[3:].strip()

        current_chunk.append(line)
        current_len += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

async def send_split_message(update: Update, text: str):
    """安全智能分段发送长消息，Markdown 解析失败时自动无损降级为纯文本"""
    chunks = smart_split_markdown(text, max_chunk_size=3800)

    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        except BadRequest as e:
            logger.warning(f"Markdown 解析异常，降级为普通纯文本发送: {e}")
            try:
                await update.message.reply_text(chunk)
            except Exception as ex:
                logger.error(f"消息发送失败: {ex}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    user = update.effective_user
    user_id = user.id if user else 0
    chat_id = update.effective_chat.id
    current_mode = agy_engine.get_mode(chat_id)
    logger.info(f"收到用户 {user_id} ({user.first_name if user else ''}) 的 /start 指令")

    allowed, reason = get_user_auth(user_id)
    if not allowed:
        if reason == "whitelist_empty":
            await update.message.reply_text(
                f"🔒 **系统安全锁定**\n\n"
                "服务端尚未配置管理员白名单 (`ALLOWED_USER_IDS`)。\n"
                "为防止 VPS 宿主机被外部恶意接管，已开启默认拒绝防护。\n\n"
                f"👤 **您的 Telegram ID**: `{user_id}`\n"
                "👉 请将该 ID 添加到服务端 `.env` 文件的 `ALLOWED_USER_IDS` 中，并重启服务。",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"⛔ **抱歉，访问受限**\n\n"
                f"您的 Telegram ID (`{user_id}`) 不在授权白名单中。\n"
                "请联系服务器管理员将其加入白名单。",
                parse_mode=ParseMode.MARKDOWN
            )
        return

    welcome_text = (
        f"👋 你好，{user.first_name if user else '朋友'}！\n\n"
        f"🤖 我是你的 **24 小时云端驻留通用自主智能体 (Cloud Autonomous Agent)**\n"
        "以 Linux 服务器为具身手脚，以 Telegram 为随身交互中枢，由 **Google Gemini 3.8 Flash (High)** 深度推理引擎驱动。\n\n"
        "✨ **五大核心自主能力**：\n"
        "1. 💻 **自主全栈研发**：独立写代码、建项目、配环境、部署 Web 服务\n"
        "2. 📡 **全自动情报搜集**：爬取网页、监控价格/榜单、整理学术论文\n"
        "3. 📊 **数据管道与重型计算**：大文件清洗、格式转换、数据统计与图表\n"
        "4. 🔄 **工作流与跨云中枢**：定时任务、文件自动打包、云存储同步\n"
        "5. 🛡️ **基础设施自愈运维**：硬件体检、日志排查、故障自动修复\n\n"
        f"⚙️ **当前运行模式**: `{current_mode.upper()}`\n\n"
        "📌 **常用指令**：\n"
        "• `/mode` - 模式切换 (`/mode agent confirm` 开启全自主 / `/mode chat` 安全对话)\n"
        "• `/cancel` 或 `/stop` - 强制中止当前正在运行的后台任务\n"
        "• `/clear` 或 `/reset` - 清除当前记忆上下文，开启全新任务\n"
        "• `/status` - 查看系统运行状态、权限安全与双引擎配置\n"
        "• `/id` - 查看你的 Telegram 用户数字 ID\n"
        "• `/help` - 查看详细功能使用说明\n\n"
        "💬 直接向我发送任意复杂任务或问题，我将立即为你自主规划并执行！"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /mode 模式切换命令（增强安全防护与二次确认）"""
    user_id = update.effective_user.id if update.effective_user else 0
    allowed, reason = get_user_auth(user_id)
    if not allowed:
        return

    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        current_mode = agy_engine.get_mode(chat_id)
        desc = (
            "🛡️ **纯对话安全模式**（深度问答思考，严格隔离服务器系统命令）"
            if current_mode == "chat"
            else "🛠️ **通用自主 Agent 模式**（已激活宿主机执行权，可全自动写代码、爬虫、跑命令）"
        )
        text = (
            f"⚙️ **当前运行模式**: `{current_mode.upper()}`\n"
            f"说明: {desc}\n\n"
            "📌 **如何切换模式**：\n"
            "• `/mode chat` - 切为纯对话安全模式\n"
            "• `/mode agent confirm` - 二次确认激活自主 Agent 模式（高危具身执行权）"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    target = args[0].lower().strip()

    if target == "chat":
        agy_engine.set_mode(chat_id, "chat")
        await update.message.reply_text(
            "🛡️ **已切换为: 纯对话安全模式**\n\n"
            "智能体将仅进行深度思考与推理问答，已严格隔离服务器终端与系统命令。"
        )
        return

    if target == "agent":
        # 安全防线 1：未配置白名单或非白名单用户严禁开启 agent 模式
        if not config.ALLOWED_USER_IDS or user_id not in config.ALLOWED_USER_IDS:
            await update.message.reply_text(
                "⛔ **安全拦截：权限不足**\n\n"
                "Agent 模式拥有 VPS 宿主机 Shell 执行权与文件读写能力。\n"
                "出于服务器安全保护，仅允许在配置了 `ALLOWED_USER_IDS` 白名单的管理员账号下开启！"
            )
            return

        # 安全防线 2：二次确认要求
        is_confirmed = len(args) > 1 and args[1].lower().strip() in ("confirm", "--force", "yes", "true")
        if not is_confirmed:
            warn_msg = (
                "⚠️ **【高危权限激活警示】**\n\n"
                "Agent 模式将授予 AI 直接在宿主机 Shell 执行命令、编写部署代码、读写文件的全自主权限！\n\n"
                "为防止误触带来安全风险，请发送以下指令进行**二次确认开启**：\n"
                "`/mode agent confirm`\n\n"
                "💡 若仅需进行日常问答，可保持当前模式或随时输入 `/mode chat`。"
            )
            await update.message.reply_text(warn_msg, parse_mode=ParseMode.MARKDOWN)
            return

        agy_engine.set_mode(chat_id, "agent")
        msg = (
            "🚀 **已成功激活: 全功能自主 Agent 模式**\n\n"
            "⚠️ **具身执行权已激活**：Gemini 3.8 Flash 现在可以直接调用宿主机 Shell、编写与部署代码、进行爬虫搜集与系统自愈。\n\n"
            "💡 **试着指派复合任务**：\n"
            "• *帮我写一个轻量 API 服务跑在 8080 端口*\n"
            "• *写个爬虫抓取 Hacker News 热门发给我*\n"
            "• *检查当前服务器磁盘、内存与异常日志*\n"
            "• *帮我写个定时备份脚本加入 crontab*\n\n"
            "🔒 如需退回安全模式，请随时发送 `/mode chat`。"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    await update.message.reply_text(
        "❌ 无效的模式参数。请使用 `/mode chat` 或 `/mode agent confirm`。"
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /cancel 或 /stop 强制中止任务命令"""
    user_id = update.effective_user.id if update.effective_user else 0
    if not is_user_allowed(user_id):
        return

    chat_id = update.effective_chat.id
    logger.info(f"收到 chat_id={chat_id} 的 /cancel 指令")
    cancelled = agy_engine.cancel_task(chat_id)
    if cancelled:
        await update.message.reply_text("🛑 已成功强制终止当前正在运行的后台任务！")
    else:
        await update.message.reply_text("⚪ 当前没有正在执行的任务。")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"收到用户 {user_id} 的 /help 指令")
    help_text = (
        "📖 **通用自主智能体使用帮助指南**\n\n"
        "1. **任务指派**：直接发送自然语言需求，Agent 会自动理解、规划步骤并在云端自主完成。\n"
        "2. **/mode**：查看或切换运行模式：\n"
        "   - `/mode agent confirm`：二次确认开启 Agent 模式（允许执行系统命令、写代码、查日志）\n"
        "   - `/mode chat`：纯对话安全模式（仅回答问题，严格隔离命令）\n"
        "3. **/cancel**：强制中止当前卡住或超时的后台任务。\n"
        "4. **/clear**：随时清空历史记忆，开启新的独立任务。\n"
        "5. **/status**：查看后端模型、运行用户、并发限额与安全状态。\n"
        "6. **/id**：查看你的 Telegram 数字 ID（用于白名单配置）。\n\n"
        f"⚙️ **主模型**: `{config.MODEL_NAME}`\n"
        f"⚡ **备用兜底**: `{config.FALLBACK_MODEL if ai_service.is_available() else '未配置'}`"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /id 命令（始终允许访问，便于获取 ID 配置白名单）"""
    user = update.effective_user
    chat = update.effective_chat
    logger.info(f"收到用户 {user.id if user else 0} 的 /id 指令")
    info = (
        f"👤 **用户 ID**: `{user.id if user else '未知'}`\n"
        f"💬 **会话 Chat ID**: `{chat.id if chat else '未知'}`"
    )
    await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /status 命令"""
    user_id = update.effective_user.id if update.effective_user else 0
    if not is_user_allowed(user_id):
        return

    chat_id = update.effective_chat.id
    conv_id = agy_engine.get_conversation_id(chat_id)
    current_mode = agy_engine.get_mode(chat_id)
    is_busy = agy_engine.is_chat_busy(chat_id)
    current_user = getpass.getuser()
    is_root = os.geteuid() == 0

    user_badge = f"{current_user} ⚠️ (超级用户，建议降权运行)" if is_root else f"{current_user} ✅ (已降权安全运行)"
    fallback_badge = f"✅ 已就绪 ({config.FALLBACK_MODEL})" if ai_service.is_available() else "⚪ 未配置 (可选配置 OPENAI_API_KEY 开启)"
    whitelist_badge = f"已启用 ({len(config.ALLOWED_USER_IDS)} 人)" if config.ALLOWED_USER_IDS else "未配置 (🔒 默认拒绝所有外部访问)"

    status_text = (
        "📊 **系统运行状态**\n\n"
        f"• **运行用户**: `{user_badge}`\n"
        f"• **主 AI 引擎**: `{config.MODEL_NAME} (agy)`\n"
        f"• **备用 AI 引擎**: `{fallback_badge}`\n"
        f"• **当前运行模式**: `{current_mode.upper()} ({'全自主 Agent 执行' if current_mode == 'agent' else '纯安全对话'})`\n"
        f"• **当前会话状态**: `{'⏳ 任务执行中...' if is_busy else '🟢 空闲就绪'}`\n"
        f"• **当前会话 ID**: `{conv_id if conv_id else '暂无（发送首条消息后自动生成）'}`\n"
        f"• **安全白名单**: `{whitelist_badge}`\n"
        f"• **并发保护上限**: `全局最大 {config.MAX_CONCURRENT_TASKS} 个任务`"
    )
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /clear 命令"""
    user_id = update.effective_user.id if update.effective_user else 0
    if not is_user_allowed(user_id):
        return

    chat_id = update.effective_chat.id
    logger.info(f"收到 chat_id={chat_id} 的 /clear 指令")
    had_session = agy_engine.clear(chat_id)
    ai_service.clear_history(chat_id)

    if had_session:
        await update.message.reply_text("🧹 已重置并清空当前会话记忆（主引擎与备用引擎已同步清理），开启全新任务！")
    else:
        await update.message.reply_text("✨ 当前本来就是全新会话，无需清理，请直接指派任务！")

async def keep_typing(bot, chat_id: int, stop_event: asyncio.Event):
    """在后台持续发送 typing 动作，提升用户体验"""
    while not stop_event.is_set():
        try:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=4.0)
        except asyncio.TimeoutError:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户文本消息"""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    chat_id = update.effective_chat.id
    user_text = update.message.text.strip()

    logger.info(f"📨 收到来自用户 {user_id} 的消息: {user_text}")

    allowed, reason = get_user_auth(user_id)
    if not allowed:
        logger.warning(f"用户 {user_id} 被安全防护拦截 (原因: {reason})")
        if reason == "whitelist_empty":
            await update.message.reply_text(
                f"🔒 **系统安全锁定**\n\n"
                "服务端尚未配置管理员白名单 (`ALLOWED_USER_IDS`)。\n"
                "为防止服务器被未授权调用与接管，已开启默认拒绝防护。\n\n"
                f"👤 **您的 Telegram ID**: `{user_id}`\n"
                "👉 请将该 ID 添加到服务端 `.env` 文件的 `ALLOWED_USER_IDS` 中，并重启服务。",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"⛔ **访问受限**\n\n您没有权限使用此机器人。\n您的 Telegram ID 是: `{user_id}`"
            )
        return

    if not user_text:
        return

    # Per-chat 并发锁检查：防止同一聊天疯狂刷屏触发大量 agy 子进程
    if agy_engine.is_chat_busy(chat_id):
        await update.message.reply_text(
            "⏳ **当前已有任务正在处理中**，请耐心等待其完成。\n"
            "💡 若该任务耗时过长或卡住，可发送 `/cancel` 强制终止。"
        )
        return

    current_mode = agy_engine.get_mode(chat_id)

    # 启动后台 typing 提示
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop_typing))

    try:
        # 调用 agy 执行引擎 (内置 per-chat 独占锁与全局并发信号量控制)
        result = await agy_engine.ask(chat_id=chat_id, prompt=user_text)
    finally:
        stop_typing.set()
        await typing_task

    if result.get("ok"):
        reply_text = result.get("response", "（无回答返回）")
        logger.info(f"📤 成功生成回复并发送给用户 {user_id}")
        await send_split_message(update, reply_text)
    else:
        error_msg = result.get("error", "❌ 执行失败，未知错误。")
        logger.error(f"处理用户 {user_id} 消息失败: {error_msg}")

        # 高可用 Fallback: 如果是 chat 模式且配置了备用 AI，自动无缝降级兜底
        if current_mode == "chat" and ai_service.is_available():
            logger.warning(f"主引擎调用失败，正在自动切换至备用 AI 引擎 ({config.FALLBACK_MODEL}) 兜底...")
            try:
                fallback_reply = await ai_service.ask_ai(chat_id, user_text)
                await send_split_message(
                    update,
                    f"{fallback_reply}\n\n*(⚡ 主引擎暂时不可用，已自动由备用 AI 引擎无缝兜底回答)*"
                )
                return
            except Exception as e:
                logger.error(f"备用 AI 兜底亦失败: {e}")

        # 如果处于 agent 模式，说明不能单纯降级（因为需要系统命令执行能力）
        if current_mode == "agent":
            await update.message.reply_text(
                f"{error_msg}\n\n"
                "💡 **Agent 模式提示**：具身执行依赖 Antigravity CLI 宿主机环境。若需纯对话，可切换至 `/mode chat`。"
            )
        else:
            await update.message.reply_text(error_msg)

def main():
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("=" * 68)
        print("⚠️ 未检测到有效 TELEGRAM_BOT_TOKEN！")
        print("请在 /root/tg-ai-bot/.env 文件中填入你的 Telegram Bot Token。")
        print("=" * 68)
        return

    # 安全检查：检测是否以 root 运行
    current_user = getpass.getuser()
    if os.geteuid() == 0:
        logger.warning("=" * 68)
        logger.warning("⚠️  【安全警示】Bot 当前正在以 root (超级用户) 权限运行！")
        logger.warning("⚠️  若在 Agent 模式下执行命令，AI 将拥有宿主机最高 root 权限。")
        logger.warning("💡 强烈建议创建专用低权限用户 (如 tgbot) 运行服务以隔离风险。")
        logger.warning("=" * 68)
    else:
        logger.info(f"✅ 当前以专用非 root 用户运行: {current_user}")

    # 安全检查：检测白名单状态
    if not config.ALLOWED_USER_IDS:
        if config.ALLOW_PUBLIC_CHAT:
            logger.warning("⚠️ ALLOWED_USER_IDS 为空，已启用 ALLOW_PUBLIC_CHAT 模式 (仅限 chat 模式，agent 模式已全面禁用)")
        else:
            logger.warning("🔒 ALLOWED_USER_IDS 为空且未开启公开聊天，已启动零信任锁定 (拒绝所有外部访问)")
    else:
        logger.info(f"🛡️ 白名单防护已生效，已授权 {len(config.ALLOWED_USER_IDS)} 个用户")

    if ai_service.is_available():
        logger.info(f"⚡ 高可用备用 AI 引擎已激活: {config.FALLBACK_MODEL}")

    print(f"🚀 正在启动 Telegram AI Bot (主模型: {config.MODEL_NAME})...")
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # 注册命令 Handler
    app.add_handler(CommandHandler(["start"], start_command))
    app.add_handler(CommandHandler(["mode"], mode_command))
    app.add_handler(CommandHandler(["help"], help_command))
    app.add_handler(CommandHandler(["clear", "reset"], clear_command))
    app.add_handler(CommandHandler(["cancel", "stop"], cancel_command))
    app.add_handler(CommandHandler(["id"], id_command))
    app.add_handler(CommandHandler(["status"], status_command))

    # 注册普通文本消息 Handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot 已经成功运行（长轮询模式），在 Telegram 中向它发送消息即可开始对话！")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()

