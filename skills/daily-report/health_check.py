#!/usr/bin/env python3
"""
健康巡检脚本 v1.0
检查项：
1. crontab任务完整性
2. 定时任务最后运行状态
3. 系统资源（CPU/内存/磁盘）
4. 关键服务进程状态
5. 日志异常检测
有异常则飞书告警
"""

import os
import sys
import re
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = Path("/var/log")

# 要检查的定时任务
CRON_JOBS = {
    "晨间新闻": {"script": "morning_news.py", "log": "morning-news.log"},
    "AI新闻抓取": {"script": "run.sh", "log": "ai-news.log"},
    "AI新闻推送": {"script": "push_email.py", "log": "ai-news.log"},
    "日报推送": {"script": "push_feishu.py", "log": "daily-report.log"},
    "Bithappy理财": {"script": "bithappy_email_pro.py", "log": "bithappy-email.log"},
    "晚间新闻": {"script": "evening_news.py", "log": "evening-news.log"},
    "加密货币监控": {"script": "crypto_monitor.py", "log": "crypto-monitor.log"},
    "技能备份": {"script": "skill-backup.sh", "log": None},
}

# 本地关键服务（OpenClaw VM）
LOCAL_SERVICES = {
    "OpenClaw Gateway": "openclaw-gateway",
}

# 远程服务器关键服务（jorge部署服务器）
REMOTE_SERVICES = {
    "Nginx": "nginx",
    "MySQL/MariaDB": "mariadb|mysql",
    "Redis": "redis-server",
    "Java后端": "jorge-ai-demo",
}


def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), 1


def check_crontab():
    """检查crontab中是否包含所有预期任务"""
    stdout, rc = run_cmd("sudo crontab -l")
    if rc != 0:
        return [("严重", "无法读取crontab，定时任务系统可能已损坏")]
    
    issues = []
    for name, cfg in CRON_JOBS.items():
        script = cfg["script"]
        if script not in stdout:
            issues.append(("严重", f"crontab中缺少任务：{name} ({script})"))
    return issues


def check_task_runs():
    """检查各任务最后运行时间"""
    issues = []
    now = datetime.now()
    
    for name, cfg in CRON_JOBS.items():
        log_file = cfg.get("log")
        if not log_file:
            continue
        
        log_path = LOG_DIR / log_file
        if not log_path.exists():
            issues.append(("警告", f"{name}：日志文件不存在 ({log_path})"))
            continue
        
        # 获取文件mtime
        mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
        hours_ago = (now - mtime).total_seconds() / 3600
        
        # 根据任务频率判断阈值
        if "crypto" in name.lower() or "bithappy" in name.lower():
            threshold = 3  # 每2-3小时应有一次
        else:
            threshold = 26  # 日报类每天一次
        
        if hours_ago > threshold:
            issues.append(("警告", f"{name}：超过{int(hours_ago)}小时未运行（阈值{threshold}h）"))
    
    return issues


def check_resources():
    """检查系统资源"""
    issues = []
    
    # CPU load
    stdout, _ = run_cmd("cat /proc/loadavg")
    try:
        load1 = float(stdout.split()[0])
        cpus, _ = run_cmd("nproc")
        cpu_count = int(cpus) if cpus else 2
        if load1 > cpu_count * 1.5:
            issues.append(("严重", f"CPU负载过高：{load1:.2f}（核心数{cpu_count}）"))
        elif load1 > cpu_count:
            issues.append(("警告", f"CPU负载偏高：{load1:.2f}（核心数{cpu_count}）"))
    except:
        pass
    
    # 内存
    stdout, _ = run_cmd("free -m | grep Mem")
    try:
        parts = stdout.split()
        total = int(parts[1])
        used = int(parts[2])
        avail = int(parts[6])
        pct = used / total * 100
        if pct > 90:
            issues.append(("严重", f"内存使用率过高：{pct:.0f}%（{used}/{total}MB）"))
        elif pct > 80:
            issues.append(("警告", f"内存使用率偏高：{pct:.0f}%（{used}/{total}MB）"))
    except:
        pass
    
    # 磁盘
    stdout, _ = run_cmd("df -h / | tail -1")
    try:
        parts = stdout.split()
        use_pct = int(parts[4].rstrip('%'))
        if use_pct > 90:
            issues.append(("严重", f"根分区使用率过高：{use_pct}%"))
        elif use_pct > 80:
            issues.append(("警告", f"根分区使用率偏高：{use_pct}%"))
    except:
        pass
    
    # Swap
    stdout, _ = run_cmd("free -m | grep Swap")
    try:
        parts = stdout.split()
        total = int(parts[1])
        used = int(parts[2])
        if total > 0:
            pct = used / total * 100
            if pct > 50:
                issues.append(("警告", f"Swap使用率偏高：{pct:.0f}%（{used}/{total}MB）"))
    except:
        pass
    
    return issues


