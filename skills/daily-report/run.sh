#!/bin/bash
# 日报运行脚本

cd "$(dirname "$0")"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要 Python3"
    exit 1
fi

# 运行日报生成并发送
python3 daily_report.py --send
