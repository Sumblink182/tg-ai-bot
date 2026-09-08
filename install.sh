#!/bin/bash
set -e

echo "======================================================="
echo "   🤖 Telegram ↔ Cloud Autonomous AI Agent 安装向导"
echo "======================================================="

# 1. 检查权限与运行用户
IS_ROOT=0
if [ "$(id -u)" = "0" ]; then
    IS_ROOT=1
fi

INSTALL_DIR="/opt/tg-ai-bot"
RUN_USER="tgbot"

if [ "$IS_ROOT" != "1" ]; then
    echo "ℹ️ 当前以普通用户 $(whoami) 运行，将安装到当前用户空间。"
    INSTALL_DIR="$HOME/tg-ai-bot"
    RUN_USER="$(whoami)"
else
    # root 运行：优先创建与使用隔离用户 tgbot
    if ! id -u "$RUN_USER" >/dev/null 2>&1; then
        echo "👤 正在创建专用隔离系统用户: $RUN_USER..."
        useradd -m -s /bin/bash "$RUN_USER" || true
    fi
fi

# 2. 检查并安装基础系统依赖
echo "📦 正在检查系统依赖 (git, python3, python3-venv, curl)..."
if command -v apt-get > /dev/null 2>&1; then
    if [ "$IS_ROOT" = "1" ]; then
        apt-get update -qq && apt-get install -y -qq git python3 python3-pip python3-venv curl > /dev/null 2>&1
    fi
elif command -v yum > /dev/null 2>&1; then
    if [ "$IS_ROOT" = "1" ]; then
        yum install -y -q git python3 python3-pip curl > /dev/null 2>&1
    fi
fi

# 3. 智能探测 Antigravity CLI (agy)
echo "🔍 正在检查 Google Antigravity CLI (agy) 环境..."
FOUND_AGY=""

for path in "$HOME/.local/bin/agy" "/root/.local/bin/agy" "/usr/local/bin/agy" "/usr/bin/agy"; do
    if [ -x "$path" ]; then
        FOUND_AGY="$path"
        break
    fi
done

if [ -z "$FOUND_AGY" ] && command -v agy > /dev/null 2>&1; then
    FOUND_AGY="$(command -v agy)"
fi

if [ -z "$FOUND_AGY" ]; then
    echo ""
    echo "======================================================="
    echo "⚠️  未在系统中检测到已安装的 Antigravity CLI (agy)！"
    echo "======================================================="
    echo "本项目核心依赖 Google Antigravity 提供的云端大模型与工具执行权。"
    echo "请按以下 2 步完成极简前置准备（仅需 1 分钟）："
    echo ""
    echo "  1️⃣ 运行官方安装脚本："
    echo "     curl -fsSL https://antigravity.google/install.sh | bash"
    echo ""
    echo "  2️⃣ 在终端输入 agy 进行首次 Google 账号认证："
    echo "     agy"
    echo ""
    echo "认证完成后，请重新运行本一键安装向导！"
    echo "======================================================="
    exit 1
fi

echo "✅ 检测到 Antigravity CLI: $FOUND_AGY"

# 4. 权限与凭证隔离配置 (降权至专用用户)
if [ "$IS_ROOT" = "1" ] && [ "$RUN_USER" = "tgbot" ]; then
    # 将 agy 软链接或复制到全局目录，确保 tgbot 用户可执行
    if [ ! -x "/usr/local/bin/agy" ]; then
        cp "$FOUND_AGY" /usr/local/bin/agy || ln -sf "$FOUND_AGY" /usr/local/bin/agy
        chmod 755 /usr/local/bin/agy
    fi
    FOUND_AGY="/usr/local/bin/agy"

    # 同步 Google 账号认证凭证到 tgbot 的 home 目录
    if [ -d "$HOME/.gemini" ] && [ -d "/home/tgbot" ]; then
        echo "🔐 正在同步 Antigravity 认证凭证到专用用户 $RUN_USER..."
        cp -r "$HOME/.gemini" /home/tgbot/
        chown -R "$RUN_USER:$RUN_USER" /home/tgbot/.gemini
    fi
fi

# 5. 下载或进入项目仓库
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📥 正在克隆项目仓库至 $INSTALL_DIR..."
    git clone https://github.com/Sumblink182/tg-ai-bot.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 6. 设置 Python 虚拟环境与依赖
echo "🐍 正在配置 Python 虚拟环境与依赖..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

# 7. 配置 .env 环境变量
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo ""
    echo "🔑 请输入你的 Telegram Bot Token (在 Telegram 搜索 @BotFather 发送 /newbot 获取):"
    read -r TOKEN
    while [ -z "$TOKEN" ]; do
        echo "❌ Token 不能为空，请重新输入:"
        read -r TOKEN
    done

    echo ""
    echo "🛡️ 请输入允许使用此 Bot 的 Telegram User ID 白名单 (安全核心配置，多个 ID 逗号分隔):"
    read -r ALLOWED_UID
    while [ -z "$ALLOWED_UID" ]; do
        echo "⚠️ 出于 VPS 安全保护，必须配置白名单 ID 以防服务器被未授权接管。"
        echo "👉 请在 Telegram 搜索 @userinfobot 或直接输入你的数字 ID:"
        read -r ALLOWED_UID
    done

    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    sed -i "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$TOKEN|" "$INSTALL_DIR/.env"
    sed -i "s|^AGY_BIN_PATH=.*|AGY_BIN_PATH=$FOUND_AGY|" "$INSTALL_DIR/.env"
    sed -i "s|^ALLOWED_USER_IDS=.*|ALLOWED_USER_IDS=$ALLOWED_UID|" "$INSTALL_DIR/.env"
fi

# 修正目录归属权限
if [ "$IS_ROOT" = "1" ] && id -u "$RUN_USER" >/dev/null 2>&1; then
    chown -R "$RUN_USER:$RUN_USER" "$INSTALL_DIR"
fi

# 8. 配置 systemd 常驻守护服务
if [ "$IS_ROOT" = "1" ]; then
    echo "⚙️ 正在配置 systemd 常驻守护服务..."
    sed -i "s|/opt/tg-ai-bot|$INSTALL_DIR|g" "$INSTALL_DIR/tg-ai-bot.service"
    sed -i "s|^User=.*|User=$RUN_USER|" "$INSTALL_DIR/tg-ai-bot.service"
    sed -i "s|^Group=.*|Group=$RUN_USER|" "$INSTALL_DIR/tg-ai-bot.service"
    sed -i "s|^ExecStart=.*|ExecStart=$INSTALL_DIR/venv/bin/python3 -u $INSTALL_DIR/bot.py|" "$INSTALL_DIR/tg-ai-bot.service"
    cp "$INSTALL_DIR/tg-ai-bot.service" /etc/systemd/system/tg-ai-bot.service
    systemctl daemon-reload
    systemctl enable --now tg-ai-bot
fi

# 9. 注册官方菜单
"$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/setup_menu.py" > /dev/null 2>&1 || true

echo ""
echo "======================================================="
echo "🎉 安装完成！你的云端通用自主智能体已以专用安全用户 ($RUN_USER) 稳定运行！"
echo "📊 查看运行状态: systemctl status tg-ai-bot"
echo "📄 查看实时交互日志: journalctl -u tg-ai-bot -f"
echo "💬 打开你的 Telegram 机器人，发送 /start 即可开启全自主任务！"
echo "======================================================="

