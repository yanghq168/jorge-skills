#!/usr/bin/env python3
"""
AI新闻邮件推送脚本
替代飞书推送，改为邮件推送
"""

import json
import smtplib
import re
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 配置
MSG_FILE = Path("/root/.openclaw/workspace/skills/ai-news-daily/data/openclaw_message.txt")
CONFIG_FILE = Path("/root/.openclaw/workspace/skills/daily-report/config.json")

def load_config():
    """加载邮件配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def parse_news_content(text):
    """解析新闻内容，提取标题和条目"""
    lines = text.strip().split('\n')
    
    # 提取日期
    date_match = re.search(r'(\d{4}年\d{2}月\d{2}日)', text)
    date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y年%m月%d日")
    
    # 提取总条数
    count_match = re.search(r'共\s*(\d+)\s*条', text)
    total_count = count_match.group(1) if count_match else "?"
    
    # 解析每条新闻
    news_items = []
    current_item = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 匹配标题行: **1. [来源] 标题**
        title_match = re.match(r'\*\*\d+\.\s*\[([^\]]+)\]\s*(.+?)\*\*', line)
        if title_match:
            if current_item:
                news_items.append(current_item)
            current_item = {
                'source': title_match.group(1),
                'title': title_match.group(2),
                'summary': '',
                'link': ''
            }
            continue
        
        # 匹配链接行
        link_match = re.search(r'\[阅读原文\]\((https?://[^\s\)]+)\)', line)
        if link_match and current_item:
            current_item['link'] = link_match.group(1)
            continue
        
        # 忽略分隔线和日期行
        if line.startswith('─') or line.startswith('📰') or line.startswith('共'):
            continue
        
        # 其他内容作为摘要
        if current_item and line and not line.startswith('🔗'):
            # 清理AI生成的冗余文案
            cleaned = re.sub(r'详细内容请点击阅读原文链接查看完整报道.*$', '', line)
            cleaned = re.sub(r'本文内容经 AI 智能整理.*$', '', cleaned)
            cleaned = re.sub(r'更多相关信息和深度分析.*$', '', cleaned)
            cleaned = re.sub(r'如需了解完整内容.*$', '', cleaned)
            cleaned = re.sub(r'我们持续跟踪报道.*$', '', cleaned)
            cleaned = re.sub(r'本文涉及的技术细节.*$', '', cleaned)
            cleaned = re.sub(r'想要了解更多背景信息.*$', '', cleaned)
            cleaned = cleaned.strip()
            if cleaned and len(cleaned) > 10:
                current_item['summary'] += cleaned + ' '
    
    # 添加最后一个
    if current_item:
        news_items.append(current_item)
    
    # 清理摘要
    for item in news_items:
        item['summary'] = item['summary'].strip()
    
    return date_str, total_count, news_items


def generate_news_html(date_str, total_count, news_items):
    """生成新闻邮件HTML"""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        }}
        .container {{
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .header {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
            font-weight: 700;
        }}
        .header .subtitle {{
            margin-top: 8px;
            font-size: 16px;
            opacity: 0.9;
        }}
        .header .meta {{
            margin-top: 12px;
            font-size: 14px;
            opacity: 0.85;
        }}
        .content {{
            padding: 30px;
        }}
        .news-item {{
            background: #f8f9fa;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            transition: transform 0.2s;
        }}
        .news-item:hover {{
            transform: translateX(5px);
        }}
        .news-number {{
            display: inline-block;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            text-align: center;
            line-height: 28px;
            font-weight: 700;
            font-size: 14px;
            margin-right: 10px;
        }}
        .news-source {{
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
        }}
        .news-title {{
            font-size: 18px;
            font-weight: 700;
            color: #2c3e50;
            margin: 10px 0;
            line-height: 1.4;
        }}
        .news-summary {{
            color: #6c757d;
            font-size: 14px;
            line-height: 1.8;
            margin: 12px 0;
        }}
        .news-link {{
            display: inline-block;
            margin-top: 10px;
            padding: 8px 20px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        .news-link:hover {{
            opacity: 0.9;
        }}
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 30px;
            padding-top: 24px;
            border-top: 2px solid #e9ecef;
            font-size: 13px;
            color: #6c757d;
        }}
        .stats-bar strong {{
            color: #2c3e50;
        }}
        .footer {{
            text-align: center;
            padding: 24px;
            color: #adb5bd;
            font-size: 12px;
            background: #f8f9fa;
        }}
        @media (max-width: 600px) {{
            body {{ padding: 10px; }}
            .header {{ padding: 30px 20px; }}
            .header h1 {{ font-size: 24px; }}
            .content {{ padding: 20px; }}
            .news-item {{ padding: 16px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 AI 每日新闻</h1>
            <div class="subtitle">精选全球AI行业最新动态</div>
            <div class="meta">⏰ {date_str} · 🤖 权权管家自动抓取</div>
        </div>
        <div class="content">
"""
    
    # 添加新闻条目
    for i, item in enumerate(news_items, 1):
        summary = item['summary'][:300] + '...' if len(item['summary']) > 300 else item['summary']
        link_html = f'<a href="{item["link"]}" class="news-link" target="_blank">🔗 阅读原文</a>' if item['link'] else ''
        
        html += f"""
        <div class="news-item">
            <div>
                <span class="news-number">{i}</span>
                <span class="news-source">{item['source']}</span>
            </div>
            <div class="news-title">{item['title']}</div>
            <div class="news-summary">{summary}</div>
            {link_html}
        </div>
"""
    
    # 页脚
    html += f"""
        </div>
        <div class="stats-bar">
            <div>📊 精选 <strong>{len(news_items)}</strong> 条新闻</div>
            <div>📅 {date_str}</div>
        </div>
        <div class="footer">
            🦞 权权管家 · AI新闻日报 · 每日 9:00 自动推送
        </div>
    </div>
</body>
</html>"""
    
    return html


