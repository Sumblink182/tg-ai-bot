import asyncio
import logging
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

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_user_allowed(user_id: int) -> bool:
    """检查用户是否有权限访问"""
    if not config.ALLOWED_USER_IDS:
        return True
    return user_id in config.ALLOWED_USER_IDS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    user = update.effective_user
    user_id = user.id if user else 0
    logger.info(f"收到用户 {user_id} ({user.first_name if user else ''}) 的 /start 指令")

    if not is_user_allowed(user_id):
        logger.warning(f"用户 {user_id} 不在白名单中，拒绝访问")
        await update.message.reply_text(
            f"⛔ 抱歉，该机器人设置了访问限制。\n您的 Telegram ID 是: `{user_id}`\n请联系管理员将其加入白名单。",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    welcome_text = (
        f"👋 你好，{user.first_name if user else '朋友'}！\n\n"
        f"🤖 我是连接到本地 **Antigravity ({config.MODEL_NAME})** 的智能助手。\n\n"
        "✨ **核心能力**：\n"
        "• 原生搭载 Google Gemini 3.8 Flash (High) 深度推理模型\n"
        "• 支持长上下文多轮记忆对话\n"
        f"• 当前运行模式: `{config.AGENT_MODE.upper()}`\n\n"
        "📌 **常用指令**：\n"
        "• `/clear` 或 `/reset` - 清除当前会话记忆，开启新话题\n"
        "• `/status` - 查看当前连接状态与会话信息\n"
        "• `/id` - 查看你的 Telegram 数字 ID\n"
        "• `/help` - 查看更多说明\n\n"
        "💬 直接向我发送任意问题，我将立即为你思考解答！"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"收到用户 {user_id} 的 /help 指令")
    help_text = (
        "📖 **使用帮助指南**\n\n"
        "1. **日常对话**：直接向机器人发送消息，它会自动记住前序对话上下文。\n"
        "2. **/clear**：随时清空历史记忆，开启新的独立会话。\n"
        "3. **/status**：查看后端模型、运行模式和会话状态。\n"
        "4. **/id**：查看你的数字 ID，用于配置在 `.env` 中的 `ALLOWED_USER_IDS` 防盗刷。\n\n"
        f"⚙️ **后端模型**: `{config.MODEL_NAME}`\n"
        f"🛡️ **运行模式**: `{config.AGENT_MODE}`"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /id 命令"""
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
    chat_id = update.effective_chat.id
    conv_id = agy_engine.get_conversation_id(chat_id)
    logger.info(f"收到 chat_id={chat_id} 的 /status 指令")
    
    status_text = (
        "📊 **系统运行状态**\n\n"
        f"• **AI 模型**: `{config.MODEL_NAME}`\n"
        f"• **引擎路径**: `{config.AGY_BIN_PATH}`\n"
        f"• **运行模式**: `{config.AGENT_MODE.upper()}`\n"
        f"• **当前会话 ID**: `{conv_id if conv_id else '暂无活跃会话（发送首条消息后自动生成）'}`\n"
        f"• **白名单保护**: `{'已启用 (' + str(len(config.ALLOWED_USER_IDS)) + ' 人)' if config.ALLOWED_USER_IDS else '未限制（公开）'}`"
    )
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /clear 命令"""
    chat_id = update.effective_chat.id
    logger.info(f"收到 chat_id={chat_id} 的 /clear 指令")
    had_session = agy_engine.clear(chat_id)
    if had_session:
        await update.message.reply_text("🧹 已重置并清空当前会话记忆，接下来我们可以聊新话题了！")
    else:
        await update.message.reply_text("✨ 当前本来就是全新会话，无需清理，请直接提问！")

async def send_split_message(update: Update, text: str):
    """安全分段发送长消息，Markdown 解析失败时自动降级为纯文本"""
    max_len = 4000
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]
    
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        except BadRequest as e:
            logger.warning(f"Markdown 解析失败，降级为普通纯文本发送: {e}")
            await update.message.reply_text(chunk)

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

    if not is_user_allowed(user_id):
        logger.warning(f"用户 {user_id} 被白名单拦截")
        await update.message.reply_text(
            f"⛔ 抱歉，您没有权限使用此机器人。\n您的 Telegram ID 是: `{user_id}`"
        )
        return

    if not user_text:
        return

    # 启动后台 typing 提示
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop_typing))

    try:
        # 调用 agy 执行引擎
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
        await update.message.reply_text(error_msg)

def main():
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("=" * 65)
        print("⚠️ 未检测到有效 TELEGRAM_BOT_TOKEN！")
        print("请在 /root/tg-ai-bot/.env 文件中填入你的 Telegram Bot Token。")
        print("=" * 65)
        return

    print(f"🚀 正在启动 Telegram AI Bot (后端模型: {config.MODEL_NAME}, 模式: {config.AGENT_MODE})...")
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # 注册命令 Handler
    app.add_handler(CommandHandler(["start"], start_command))
    app.add_handler(CommandHandler(["help"], help_command))
    app.add_handler(CommandHandler(["clear", "reset"], clear_command))
    app.add_handler(CommandHandler(["id"], id_command))
    app.add_handler(CommandHandler(["status"], status_command))

    # 注册普通文本消息 Handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot 已经成功运行（长轮询模式），在 Telegram 中向它发送消息即可开始对话！")
    # 设置 drop_pending_updates=False，确保断线重连期间用户发的消息不会丢失
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
