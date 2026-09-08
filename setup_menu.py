import asyncio
from telegram import Bot, BotCommand
import config

async def setup_bot_menu():
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ 未找到 TELEGRAM_BOT_TOKEN")
        return

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    commands = [
        BotCommand("start", "启动智能体并获取全能指引"),
        BotCommand("mode", "切换模式 (agent自主执行 / chat安全对话)"),
        BotCommand("clear", "清除当前记忆，开启全新任务"),
        BotCommand("status", "查看智能体状态、当前模式与会话ID"),
        BotCommand("id", "获取你的 Telegram 用户数字 ID"),
        BotCommand("help", "查看详细功能使用指南")
    ]
    
    print("🚀 正在向 Telegram 官方注册指令菜单...")
    await bot.set_my_commands(commands)
    print("✅ 成功！Telegram 官方菜单指令已更新注册生效！")

if __name__ == "__main__":
    asyncio.run(setup_bot_menu())