def check_local_services():
    """检查本地关键服务"""
    issues = []
    stdout, _ = run_cmd("ps aux")
    
    for name, pattern in LOCAL_SERVICES.items():
        if not re.search(pattern, stdout, re.IGNORECASE):
            issues.append(("警告", f"本地服务未运行：{name}"))
    
    return issues


def check_remote_services():
    """通过SSH检查远程服务器服务"""
    issues = []
    ssh_key = os.path.expanduser("~/.ssh/jorge_server")
    host = "ai-worker@82.156.225.39"
    
    if not os.path.exists(ssh_key):
        issues.append(("警告", f"SSH密钥不存在：{ssh_key}"))
        return issues
    
    stdout, rc = run_cmd(f"ssh -i {ssh_key} -o ConnectTimeout=10 -o StrictHostKeyChecking=no {host} 'ps aux' 2>&1")
    
    if rc != 0:
        issues.append(("警告", f"无法连接远程服务器 ({host})：{stdout[:100]}"))
        return issues
    
    for name, pattern in REMOTE_SERVICES.items():
        if not re.search(pattern, stdout, re.IGNORECASE):
            issues.append(("严重", f"远程服务未运行：{name}"))
    
    return issues


def check_log_errors():
    """检查最近日志中的错误"""
    issues = []
    
    # 检查各日志文件最近10行是否有error
    for name, cfg in CRON_JOBS.items():
        log_file = cfg.get("log")
        if not log_file:
            continue
        log_path = LOG_DIR / log_file
        if not log_path.exists():
            continue
        
        stdout, _ = run_cmd(f"tail -n 20 {log_path}")
        error_lines = []
        for l in stdout.split('\n'):
            l_lower = l.lower()
            if any(e in l_lower for e in ['error', 'failed', 'exception', 'traceback']):
                # 过滤可预期的错误
                skip_patterns = [
                    '404 client error',
                    'not found for url',
                    '抓取失败',
                ]
                if not any(sp in l_lower for sp in skip_patterns):
                    error_lines.append(l)
        if error_lines:
            issues.append(("警告", f"{name}：最近日志有 {len(error_lines)} 条错误"))
    
    return issues


def generate_report():
    """生成巡检报告"""
    all_issues = []
    all_issues.extend([(s, m, "crontab") for s, m in check_crontab()])
    all_issues.extend([(s, m, "任务运行") for s, m in check_task_runs()])
    all_issues.extend([(s, m, "资源") for s, m in check_resources()])
    all_issues.extend([(s, m, "本地服务") for s, m in check_local_services()])
    all_issues.extend([(s, m, "远程服务") for s, m in check_remote_services()])
    all_issues.extend([(s, m, "日志") for s, m in check_log_errors()])
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if not all_issues:
        lines = [
            f"✅ 系统巡检报告 · {now}",
            "─" * 25,
            "",
            "所有检查项正常：",
            "  ✓ crontab任务完整",
            "  ✓ 定时任务运行正常",
            "  ✓ 系统资源健康",
            "  ✓ 关键服务运行中",
            "  ✓ 日志无异常",
            "",
            "🦞 权权管家健康中心",
        ]
        return "\n".join(lines), False
    
    critical = [i for i in all_issues if i[0] == "严重"]
    warnings = [i for i in all_issues if i[0] == "警告"]
    
    lines = [
        f"⚠️ 系统巡检报告 · {now}",
        "─" * 25,
        f"",
        f"发现 {len(critical)} 个严重问题，{len(warnings)} 个警告",
        "",
    ]
    
    if critical:
        lines.append("🔴 严重：")
        for sev, msg, cat in critical:
            lines.append(f"  • [{cat}] {msg}")
        lines.append("")
    
    if warnings:
        lines.append("🟡 警告：")
        for sev, msg, cat in warnings:
            lines.append(f"  • [{cat}] {msg}")
        lines.append("")
    
    lines.append("🦞 权权管家健康中心 · 请尽快处理")
    
    return "\n".join(lines), len(critical) > 0


