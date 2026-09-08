#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ -f "$DIR/bot.pid" ]; then
    PID=$(cat "$DIR/bot.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️ Bot 已在运行中 (PID: $PID)"
        exit 0
    else
        rm -f "$DIR/bot.pid"
    fi
fi

echo "🚀 正在启动 Telegram AI Bot..."
nohup "$DIR/venv/bin/python3" -u "$DIR/bot.py" >> "$DIR/bot.log" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$DIR/bot.pid"
sleep 2

if ps -p "$NEW_PID" > /dev/null 2>&1; then
    echo "✅ 启动成功！进程 PID: $NEW_PID"
    echo "📄 查看实时日志: tail -f $DIR/bot.log"
else
    echo "❌ 启动失败，请检查日志:"
    tail -n 20 "$DIR/bot.log"
fi
