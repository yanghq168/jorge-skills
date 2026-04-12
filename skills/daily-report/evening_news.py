#!/usr/bin/env python3
"""
AI + 区块链 晚间新闻晚报 - Pro 版
使用统一邮件模板，专业样式
每天晚上9点自动发送
"""

import requests
import feedparser
import json
import re
import os
import sys
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 导入统一邮件模板
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from email_templates import create_news_email

# 加载日报配置
DAILY_REPORT_DIR = Path("/root/.openclaw/workspace/skills/daily-report")
CONFIG_FILE = DAILY_REPORT_DIR / "config.json"


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# ============ AI新闻源 ============
AI_SOURCES = {
    "qbitai": {"name": "量子位", "rss": "https://www.qbitai.com/feed"},
    "jiqizhixin": {"name": "机器之心", "rss": "https://www.jiqizhixin.com/rss"},
    "36kr": {"name": "36氪", "rss": "https://36kr.com/feed"},
    "techcrunch_ai": {"name": "TechCrunch AI", "rss": "https://techcrunch.com/category/artificial-intelligence/feed/"},
}

# ============ 区块链新闻源 ============
BLOCKCHAIN_SOURCES = {
    "chainnews": {"name": "链闻", "rss": "https://www.chainnews.com/rss"},
    "odaily": {"name": "Odaily", "rss": "https://www.odaily.news/rss"},
    "panews": {"name": "PANews", "rss": "https://www.panewslab.com/rss"},
    "blockbeats": {"name": "BlockBeats", "rss": "https://www.theblockbeats.info/rss"},
    "cointelegraph": {"name": "Cointelegraph", "rss": "https://cointelegraph.com/rss"},
    "coindesk": {"name": "CoinDesk", "rss": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
}

# AI关键词
AI_KEYWORDS = [
    "AI", "人工智能", "机器学习", "深度学习", "大模型", "LLM", "神经网络",
    "GPT", "ChatGPT", "OpenAI", "Claude", "Gemini", "Kimi", "DeepSeek"
]

# 区块链关键词
BLOCKCHAIN_KEYWORDS = [
    "比特币", "Bitcoin", "BTC", "以太坊", "Ethereum", "ETH",
    "区块链", "Blockchain", "加密货币", "Crypto", "DeFi", "NFT",
    "Web3", "智能合约", "挖矿", "矿工", "交易所", "币安", "Binance",
    "OKX", "Coinbase", "山寨币", "Altcoin", "稳定币", "USDT"
]


def fetch_rss(source_id, source_info):
    """抓取单个RSS源"""
    try:
        resp = requests.get(source_info['rss'], timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        
        articles = []
        for entry in feed.entries[:5]:
            articles.append({
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'summary': entry.get('summary', '')[:200] if entry.get('summary') else '',
                'published': entry.get('published', ''),
                'source': source_info['name']
            })
        return source_id, articles
    except Exception as e:
        print(f"抓取失败 {source_info['name']}: {e}")
        return source_id, []


def classify_news(title, summary):
    """分类新闻为AI或区块链"""
    text = (title + summary).lower()
    
    ai_score = sum(1 for k in AI_KEYWORDS if k.lower() in text)
    blockchain_score = sum(1 for k in BLOCKCHAIN_KEYWORDS if k.lower() in text)
    
    if ai_score > blockchain_score:
        return 'ai'
    elif blockchain_score > ai_score:
        return 'blockchain'
    else:
        return 'both' if (ai_score > 0 and blockchain_score > 0) else 'other'


def fetch_all_news():
    """抓取所有新闻"""
    all_news = {'ai': [], 'blockchain': [], 'both': [], 'other': []}
    
    print("📰 抓取AI新闻...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_rss, k, v): k for k, v in AI_SOURCES.items()}
        for future in as_completed(futures):
            source_id, articles = future.result()
            for article in articles:
                cat = classify_news(article['title'], article['summary'])
                all_news[cat].append(article)
    
    print("⛓️  抓取区块链新闻...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_rss, k, v): k for k, v in BLOCKCHAIN_SOURCES.items()}
        for future in as_completed(futures):
            source_id, articles = future.result()
            for article in articles:
                cat = classify_news(article['title'], article['summary'])
                if cat == 'ai':
                    cat = 'both'
                all_news[cat].append(article)
    
    return all_news


def deduplicate_news(news_list):
    """去重"""
    seen = set()
    unique = []
    for item in news_list:
        key = item['title'][:30]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:10]


def generate_email_content(news_data):
    """生成邮件内容 - 使用专业模板"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    ai_news = deduplicate_news(news_data.get('ai', []) + news_data.get('both', []))
    blockchain_news = deduplicate_news(news_data.get('blockchain', []) + news_data.get('both', []))
    
    # 使用新闻主题模板（晚报用深色主题）
    email = create_news_email("🌙 晚间新闻晚报", f"AI · 区块链 · 每日精选 · {today}")
    
    # 添加AI新闻
    if ai_news:
        ai_rows = []
        for item in ai_news[:8]:
            title = item['title']
            source = item['source']
            link = item['link']
            ai_rows.append([f"<a href='{link}' target='_blank' style='color:#3498db;text-decoration:none;'>{title}</a>", source])
        
        ai_html = '<table>\n<tr><th>标题</th><th>来源</th></tr>\n'
        for row in ai_rows:
            ai_html += f'<tr><td>{row[0]}</td><td><span class="badge badge-new">{row[1]}</span></td></tr>\n'
        ai_html += '</table>'
        email.add_section("🤖 AI 人工智能", "🤖", ai_html)
    
    # 添加区块链新闻
    if blockchain_news:
        bc_rows = []
        for item in blockchain_news[:8]:
            title = item['title']
            source = item['source']
            link = item['link']
            bc_rows.append([f"<a href='{link}' target='_blank' style='color:#3498db;text-decoration:none;'>{title}</a>", source])
        
        bc_html = '<table>\n<tr><th>标题</th><th>来源</th></tr>\n'
        for row in bc_rows:
            bc_html += f'<tr><td>{row[0]}</td><td><span class="badge badge-new" style="background:#fff7e6;color:#e67e22;">{row[1]}</span></td></tr>\n'
        bc_html += '</table>'
        email.add_section("⛓️ 区块链 & Web3", "⛓️", bc_html)
    
    # 添加统计
    email.add_stats_bar([
        {'icon': '🤖', 'label': 'AI新闻', 'value': f"{len(ai_news)} 条"},
        {'icon': '⛓️', 'label': '区块链', 'value': f"{len(blockchain_news)} 条"},
        {'icon': '📰', 'label': '总计', 'value': f"{len(ai_news) + len(blockchain_news)} 条"},
    ])
    
    # 生成纯文本版本
    text_content = f"""🌙 晚间新闻晚报 - {today}

🤖 AI 人工智能 ({len(ai_news)} 条):
"""
    for item in ai_news[:5]:
        text_content += f"  • [{item['source']}] {item['title']}\n"
        text_content += f"    {item['link']}\n"
    
    text_content += f"\n⛓️ 区块链 & Web3 ({len(blockchain_news)} 条):\n"
    for item in blockchain_news[:5]:
        text_content += f"  • [{item['source']}] {item['title']}\n"
        text_content += f"    {item['link']}\n"
    
    text_content += "\n🦞 由暴躁小龙虾自动生成 · 每天晚上9:00送达"
    
    return email.render(), text_content


def send_email(subject, html_content, text_content):
    """发送邮件（同时发送 HTML 和纯文本版本）"""
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
        msg['From'] = f"=?utf-8?b?5p2D5p2D5YW755qE6Jm+77yIV0VCM++8iQ==?= <{smtp_user}>"
        msg['To'] = to_email
        
        # 添加纯文本版本
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # 添加HTML版本
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
    print("🌙 晚间新闻晚报")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # 抓取新闻
    news_data = fetch_all_news()
    
    total = sum(len(v) for v in news_data.values())
    print(f"\n📊 总计抓取: {total} 条新闻")
    print(f"   AI: {len(news_data['ai'])} 条")
    print(f"   区块链: {len(news_data['blockchain'])} 条")
    print(f"   两者都有: {len(news_data['both'])} 条")
    
    # 生成邮件
    html, text = generate_email_content(news_data)
    
    # 保存预览
    preview_file = '/tmp/evening_news.html'
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n💾 预览已保存: {preview_file}")
    
    # 发送邮件
    today = datetime.now().strftime("%Y年%m月%d日")
    subject = f"🌙 晚间新闻晚报 - {today}"
    success = send_email(subject, html, text)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