def send_feishu(content):
    TARGET = "ou_b38c2eefcb9e3efa1a08f81b73af91c7"
    MAX_LEN = 8000
    if len(content) > MAX_LEN:
        content = content[:MAX_LEN] + "\n\n...(内容过长)"
    
    result = subprocess.run(
        [
            "/root/.nvm/versions/node/v22.22.0/bin/openclaw", "message", "send",
            "--channel", "feishu",
            "--target", TARGET,
            "--message", content,
        ],
        capture_output=True, text=True,
    )
    
    if result.returncode != 0:
        print("❌ 飞书发送失败:", result.stderr)
        return False
    print("✅ 巡检报告已发送")
    return True


def auto_fix(issues):
    """自动修复常见问题"""
    fixed = []
    
    for severity, msg, category in issues:
        # 修复1: crontab PATH丢失
        if category == "crontab" and "PATH" in msg:
            run_cmd("echo 'PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' | cat - <(sudo crontab -l) | sudo crontab -")
            fixed.append("已修复: crontab PATH环境变量")
        
        # 修复2: 日志文件缺失
        if category == "任务运行" and "日志文件不存在" in msg:
            log_match = re.search(r'\(([^)]+)\)', msg)
            if log_match:
                log_path = log_match.group(1)
                run_cmd(f"sudo touch {log_path} && sudo chmod 644 {log_path}")
                fixed.append(f"已修复: 创建日志文件 {log_path}")
        
        # 修复3: 任务超过阈值未运行 → 尝试手动执行一次
        if category == "任务运行" and "超过" in msg and "小时未运行" in msg:
            # 从消息中提取任务名，找到对应脚本
            for job_name, cfg in CRON_JOBS.items():
                if job_name in msg:
                    script = cfg["script"]
                    script_dir = cfg.get("dir", "/root/.openclaw/workspace/skills/daily-report")
                    if "ai-news" in script:
                        script_dir = "/root/.openclaw/workspace/skills/ai-news-daily"
                    run_cmd(f"cd {script_dir} && python3 {script} >> /tmp/auto-fix-{job_name}.log 2>&1 &")
                    fixed.append(f"已触发: {job_name} 手动执行")
                    break
    
    return fixed


def save_state(has_critical):
    """保存巡检状态，用于历史追踪"""
    state_file = WORKSPACE / "memory" / "health-check.json"
    state = {
        "last_check": datetime.now().isoformat(),
        "has_critical": has_critical,
    }
    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except:
        pass


def main():
    report, has_critical = generate_report()
    print(report)
    print("\n" + "=" * 30 + "\n")
    
    # 获取所有问题
    all_issues = []
    all_issues.extend([(s, m, "crontab") for s, m in check_crontab()])
    all_issues.extend([(s, m, "任务运行") for s, m in check_task_runs()])
    all_issues.extend([(s, m, "资源") for s, m in check_resources()])
    all_issues.extend([(s, m, "本地服务") for s, m in check_local_services()])
    all_issues.extend([(s, m, "远程服务") for s, m in check_remote_services()])
    all_issues.extend([(s, m, "日志") for s, m in check_log_errors()])
    
    # 尝试自动修复
    if all_issues:
        fixed = auto_fix(all_issues)
        if fixed:
            fix_msg = "\n🔧 自动修复:\n" + "\n".join(f"  • {f}" for f in fixed)
            print(fix_msg)
            report += "\n" + fix_msg
    
    send_feishu(report)
    save_state(has_critical)
    
    sys.exit(1 if has_critical else 0)


if __name__ == '__main__':
    main()
