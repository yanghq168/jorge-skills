#!/usr/bin/env python3
"""
月报生成脚本 v1.0
每月最后一天自动生成月报，包含：
1. 本月工作汇总（从日报memory文件聚合）
2. 性能趋势（CPU/内存/磁盘月度走势）
3. 定时任务执行统计
4. Agent军团动态
5. 系统事件（告警、修复记录）
6. GitHub提交统计
"""

import os
import sys
import re
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
METRICS_DIR = MEMORY_DIR / "metrics"

def get_month_dates():
    """获取本月日期列表"""
    today = datetime.now()
    # 找到本月第一天
    first_day = today.replace(day=1)
    # 找到本月最后一天
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    dates = []
    d = first_day
    while d <= last_day and d <= today:
        dates.append(d)
        d += timedelta(days=1)
    return dates

def get_monthly_work():
    """聚合本月工作记录"""
    all_work = []
    dates = get_month_dates()
    
    for date in dates:
        memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        if not memory_file.exists():
            continue
        
        content = memory_file.read_text(encoding='utf-8')
        day_work = []
        
        patterns = [
            r"- \[权权管家\] (.+)", r"- \[AI\] (.+)",
            r"- \[我\] (.+)", r"- \[暴躁小龙虾\] (.+)",
        ]
        for p in patterns:
            day_work.extend(re.findall(p, content))
        
        in_completed = False
        for line in content.split('\n'):
            line = line.strip()
            if any(m in line for m in ['## ✅', '## 完成', '## 📋', '## 今日完成']):
                in_completed = True
                continue
            if in_completed and line.startswith('## '):
                in_completed = False
                continue
            if in_completed and (line.startswith('- [x]') or line.startswith('- [X]')):
                item = line.replace('- [x]', '').replace('- [X]', '').strip()
                if item and len(item) > 3:
                    day_work.append(item)
        
        if day_work:
            all_work.append((date.strftime("%m-%d"), day_work))
    
    return all_work

def get_monthly_metrics():
    """获取本月性能趋势"""
    dates = get_month_dates()
    trends = []
    
    for date in dates:
        file_path = METRICS_DIR / f"{date.strftime('%Y-%m-%d')}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if data:
                    cpu_vals = [d["cpu"].get("usage", 0) for d in data if d.get("cpu") and d["cpu"].get("usage") is not None]
                    mem_vals = [d["memory"].get("usage_pct", 0) for d in data if d.get("memory") and d["memory"].get("usage_pct") is not None]
                    
                    trends.append({
                        "date": date.strftime("%m-%d"),
                        "cpu_avg": round(sum(cpu_vals)/len(cpu_vals), 1) if cpu_vals else None,
                        "mem_avg": round(sum(mem_vals)/len(mem_vals), 1) if mem_vals else None,
                        "samples": len(data),
                    })
            except:
                pass
    
    return trends

def get_task_stats():
    """统计本月定时任务执行情况"""
    stats = {}
    dates = get_month_dates()
    
    logs = {
        "AI新闻": "ai-news.log",
        "日报推送": "daily-report.log",
        "晨间新闻": "morning-news.log",
        "晚间新闻": "evening-news.log",
        "加密货币": "crypto-monitor.log",
        "理财监控": "bithappy-email.log",
        "系统巡检": "health-check.log",
    }
    
    for name, logfile in logs.items():
        log_path = Path("/var/log") / logfile
        if not log_path.exists():
            continue
        
        success_count = 0
        for date in dates:
            date_str = date.strftime("%Y-%m-%d")
            stdout = subprocess.run(
                f"grep '{date_str}' {log_path} | grep -c '✅'",
                shell=True, capture_output=True, text=True, timeout=5
            ).stdout.strip()
            try:
                success_count += int(stdout)
            except:
                pass
        
        stats[name] = success_count
    
    return stats

def get_github_stats():
    """获取本月GitHub提交统计"""
    repo_dir = WORKSPACE / "jorge-ai-repository"
    if not (repo_dir / ".git").exists():
        return 0
    
    today = datetime.now()
    first_day = today.replace(day=1).strftime("%Y-%m-%d")
    
    stdout = subprocess.run(
        f"cd {repo_dir} && git log --since='{first_day}' --oneline --no-decorate | wc -l",
        shell=True, capture_output=True, text=True, timeout=10
    ).stdout.strip()
    
    try:
        return int(stdout)
    except:
        return 0

def generate_monthly_report():
    """生成月报文本"""
    today = datetime.now()
    month_start = today.replace(day=1)
    
    lines = []
    lines.append(f"📊 月报 · {today.strftime('%Y年%m月')}")
    lines.append("═" * 40)
    lines.append("")
    
    # 1. 本月工作汇总
    monthly_work = get_monthly_work()
    if monthly_work:
        lines.append("🦞 本月工作汇总")
        total_items = 0
        total_days = 0
        for date_str, work_items in monthly_work:
            total_items += len(work_items)
            total_days += 1
        lines.append(f"  记录天数: {total_days} 天")
        lines.append(f"  工作项: {total_items} 项")
        lines.append(f"  日均: {round(total_items/total_days, 1) if total_days > 0 else 0} 项")
        lines.append("")
    else:
        lines.append("🦞 本月工作汇总")
        lines.append("  • 暂无记录")
        lines.append("")
    
    # 2. 性能趋势
    trends = get_monthly_metrics()
    if trends:
        lines.append("📈 本月性能趋势")
        cpu_vals = [t['cpu_avg'] for t in trends if t['cpu_avg'] is not None]
        mem_vals = [t['mem_avg'] for t in trends if t['mem_avg'] is not None]
        
        if cpu_vals:
            lines.append(f"  CPU平均: {round(sum(cpu_vals)/len(cpu_vals), 1)}%")
        if mem_vals:
            lines.append(f"  内存平均: {round(sum(mem_vals)/len(mem_vals), 1)}%")
        lines.append(f"  采样天数: {len(trends)} 天")
        lines.append("")
    
    # 3. 定时任务统计
    stats = get_task_stats()
    if stats:
        lines.append("⏰ 定时任务本月执行统计")
        for name, count in stats.items():
            status = "✅" if count > 0 else "⚪"
            lines.append(f"  {status} {name}: {count}次成功")
        lines.append("")
    
    # 4. GitHub提交
    github_count = get_github_stats()
    if github_count > 0:
        lines.append(f"🐙 GitHub提交: {github_count} 次")
        lines.append("")
    
    # 5. Agent统计
    agents_dir = WORKSPACE / "agency-agents"
    agent_count = 0
    if agents_dir.exists():
        for _ in agents_dir.rglob("*.md"):
            agent_count += 1
    lines.append(f"🤖 Agent军团: {agent_count} 个")
    lines.append("")
    
    lines.append("═" * 40)
    lines.append("🦞 权权管家指挥中心 · 自动生成")
    
    return "\n".join(lines)

def send_feishu(content):
    TARGET = "ou_b38c2eefcb9e3efa1a08f81b73af91c7"
    result = subprocess.run(
        [
            "/root/.nvm/versions/node/v22.22.0/bin/openclaw", "message", "send",
            "--channel", "feishu", "--target", TARGET, "--message", content,
        ],
        capture_output=True, text=True,
    )
    return result.returncode == 0

def main():
    content = generate_monthly_report()
    print(content)
    print("\n" + "=" * 30 + "\n")
    success = send_feishu(content)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
