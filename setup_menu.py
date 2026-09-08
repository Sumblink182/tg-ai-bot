import asyncio
from telegram import Bot, BotCommand
import config

async def setup_bot_menu():
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ 未找到 TELEGRAM_BOT_TOKEN")
        return

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    commands = [
        BotCommand("start", "启动机器人并获取欢迎指引"),
        BotCommand("clear", "清除当前记忆上下文，开启新话题"),
        BotCommand("status", "查看系统状态、活跃会话与当前模型"),
        BotCommand("id", "获取你的 Telegram 用户数字 ID"),
        BotCommand("help", "查看详细功能使用说明")
    ]
    
    print("🚀 正在向 Telegram 官方注册指令菜单...")
    await bot.set_my_commands(commands)
    print("✅ 成功！Telegram 官方菜单指令已注册生效！")

if __name__ == "__main__":
    asyncio.run(setup_bot_menu())
