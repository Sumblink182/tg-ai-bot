#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ -f "$DIR/bot.pid" ]; then
    PID=$(cat "$DIR/bot.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🟢 Bot 正在正常运行 (PID: $PID)"
    else
        echo "🔴 Bot 未在运行 (残留无效 PID: $PID)"
    fi
else
    echo "⚪ Bot 未运行"
fi

if [ -f "$DIR/bot.log" ]; then
    echo "--- 最近 10 行日志 ---"
    tail -n 10 "$DIR/bot.log"
fi
