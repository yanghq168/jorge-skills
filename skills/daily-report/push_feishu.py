#!/usr/bin/env python3
"""
日报飞书推送脚本 - v2.0 增强版
数据源：
1. memory工作记录
2. 今日脚本/技能新建或修改
3. 定时任务执行状态
4. 远程服务器运维记录
5. 系统巡检状态
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
SKILL_DIR = WORKSPACE / "skills"
SCRIPT_DIR = WORKSPACE / "scripts"
LOG_DIR = Path("/var/log")


def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return r.stdout.strip(), r.returncode
    except:
        return "", 1


def get_quanquan_work(date):
    """从memory文件提取工作记录"""
    memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
    if not memory_file.exists():
        return []

    content = memory_file.read_text(encoding='utf-8')
    work_items = []

    patterns = [
        r"- \[权权管家\] (.+)", r"- \[AI\] (.+)",
        r"- \[我\] (.+)", r"- \[暴躁小龙虾\] (.+)"
    ]
    for p in patterns:
        work_items.extend(re.findall(p, content))

    schedule_matches = re.findall(r"###\s+(\d{2}:\d{2}(?:\s+-\s+\d{2}:\d{2})?)\s+(.+)", content)
    for time_range, task in schedule_matches:
        work_items.append(f"[{time_range}] {task.strip()}")

    in_completed = False
    for line in content.split('\n'):
        line = line.strip()
        if any(m in line for m in ['## ✅', '## 完成', '## 📋', '## 今日完成']):
            in_completed = True
            continue
        if in_completed and line.startswith('## ') and '完成' not in line and '✅' not in line:
            in_completed = False
            continue
        if in_completed:
            if line.startswith('- [x]') or line.startswith('- [X]'):
                item = line.replace('- [x]', '').replace('- [X]', '').strip()
                if item and item not in work_items:
                    work_items.append(item)
            elif line.startswith('- ') and not line.startswith('- [ ]'):
                item = re.sub(r'\*\*(.+?)\*\*', r'\1', line[2:].strip())
                if item and len(item) > 3 and item not in work_items:
                    work_items.append(item)

    for line in content.split('\n'):
        if line.startswith('- **') and any(k in line for k in ['完成', '修复', '创建', '配置', '部署', '优化', '添加', '更新', '设置', '生成', '推送', '翻译', '备份', '新增']):
            item = line.lstrip('- **').rstrip('**').strip()
            if not any(skip in item.lower() for skip in ['最后更新', 'agent 总数']):
                if item not in work_items:
                    work_items.append(item)

    return work_items


def get_today_file_changes():
    """今天新建或修改的文件/技能"""
    items = []
    today = datetime.now().strftime("%Y-%m-%d")

    for d in SKILL_DIR.iterdir():
        if d.is_dir() and d.name not in ('__pycache__', '.git'):
            try:
                mtime = datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d")
                if mtime == today:
                    items.append(f"技能更新: {d.name}")
            except:
                pass

    for f in SCRIPT_DIR.glob("*.py"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
            if mtime == today:
                items.append(f"脚本更新: {f.name}")
        except:
            pass

    today_memory = MEMORY_DIR / f"{today}.md"
    if today_memory.exists():
        items.append("生成今日记忆日志")

    return items


def get_task_execution_status():
    """今日定时任务执行状态"""
    status = []
    date_str = datetime.now().strftime("%Y-%m-%d")

    logs = {
        "AI新闻": "ai-news.log",
        "日报推送": "daily-report.log",
        "晨间新闻": "morning-news.log",
        "晚间新闻": "evening-news.log",
        "加密货币": "crypto-monitor.log",
        "理财监控": "bithappy-email.log",
    }

    for name, logfile in logs.items():
        log_path = LOG_DIR / logfile
        if log_path.exists():
            mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
            if mtime.strftime("%Y-%m-%d") == date_str:
                stdout, _ = run_cmd(f"tail -n 5 {log_path}")
                if '✅' in stdout or '成功' in stdout or 'Sent' in stdout or '推送完成' in stdout:
                    status.append(f"✅ {name}")
                else:
                    status.append(f"🟡 {name} (无成功标记)")
            else:
                status.append(f"⚪ {name} (今日未更新)")
        else:
            status.append(f"❓ {name} (日志缺失)")

    return status


def get_remote_server_ops():
    """今日远程服务器运维记录"""
    items = []
    ssh_key = os.path.expanduser("~/.ssh/jorge_server")
    host = "ai-worker@82.156.225.39"

    stdout, rc = run_cmd(f"ssh -i {ssh_key} -o ConnectTimeout=5 {host} 'uptime' 2>/dev/null")
    if rc == 0 and stdout:
        items.append(f"服务器在线: {stdout}")

    stdout, rc = run_cmd(f"ssh -i {ssh_key} -o ConnectTimeout=5 {host} 'df -h / | tail -1' 2>/dev/null")
    if rc == 0 and stdout:
        parts = stdout.split()
        if len(parts) >= 5:
            items.append(f"磁盘: {parts[4]}")

    return items


def get_system_health():
    """今日巡检状态"""
    health_file = WORKSPACE / "memory" / "health-check.json"
    if health_file.exists():
        try:
            with open(health_file, 'r') as f:
                data = json.load(f)
                last_check = data.get('last_check', '')
                has_critical = data.get('has_critical', False)
                if last_check and datetime.fromisoformat(last_check).strftime("%Y-%m-%d") == datetime.now().strftime("%Y-%m-%d"):
                    return "🔴 今日巡检发现严重问题" if has_critical else "✅ 今日巡检正常"
        except:
            pass
    return "⚪ 今日巡检未执行"


def get_agent_count():
    """统计Agent总数"""
    agents_dir = WORKSPACE / "agency-agents"
    count = 0
    if agents_dir.exists():
        for _ in agents_dir.rglob("*.md"):
            count += 1
    return count


def get_github_commits():
    """获取今日GitHub提交记录"""
    items = []
    repo_dir = WORKSPACE / "jorge-ai-repository"
    if not (repo_dir / ".git").exists():
        return items
    
    today = datetime.now().strftime("%Y-%m-%d")
    stdout, rc = run_cmd(f"cd {repo_dir} && git log --since='{today} 00:00' --until='{today} 23:59' --oneline --no-decorate 2>/dev/null")
    
    if rc == 0 and stdout.strip():
        for line in stdout.strip().split('\n'):
            line = line.strip()
            if line:
                # 格式: hash message
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    items.append(parts[1])
                else:
                    items.append(line)
    
    return items
    """获取优化记录"""
    memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
    if not memory_file.exists():
        return []

    content = memory_file.read_text(encoding='utf-8')
    optimizations = []
    patterns = [
        (r'- \[优化\] (.+)', '优化'), (r'- \[改进\] (.+)', '改进'),
        (r'- \[重构\] (.+)', '重构'), (r'- \[更新\] (.+)', '更新'),
    ]
    for pattern, opt_type in patterns:
        for match in re.findall(pattern, content):
            optimizations.append({'type': opt_type, 'description': match})
    return optimizations


def generate_daily_report_text():
    """生成飞书格式的日报文本"""
    today = datetime.now()
    date_str = today.strftime("%Y年%m月%d日")
    weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][today.weekday()]

    lines = []
    lines.append(f"📋 每日工作日报 · {date_str} ({weekday})")
    lines.append("─" * 30)
    lines.append("")

    # 1. 权权管家工作记录
    work_items = get_quanquan_work(today)
    if work_items:
        lines.append("🦞 权权管家今日工作")
        for item in work_items:
            lines.append(f"  • {item}")
    else:
        lines.append("🦞 权权管家今日工作")
        lines.append("  • 暂无记录")
    lines.append("")

    # 2. 今日文件/技能变更
    changes = get_today_file_changes()
    if changes:
        lines.append("🛠️ 今日变更")
        for c in changes:
            lines.append(f"  • {c}")
        lines.append("")

    # 3. 定时任务执行状态
    task_status = get_task_execution_status()
    if task_status:
        lines.append("⏰ 定时任务状态")
        for s in task_status:
            lines.append(f"  {s}")
        lines.append("")

    # 4. 远程服务器状态
    remote_ops = get_remote_server_ops()
    # 远程性能数据
    remote_metrics_file = WORKSPACE / "memory" / "metrics" / "remote" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    if remote_metrics_file.exists():
        try:
            with open(remote_metrics_file, 'r') as f:
                remote_data = json.load(f)
            if remote_data:
                latest = remote_data[-1]
                mem = latest.get('memory', {}).get('usage_pct')
                disk = latest.get('disk', {}).get('usage_pct')
                load = latest.get('load', {}).get('1min')
                remote_ops.append(f"资源: 内存{mem}% | 磁盘{disk}% | 负载{load}")
        except:
            pass
    if remote_ops:
        lines.append("🖥️ 服务器状态")
        for op in remote_ops:
            lines.append(f"  • {op}")
        lines.append("")

    # 5. 系统健康
    health = get_system_health()
    lines.append(f"🔍 系统巡检: {health}")
    lines.append("")

    # 6. Agent优化
    optimizations = get_optimizations(today)
    if optimizations:
        lines.append(f"🚀 Agent优化（{len(optimizations)}项）")
        for opt in optimizations:
            lines.append(f"  • [{opt['type']}] {opt['description']}")
        lines.append("")

    # 7. GitHub提交记录
    github_commits = get_github_commits()
    if github_commits:
        lines.append(f"🐙 GitHub提交（{len(github_commits)}项）")
        for commit in github_commits:
            lines.append(f"  • {commit}")
        lines.append("")

    # 8. Agent统计
    agent_count = get_agent_count()
    lines.append(f"🤖 Agent军团: {agent_count} 个待命")
    lines.append("")

    # 底部
    lines.append("─" * 30)
    lines.append("🦞 权权管家指挥中心 · 自动生成")

    return "\n".join(lines)


def get_optimizations(date):
    """获取优化记录"""
    memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
    if not memory_file.exists():
        return []

    content = memory_file.read_text(encoding='utf-8')
    optimizations = []
    patterns = [
        (r'- \[优化\] (.+)', '优化'), (r'- \[改进\] (.+)', '改进'),
        (r'- \[重构\] (.+)', '重构'), (r'- \[更新\] (.+)', '更新'),
    ]
    for pattern, opt_type in patterns:
        for match in re.findall(pattern, content):
            optimizations.append({'type': opt_type, 'description': match})
    return optimizations


def send_feishu_message(content):
    TARGET = "ou_b38c2eefcb9e3efa1a08f81b73af91c7"
    MAX_LEN = 8000
    if len(content) > MAX_LEN:
        content = content[:MAX_LEN] + "\n\n...(内容过长，已截断)"

    result = subprocess.run(
        [
            "/root/.nvm/versions/node/v22.22.0/bin/openclaw", "message", "send",
            "--channel", "feishu", "--target", TARGET, "--message", content,
        ], capture_output=True, text=True,
    )

    print(result.stdout)
    if result.returncode != 0:
        print("❌ 发送失败:", result.stderr)
        return False
    print("✅ 日报飞书推送完成")
    return True


def main():
    content = generate_daily_report_text()
    print(content)
    print("\n" + "=" * 30 + "\n")
    success = send_feishu_message(content)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
