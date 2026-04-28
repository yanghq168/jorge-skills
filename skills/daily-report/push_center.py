#!/usr/bin/env python3
"""
统一推送中心 v1.0
所有渠道的推送统一走这里
支持：飞书、邮件
策略：紧急简短 → 飞书，详细报告 → 邮件
"""

import os
import sys
import json
import smtplib
import subprocess
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

WORKSPACE = Path("/root/.openclaw/workspace")
CONFIG_FILE = WORKSPACE / "skills" / "daily-report" / "config.json"

# 飞书目标用户
FEISHU_TARGET = "ou_b38c2eefcb9e3efa1a08f81b73af91c7"
OPENCLAW_BIN = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def send_feishu(content, target=None):
    """飞书推送"""
    target = target or FEISHU_TARGET
    MAX_LEN = 8000
    if len(content) > MAX_LEN:
        content = content[:MAX_LEN] + "\n\n...(内容过长，已截断)"
    
    result = subprocess.run(
        [
            OPENCLAW_BIN, "message", "send",
            "--channel", "feishu",
            "--target", target,
            "--message", content,
        ],
        capture_output=True, text=True,
    )
    
    if result.returncode != 0:
        print(f"❌ 飞书发送失败: {result.stderr}")
        return False
    return True


def send_email(subject, html_content, text_content, to_email=None):
    """邮件发送"""
    config = load_config()
    
    smtp_server = config.get('smtp_server', 'smtp.qq.com')
    smtp_port = config.get('smtp_port', 465)
    smtp_user = config.get('smtp_user')
    smtp_pass = config.get('smtp_pass')
    
    if not smtp_user or not smtp_pass:
        print("❌ 邮件配置不完整")
        return False
    
    if not to_email:
        to_email = config.get('to_email', smtp_user)
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"=?utf-8?b?5p2D5p2D5YW755qE6Jm+77yI566h5a6277yJ?= <{smtp_user}>"
        msg['To'] = to_email
        
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        if smtp_port == 465 or 'qq.com' in smtp_server:
            server = smtplib.SMTP_SSL(smtp_server, 465)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


def push(content, subject=None, html=None, channel="auto", target=None):
    """
    统一推送入口
    channel:
      - "auto": 根据内容长度自动选择（<1000字飞书，>1000字邮件）
      - "feishu": 强制飞书
      - "email": 强制邮件
      - "both": 双通道
    """
    text = content
    
    # 自动判断策略
    if channel == "auto":
        if len(text) < 1000:
            channel = "feishu"
        else:
            channel = "email"
    
    results = {}
    
    if channel in ("feishu", "both"):
        results['feishu'] = send_feishu(text, target)
    
    if channel in ("email", "both"):
        subj = subject or "权权管家通知"
        html_body = html or f"<pre style='font-size:14px'>{text}</pre>"
        results['email'] = send_email(subj, html_body, text)
    
    return results


def push_alert(title, message, level="warning"):
    """紧急告警推送 - 双通道确保送达"""
    emoji = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(level, "🟡")
    content = f"{emoji} {title}\n\n{message}\n\n🦞 权权管家告警中心"
    return push(content, subject=f"{emoji} {title}", channel="both")


def push_summary(title, text_content, html_content=None):
    """日报/总结类推送 - 飞书预览 + 邮件详情"""
    # 飞书发精简版
    feishu_text = f"{title}\n\n{text_content[:800]}\n\n...(完整内容见邮件)\n\n🦞 权权管家"
    send_feishu(feishu_text)
    
    # 邮件发完整版
    subj = title.replace("📋", "").replace("🤖", "").strip()
    html = html_content or f"<pre style='font-size:14px'>{text_content}</pre>"
    send_email(f"📋 {subj}", html, text_content)


if __name__ == '__main__':
    # 测试
    if len(sys.argv) > 1:
        push(" ".join(sys.argv[1:]), channel="auto")
    else:
        print("统一推送中心就绪")
