#!/bin/bash
set -e

echo "======================================================="
echo "   🤖 Telegram ↔ Antigravity (Gemini 3.8 Flash) 安装向导"
echo "======================================================="

# 1. 检查 root 权限
if [ "$(id -u)" != "0" ]; then
    echo "⚠️ 请使用 root 用户或使用 sudo 运行此安装脚本。"
    exit 1
fi

INSTALL_DIR="/opt/tg-ai-bot"
if [ -d "/root/tg-ai-bot" ]; then
    INSTALL_DIR="/root/tg-ai-bot"
fi

# 2. 检查依赖
echo "📦 正在检查系统依赖..."
if command -v apt-get > /dev/null 2>&1; then
    apt-get update -qq && apt-get install -y -qq git python3 python3-pip python3-venv curl > /dev/null 2>&1
fi

# 3. 检查 Antigravity CLI
if ! command -v /root/.local/bin/agy > /dev/null 2>&1 && ! command -v agy > /dev/null 2>&1; then
    echo "⚠️ 提示: 未检测到系统中的 agy 命令。请确保已完成 Antigravity CLI 安装与认证。"
fi

# 4. 下载或更新代码
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📥 正在克隆项目仓库..."
    git clone https://github.com/Sumblink182/tg-ai-bot.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 5. 设置 Python 虚拟环境
echo "🐍 正在配置 Python 虚拟环境与依赖..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

# 6. 配置 .env 环境变量
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo ""
    echo "🔑 请输入你的 Telegram Bot Token (从 @BotFather 获取):"
    read -r TOKEN
    while [ -z "$TOKEN" ]; do
        echo "❌ Token 不能为空，请重新输入:"
        read -r TOKEN
    done

    echo ""
    echo "🛡️ 请输入允许使用此 Bot 的 Telegram User ID (可选，建议填写以防盗刷，留空则公开):"
    read -r ALLOWED_UID

    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    sed -i "s/^TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=$TOKEN/" "$INSTALL_DIR/.env"
    if [ -n "$ALLOWED_UID" ]; then
        sed -i "s/^ALLOWED_USER_IDS=.*/ALLOWED_USER_IDS=$ALLOWED_UID/" "$INSTALL_DIR/.env"
    fi
fi

# 7. 配置 systemd 服务
echo "⚙️ 正在配置 systemd 常驻守护服务..."
sed -i "s|/root/tg-ai-bot|$INSTALL_DIR|g" "$INSTALL_DIR/tg-ai-bot.service"
cp "$INSTALL_DIR/tg-ai-bot.service" /etc/systemd/system/tg-ai-bot.service
systemctl daemon-reload
systemctl enable --now tg-ai-bot

# 8. 注册官方菜单
"$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/setup_menu.py" > /dev/null 2>&1 || true

echo ""
echo "======================================================="
echo "🎉 安装完成！机器人已在后台稳定运行并配置开机自启！"
echo "📊 查看运行状态: systemctl status tg-ai-bot"
echo "📄 查看实时日志: journalctl -u tg-ai-bot -f"
echo "======================================================="
