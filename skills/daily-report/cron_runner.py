#!/usr/bin/env python3
"""
日报推送 - 用于 OpenClaw Cron
每天晚上19点发送个人日报到飞书
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")

def get_memory_content(date):
    """获取指定日期的 memory 文件内容"""
    memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
    if memory_file.exists():
        return memory_file.read_text(encoding='utf-8')
    return None

def parse_schedule(content):
    """解析日程"""
    if not content:
        return []
    
    schedule_items = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # 提取 ### 开头的日程项 (如 "### 10:30 - 12:20 健身")
        if line.startswith('### ') and any(c.isdigit() for c in line):
            item = line.lstrip('#').strip()
            if item:
                schedule_items.append(item)
    
    return schedule_items

def parse_todos(content):
    """解析待办事项"""
    if not content:
        return []
    
    todos = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # 提取待办事项 [x] 或 [ ]
        if line.startswith('- [x]') or line.startswith('- [ ]'):
            status = "✅" if '[x]' in line else "⬜"
            text = line.replace('- [x]', '').replace('- [ ]', '').strip()
            todos.append(f"{status} {text}")
    
    return todos

def generate_daily_report():
    """生成日报"""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    # 获取今日日程
    today_content = get_memory_content(today)
    today_schedule = parse_schedule(today_content) if today_content else []
    today_todos = parse_todos(today_content) if today_content else []
    
    # 获取明日日程
    tomorrow_content = get_memory_content(tomorrow)
    tomorrow_schedule = parse_schedule(tomorrow_content) if tomorrow_content else []
    
    # 构建日报
    date_str = today.strftime("%Y年%m月%d日")
    report = [f"📅 **日报 - {date_str}**", ""]
    
    # 今日日程
    report.append("📋 **今日日程**")
    if today_schedule:
        for item in today_schedule:
            report.append(f"  • {item}")
    else:
        report.append("  （暂无日程）")
    report.append("")
    
    # 今日待办
    if today_todos:
        report.append("✅ **今日待办**")
        for todo in today_todos:
            report.append(f"  {todo}")
        report.append("")
    
    # 明日日程
    report.append("📋 **明日日程**")
    if tomorrow_schedule:
        for item in tomorrow_schedule:
            report.append(f"  • {item}")
    else:
        report.append("  （暂无安排）")
    
    report.append("")
    report.append("🦞 暴躁小龙虾 · 日报")
    
    return "\n".join(report)

def main():
    """主函数"""
    report = generate_daily_report()
    print(report)

if __name__ == "__main__":
    main()
