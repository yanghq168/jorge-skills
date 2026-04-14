#!/usr/bin/env python3
import subprocess
from pathlib import Path

MSG_FILE = Path("/root/.openclaw/workspace/skills/ai-news-daily/data/openclaw_message.txt")
TARGET = "ou_b38c2eefcb9e3efa1a08f81b73af91c7"

if not MSG_FILE.exists():
    print("❌ 消息文件不存在")
    exit(1)

content = MSG_FILE.read_text(encoding="utf-8").strip()
if not content:
    print("❌ 消息内容为空")
    exit(1)

# 飞书单条消息有长度限制，如果超长需要截断
MAX_LEN = 8000
if len(content) > MAX_LEN:
    content = content[:MAX_LEN] + "\n\n...(内容过长，已截断)"

result = subprocess.run(
    [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", TARGET,
        "--message", content,
    ],
    capture_output=True,
    text=True,
)

print(result.stdout)
if result.returncode != 0:
    print("❌ 发送失败:", result.stderr)
    exit(1)

print("✅ AI 新闻推送完成")
