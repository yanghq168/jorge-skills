#!/usr/bin/env python3
"""
周报生成脚本 v1.0
每周日自动生成周报，包含：
1. 本周工作汇总（从日报memory文件聚合）
2. 性能趋势（CPU/内存/磁盘7天走势）
3. 定时任务执行统计
4. Agent军团动态
5. 系统事件（告警、修复记录）
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


def get_week_dates():
    """获取本周日期列表（周一到周日）"""
    today = datetime.now()
    # 找到本周一
    monday = today - timedelta(days=today.weekday())
    dates = []
    for i in range(7):
        d = monday + timedelta(days=i)
        dates.append(d)
    return dates


def get_weekly_work():
    """聚合本周工作记录"""
    all_work = []
    dates = get_week_dates()
    
    for date in dates:
        memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        if not memory_file.exists():
            continue
        
        content = memory_file.read_text(encoding='utf-8')
        day_work = []
        
        # 匹配工作记录
        patterns = [
            r"- \[权权管家\] (.+)", r"- \[AI\] (.+)",
            r"- \[我\] (.+)", r"- \[暴躁小龙虾\] (.+)",
        ]
        for p in patterns:
            day_work.extend(re.findall(p, content))
        
        # 匹配完成事项
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


def get_weekly_remote_metrics():
    """获取远程服务器本周性能趋势"""
    dates = get_week_dates()
    trends = []
    remote_dir = METRICS_DIR / "remote"
    
    for date in dates:
        file_path = remote_dir / f"{date.strftime('%Y-%m-%d')}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if data:
                    mem_vals = [d["memory"].get("usage_pct", 0) for d in data if d.get("memory") and d["memory"].get("usage_pct") is not None]
                    disk_vals = [d["disk"].get("usage_pct", 0) for d in data if d.get("disk") and d["disk"].get("usage_pct") is not None]
                    load_vals = [d["load"].get("1min", 0) for d in data if d.get("load") and d["load"].get("1min") is not None]
                    
                    trends.append({
                        "date": date.strftime("%m-%d"),
                        "mem_avg": round(sum(mem_vals)/len(mem_vals), 1) if mem_vals else None,
                        "disk_avg": round(sum(disk_vals)/len(disk_vals), 1) if disk_vals else None,
                        "load_avg": round(sum(load_vals)/len(load_vals), 2) if load_vals else None,
                        "samples": len(data),
                    })
            except:
                pass
    
    return trends


def get_weekly_metrics():
    """获取本周性能趋势"""
    dates = get_week_dates()
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
    """统计本周定时任务执行情况"""
    stats = {}
    dates = get_week_dates()
    
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
        
        # 统计本周成功次数
        success_count = 0
        for date in dates:
            date_str = date.strftime("%Y-%m-%d")
            stdout, _ = subprocess.run(
                f"grep '{date_str}' {log_path} | grep -c '✅'",
                shell=True, capture_output=True, text=True, timeout=5
            ).stdout.strip(), 0
            try:
                success_count += int(stdout)
            except:
                pass
        
        stats[name] = success_count
    
    return stats


def get_system_events():
    """获取本周系统事件（告警、修复）"""
    events = []
    dates = get_week_dates()
    
    # 从health-check日志中提取告警
    health_log = Path("/var/log/health-check.log")
    if health_log.exists():
        for date in dates:
            date_str = date.strftime("%Y-%m-%d")
            stdout, _ = subprocess.run(
                f"grep '{date_str}' {health_log} | grep -E '严重|警告' | tail -5",
                shell=True, capture_output=True, text=True, timeout=5
            ).stdout, 0
            if stdout.strip():
                events.append((date.strftime("%m-%d"), "系统巡检告警", stdout.strip()))
    
    # 从memory文件提取授权/配置变更
    for date in dates:
        memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        if not memory_file.exists():
            continue
        
        content = memory_file.read_text(encoding='utf-8')
        if "授权" in content or "服务器权限" in content or "部署" in content:
            events.append((date.strftime("%m-%d"), "重要配置变更", "检测到权限/部署相关记录"))
    
    return events


def generate_weekly_report():
    """生成周报文本"""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    lines = []
    lines.append(f"📊 周报 · {week_start.strftime('%m月%d日')} ~ {week_end.strftime('%m月%d日')}")
    lines.append("═" * 40)
    lines.append("")
    
    # 1. 本周工作汇总
    weekly_work = get_weekly_work()
    if weekly_work:
        lines.append("🦞 本周工作汇总")
        total_items = 0
        for date_str, work_items in weekly_work:
            lines.append(f"  [{date_str}] {len(work_items)}项")
            for item in work_items[:3]:  # 每天只显示前3项
                lines.append(f"    • {item}")
            if len(work_items) > 3:
                lines.append(f"    ... 还有{len(work_items)-3}项")
            total_items += len(work_items)
        lines.append(f"  合计: {total_items} 项工作记录")
        lines.append("")
    else:
        lines.append("🦞 本周工作汇总")
        lines.append("  • 暂无记录")
        lines.append("")
    
    # 2. 性能趋势
    trends = get_weekly_metrics()
    remote_trends = get_weekly_remote_metrics()
    if trends or remote_trends:
        lines.append("📈 本周性能趋势（每4小时采样）")
        if trends:
            lines.append("  [本地]")
            for t in trends:
                cpu_str = f"CPU{t['cpu_avg']}%" if t['cpu_avg'] is not None else "CPU-"
                mem_str = f"内存{t['mem_avg']}%" if t['mem_avg'] is not None else "内存-"
                lines.append(f"    [{t['date']}] {cpu_str} | {mem_str} | {t['samples']}次")
        if remote_trends:
            lines.append("  [远程 82.156.225.39]")
            for t in remote_trends:
                mem_str = f"内存{t['mem_avg']}%" if t['mem_avg'] is not None else "内存-"
                disk_str = f"磁盘{t['disk_avg']}%" if t['disk_avg'] is not None else "磁盘-"
                load_str = f"负载{t['load_avg']}" if t['load_avg'] is not None else "负载-"
                lines.append(f"    [{t['date']}] {mem_str} | {disk_str} | {load_str} | {t['samples']}次")
        lines.append("")
    
    # 3. 定时任务统计
    stats = get_task_stats()
    if stats:
        lines.append("⏰ 定时任务本周执行统计")
        for name, count in stats.items():
            status = "✅" if count > 0 else "⚪"
            lines.append(f"  {status} {name}: {count}次成功")
        lines.append("")
    
    # 4. 系统事件
    events = get_system_events()
    if events:
        lines.append("🔔 本周系统事件")
        for date_str, event_type, detail in events[:5]:
            lines.append(f"  [{date_str}] {event_type}")
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
    MAX_LEN = 8000
    if len(content) > MAX_LEN:
        content = content[:MAX_LEN] + "\n\n...(内容过长)"
    
    result = subprocess.run(
        [
            "/root/.nvm/versions/node/v22.22.0/bin/openclaw", "message", "send",
            "--channel", "feishu", "--target", TARGET, "--message", content,
        ],
        capture_output=True, text=True,
    )
    
    if result.returncode != 0:
        print("❌ 发送失败:", result.stderr)
        return False
    print("✅ 周报飞书推送完成")
    return True


def main():
    content = generate_weekly_report()
    print(content)
    print("\n" + "=" * 30 + "\n")
    success = send_feishu(content)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