def generate_news_text(date_str, total_count, news_items):
    """生成纯文本版本"""
    lines = [
        "=" * 50,
        f"📰 AI 每日新闻 - {date_str}",
        "=" * 50,
        ""
    ]
    
    for i, item in enumerate(news_items, 1):
        lines.append(f"【{i}】[{item['source']}] {item['title']}")
        if item['summary']:
            summary = item['summary'][:200] + '...' if len(item['summary']) > 200 else item['summary']
            lines.append(f"    {summary}")
        if item['link']:
            lines.append(f"    🔗 {item['link']}")
        lines.append("")
    
    lines.extend([
        "=" * 50,
        f"🦞 权权管家 · 共 {len(news_items)} 条新闻",
        "=" * 50
    ])
    
    return '\n'.join(lines)


def send_news_email():
    """发送AI新闻邮件"""
    
    # 检查消息文件
    if not MSG_FILE.exists():
        print("❌ 消息文件不存在")
        return False
    
    content = MSG_FILE.read_text(encoding='utf-8').strip()
    if not content:
        print("❌ 消息内容为空")
        return False
    
    # 加载配置
    config = load_config()
    
    smtp_server = config.get('smtp_server', 'smtp.qq.com')
    smtp_port = config.get('smtp_port', 465)
    smtp_user = config.get('smtp_user')
    smtp_pass = config.get('smtp_pass')
    to_email = config.get('to_email', smtp_user)
    
    if not smtp_user or not smtp_pass:
        print("❌ 邮件配置不完整，请检查 config.json")
        return False
    
    # 解析新闻内容
    date_str, total_count, news_items = parse_news_content(content)
    
    # 生成邮件内容
    html_content = generate_news_html(date_str, total_count, news_items)
    text_content = generate_news_text(date_str, total_count, news_items)
    
    # 构建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📰 AI 每日新闻 - {date_str}"
    msg['From'] = f"=?utf-8?b?5p2D5p2D566h5a62?= <{smtp_user}>"
    msg['To'] = to_email
    
    # 添加纯文本和HTML
    msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # 发送
    try:
        if smtp_port == 465 or 'qq.com' in smtp_server:
            server = smtplib.SMTP_SSL(smtp_server, 465)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        
        print(f"✅ AI新闻邮件已发送到 {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


if __name__ == "__main__":
    success = send_news_email()
    exit(0 if success else 1)
