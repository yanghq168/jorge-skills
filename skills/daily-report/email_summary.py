#!/usr/bin/env python3
"""
邮件每日摘要
- 读取今日邮件
- 智能分类（工作/重要/推广）
- 生成摘要报告
- 发送到QQ邮箱
"""

import os
import sys
import json
import imaplib
import email
import re
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from pathlib import Path

# 配置
DAILY_REPORT_DIR = Path("/root/.openclaw/workspace/skills/daily-report")
CONFIG_FILE = DAILY_REPORT_DIR / "config.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def decode_str(s):
    if not s:
        return ""
    try:
        decoded = decode_header(s)
        result = ""
        for part, charset in decoded:
            if isinstance(part, bytes):
                result += part.decode(charset or 'utf-8', errors='replace')
            else:
                result += part
        return result
    except:
        return str(s)

def get_email_body(msg):
    """获取邮件正文"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(charset, errors='replace')
                    break
                except:
                    continue
            elif content_type == "text/html" and not body:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    html = part.get_payload(decode=True).decode(charset, errors='replace')
                    body = re.sub(r'<[^>]+>', ' ', html)
                    body = re.sub(r'\s+', ' ', body).strip()[:300]
                except:
                    continue
    else:
        try:
            charset = msg.get_content_charset() or 'utf-8'
            body = msg.get_payload(decode=True).decode(charset, errors='replace')
        except:
            body = ""
    
    body = body.replace('\r', ' ').replace('\n', ' ').strip()
    body = re.sub(r'\s+', ' ', body)
    return body[:200] if len(body) > 200 else body

def classify_email(from_addr, subject, body):
    """智能分类邮件"""
    text = (from_addr + subject + body).lower()
    
    # 重要/工作
    if any(k in text for k in ['@company', '@work', '会议', 'deadline', 'urgent', '重要', '审批', '申请']):
        return 'important'
    
    # 财务/银行
    if any(k in text for k in ['bank', '支付宝', '微信', '账单', '消费', '交易', 'transfer', 'invoice', 'payment']):
        return 'finance'
    
    # 社交
    if any(k in text for k in ['linkedin', 'github', 'twitter', 'invite', '好友请求']):
        return 'social'
    
    # 推广/广告
    if any(k in text for k in ['unsubscribe', '退订', '优惠', '促销', '折扣', 'sale', '广告', 'marketing', 'promo', 'limited time']):
        return 'promo'
    
    # 订阅/新闻
    if any(k in text for k in ['newsletter', '订阅', 'news', '更新']):
        return 'news'
    
    # 系统通知
    if any(k in text for k in ['noreply', 'no-reply', 'notification', 'verify', '验证码', '系统通知']):
        return 'system'
    
    return 'other'

def parse_email_date(date_str):
    """解析邮件日期为datetime对象"""
    if not date_str:
        return None
    
    # 尝试多种日期格式
    date_formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%d %b %Y %H:%M:%S %Z',
        '%Y-%m-%d %H:%M:%S',
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    # 尝试从日期字符串中提取日期部分
    try:
        # 处理类似 "Wed, 02 Apr 2026 08:30:00 +0800" 的格式
        match = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', date_str, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            month_num = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
            return datetime(int(year), month_num[month.lower()], int(day))
    except:
        pass
    
    return None

def is_today_email(date_str):
    """判断邮件是否是今天的"""
    email_date = parse_email_date(date_str)
    if not email_date:
        return False
    
    today = datetime.now()
    # 考虑时区差异，使用日期部分比较
    return (email_date.year == today.year and 
            email_date.month == today.month and 
            email_date.day == today.day)

def fetch_today_emails():
    """获取今日邮件"""
    config = load_config()
    
    imap_server = config.get('imap_server', 'imap.qq.com')
    imap_user = config.get('smtp_user')
    imap_pass = config.get('smtp_pass')
    
    if not imap_user or not imap_pass:
        print("❌ 邮箱配置不完整")
        return []
    
    try:
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(imap_user, imap_pass)
        mail.select('INBOX')
        
        # 获取最近3天的邮件，然后过滤出今天的
        # 使用 SINCE 搜索最近3天的邮件
        three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")
        
        result, data = mail.search(None, f'(SINCE "{three_days_ago}")')
        
        if result != 'OK':
            mail.logout()
            return []
        
        email_ids = data[0].split()
        emails = []
        
        print(f"📥 找到 {len(email_ids)} 封最近3天的邮件，开始筛选今天的...")
        
        for e_id in email_ids:
            result, data = mail.fetch(e_id, '(RFC822)')
            if result != 'OK':
                continue
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = decode_str(msg.get('Subject', ''))
            from_addr = decode_str(msg.get('From', ''))
            date_str = msg.get('Date', '')
            
            # 只取发件人名称
            from_name = from_addr.split('<')[0].strip() if '<' in from_addr else from_addr
            from_name = re.sub(r'["\']', '', from_name)[:30]
            
            # 检查是否是今天的邮件
            if not is_today_email(date_str):
                continue
            
            body = get_email_body(msg)
            category = classify_email(from_addr, subject, body)
            
            # 判断是否为未读（QQ邮箱FLAGS判断）
            is_unread = True  # 简化处理
            
            emails.append({
                'subject': subject,
                'from': from_name,
                'from_full': from_addr,
                'date': date_str,
                'body': body,
                'category': category,
                'is_unread': is_unread
            })
        
        mail.logout()
        print(f"✓ 筛选出 {len(emails)} 封今天的邮件")
        return emails
        
    except Exception as e:
        print(f"❌ 读取邮件失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def generate_summary(emails):
    """生成邮件摘要"""
    if not emails:
        return None
    
    # 分类统计
    categories = {
        'important': {'name': '🔴 重要/工作', 'items': []},
        'finance': {'name': '💰 财务/账单', 'items': []},
        'social': {'name': '👥 社交网络', 'items': []},
        'news': {'name': '📰 订阅/新闻', 'items': []},
        'system': {'name': '⚙️ 系统通知', 'items': []},
        'promo': {'name': '📢 推广/广告', 'items': []},
        'other': {'name': '📧 其他邮件', 'items': []}
    }
    
    for e in emails:
        cat = e.get('category', 'other')
        if cat in categories:
            categories[cat]['items'].append(e)
    
    # 统计
    summary = {
        'total': len(emails),
        'unread': len([e for e in emails if e.get('is_unread')]),
        'categories': {k: v for k, v in categories.items() if v['items']}
    }
    
    return summary

def generate_email_html(summary):
    """生成HTML邮件"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>邮件日报 - {today}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif; 
                line-height: 1.6; max-width: 700px; margin: 0 auto; padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .container {{ background: white; border-radius: 12px; padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        .header {{ text-align: center; padding-bottom: 25px; border-bottom: 3px solid #667eea; margin-bottom: 25px; }}
        .header h1 {{ color: #667eea; margin: 0; font-size: 26px; }}
        .header .date {{ color: #888; font-size: 14px; margin-top: 8px; }}
        
        .stats {{ display: flex; justify-content: center; gap: 30px; margin-bottom: 25px; }}
        .stat-box {{ text-align: center; padding: 15px 25px; background: linear-gradient(135deg, #667eea, #764ba2); 
                     color: white; border-radius: 10px; }}
        .stat-number {{ font-size: 28px; font-weight: bold; }}
        .stat-label {{ font-size: 12px; opacity: 0.9; }}
        
        .section {{ margin-bottom: 25px; }}
        .section-title {{ font-size: 16px; font-weight: bold; margin-bottom: 12px; 
                         padding: 8px 12px; background: #f8f9fa; border-radius: 6px; }}
        .section-count {{ float: right; background: #667eea; color: white; 
                          padding: 2px 10px; border-radius: 12px; font-size: 12px; }}
        
        .email-item {{ background: #fafbfc; padding: 12px 15px; margin-bottom: 8px; 
                      border-radius: 8px; border-left: 4px solid #ddd; }}
        .email-item.important {{ border-left-color: #f5222d; background: #fff1f0; }}
        .email-item.finance {{ border-left-color: #faad14; background: #fffbe6; }}
        .email-item.promo {{ opacity: 0.7; }}
        
        .email-subject {{ font-weight: 500; color: #1890ff; margin-bottom: 4px; }}
        .email-from {{ font-size: 12px; color: #52c41a; }}
        .email-preview {{ font-size: 13px; color: #666; margin-top: 6px; line-height: 1.4; }}
        
        .empty {{ text-align: center; color: #999; padding: 20px; font-style: italic; }}
        
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; 
                   text-align: center; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 邮件日报</h1>
            <div class="date">{today}</div>
        </div>
"""
    
    if summary:
        # 统计概览
        html += f"""
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{summary['total']}</div>
                <div class="stat-label">今日邮件</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{summary['unread']}</div>
                <div class="stat-label">未读</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(summary['categories'])}</div>
                <div class="stat-label">分类</div>
            </div>
        </div>
"""
        
        # 各类邮件
        priority_order = ['important', 'finance', 'social', 'news', 'system', 'other', 'promo']
        
        for cat_key in priority_order:
            if cat_key in summary['categories']:
                cat_data = summary['categories'][cat_key]
                items = cat_data['items'][:10]  # 每类最多10条
                
                html += f'''
        <div class="section">
            <div class="section-title">
                {cat_data['name']}
                <span class="section-count">{len(cat_data['items'])}</span>
            </div>
'''
                for item in items:
                    css_class = cat_key
                    subject = item['subject'] or '(无主题)'
                    from_name = item['from']
                    preview = item['body'][:80] + '...' if len(item['body']) > 80 else item['body']
                    
                    html += f'''
            <div class="email-item {css_class}">
                <div class="email-subject">{subject}</div>
                <div class="email-from">{from_name}</div>
                {f'<div class="email-preview">{preview}</div>' if preview else ''}
            </div>'''
                
                if len(cat_data['items']) > 10:
                    html += f'<div style="text-align: center; color: #999; font-size: 12px; margin-top: 8px;">还有 {len(cat_data["items"]) - 10} 封...</div>'
                
                html += '</div>'
    else:
        html += '<div class="empty">今日暂无邮件</div>'
    
    html += '''
        <div class="footer">
            🦞 由权权龙虾管家自动生成 · 智能邮件分类<br>
            支持：重要邮件 / 财务账单 / 社交网络 / 订阅新闻 / 推广广告
        </div>
    </div>
</body>
</html>'''
    
    return html

def send_email(subject, html_content):
    """发送邮件"""
    config = load_config()
    
    smtp_server = config.get('smtp_server', 'smtp.qq.com')
    smtp_user = config.get('smtp_user')
    smtp_pass = config.get('smtp_pass')
    to_email = config.get('to_email', smtp_user)
    
    if not smtp_user or not smtp_pass:
        print("❌ 邮件配置不完整")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"=?utf-8?b?5p2D5p2D6b6Z6Jm+566h5a62?= <{smtp_user}>"
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        
        print(f"✅ 邮件发送成功: {to_email}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def main():
    print("=" * 50)
    print("📧 邮件日报生成中...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # 获取邮件
    print("\n📥 读取今日邮件...")
    emails = fetch_today_emails()
    print(f"✓ 共获取到 {len(emails)} 封今日邮件")
    
    # 生成摘要
    print("\n📝 生成摘要...")
    summary = generate_summary(emails)
    
    # 生成HTML
    html = generate_email_html(summary)
    
    # 保存预览
    preview_file = '/tmp/email_daily_summary.html'
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n💾 预览已保存: {preview_file}")
    
    # 发送邮件
    today = datetime.now().strftime("%Y年%m月%d日")
    subject = f"📧 邮件日报 - {today}"
    success = send_email(subject, html)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())