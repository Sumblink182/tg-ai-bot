#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ -f "$DIR/bot.pid" ]; then
    PID=$(cat "$DIR/bot.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🛑 正在停止 Bot (PID: $PID)..."
        kill "$PID"
        sleep 1
        if ps -p "$PID" > /dev/null 2>&1; then
            kill -9 "$PID"
        fi
        rm -f "$DIR/bot.pid"
        echo "✅ Bot 已停止。"
    else
        echo "⚠️ 进程 $PID 未在运行，正在清理 pid 文件..."
        rm -f "$DIR/bot.pid"
    fi
else
    echo "⚠️ 未找到 bot.pid，尝试通过进程名停止..."
    pkill -f "$DIR/bot.py" && echo "✅ 已停止相关进程。" || echo "未找到运行中的实例。"
fi
