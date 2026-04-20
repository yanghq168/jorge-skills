#!/usr/bin/env python3
"""
AI + 区块链 晨间新闻邮件
每天早上7点自动发送
使用统一邮件模板系统
"""

import requests
import feedparser
import json
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 导入统一邮件模板
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
        for entry in feed.entries[:5]:  # 每个源最多5条
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
    
    # 抓取AI新闻
    print("📰 抓取AI新闻...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_rss, k, v): k for k, v in AI_SOURCES.items()}
        for future in as_completed(futures):
            source_id, articles = future.result()
            for article in articles:
                cat = classify_news(article['title'], article['summary'])
                all_news[cat].append(article)
    
    # 抓取区块链新闻
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
        key = item['title'][:30]  # 用标题前30字去重
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:10]  # 每类最多10条


def build_news_html(news_items, is_blockchain=False):
    """构建新闻列表HTML"""
    if not news_items:
        return '<div style="color: #999; font-style: italic; text-align: center; padding: 20px;">今日暂无相关新闻</div>'
    
    html = ''
    for item in news_items:
        title = item['title']
        link = item['link']
        source = item['source']
        summary = item['summary'][:100] + '...' if len(item['summary']) > 100 else item['summary']
        
        bg_color = '#fff7e6' if is_blockchain else '#f6ffed'
        border_color = '#fa8c16' if is_blockchain else '#52c41a'
        source_color = '#fa8c16' if is_blockchain else '#52c41a'
        
        html += f'''
        <div style="background: {bg_color}; border-left: 4px solid {border_color}; padding: 12px 15px; margin-bottom: 10px; border-radius: 0 6px 6px 0;">
            <a href="{link}" style="font-weight: 500; color: #1890ff; text-decoration: none; display: block; margin-bottom: 5px;" target="_blank">{title}</a>
            <span style="font-size: 12px; color: {source_color}; background: {bg_color}; padding: 2px 8px; border-radius: 10px; display: inline-block;">{source}</span>
            {f'<div style="font-size: 13px; color: #666; margin-top: 6px; line-height: 1.5;">{summary}</div>' if summary else ''}
        </div>'''
    
    return html


def build_news_text(news_items, is_blockchain=False):
    """构建新闻列表纯文本"""
    if not news_items:
        return "今日暂无相关新闻\n"
    
    lines = []
    for item in news_items:
        lines.append(f"• {item['title']}")
        lines.append(f"  来源: {item['source']} | 链接: {item['link']}")
        if item['summary']:
            lines.append(f"  摘要: {item['summary'][:80]}...")
        lines.append("")
    
    return '\n'.join(lines)


def generate_email(news_data):
    """生成邮件内容"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    ai_news = deduplicate_news(news_data.get('ai', []) + news_data.get('both', []))
    blockchain_news = deduplicate_news(news_data.get('blockchain', []) + news_data.get('both', []))
    
    # 使用统一模板
    email = create_news_email("🌅 晨间新闻简报", f"AI · 区块链 · 每日精选 · {today}")
    
    # 添加AI新闻区块
    ai_html = build_news_html(ai_news, is_blockchain=False)
    email.add_section("🤖 AI 人工智能", "🤖", ai_html)
    
    # 添加区块链新闻区块
    bc_html = build_news_html(blockchain_news, is_blockchain=True)
    email.add_section("⛓️ 区块链 & Web3", "⛓️", bc_html)
    
    # 添加统计栏
    email.add_stats_bar([
        {'icon': '📰', 'label': 'AI新闻', 'value': f'{len(ai_news)} 条'},
        {'icon': '⛓️', 'label': '区块链新闻', 'value': f'{len(blockchain_news)} 条'},
        {'icon': '📅', 'label': '日期', 'value': today},
    ])
    
    # 生成纯文本版本
    text_content = f"🌅 晨间新闻简报 - {today}\n"
    text_content += f"AI · 区块链 · 每日精选\n"
    text_content += "=" * 40 + "\n\n"
    text_content += f"【🤖 AI 人工智能】({len(ai_news)}条)\n"
    text_content += build_news_text(ai_news)
    text_content += f"【⛓️ 区块链 & Web3】({len(blockchain_news)}条)\n"
    text_content += build_news_text(blockchain_news, is_blockchain=True)
    text_content += "=" * 40 + "\n"
    text_content += "🦞 由暴躁小龙虾自动生成 · 每天早上7:00送达\n"
    
    return email.render(), text_content


def send_email(subject, html_content, text_content):
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
        msg['From'] = f"=?utf-8?b?5p2D5p2D5YW755qE6Jm+77yIV0VCM++8iQ==?= <{smtp_user}>"
        msg['To'] = to_email
        
        # 添加纯文本版本（优先）
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
    print("🌅 晨间新闻简报")
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
    html, text = generate_email(news_data)
    
    # 保存预览
    preview_file = '/tmp/morning_news.html'
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n💾 预览已保存: {preview_file}")
    
    # 发送邮件
    today = datetime.now().strftime("%Y年%m月%d日")
    subject = f"🌅 晨间新闻简报 - {today}"
    success = send_email(subject, html, text)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
