#!/usr/bin/env python3
"""
合约交易辅助系统 - Pro 版
价格预警 + 市场数据 + 链上监控
使用统一邮件模板，专业样式
"""

import requests
import json
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# 导入统一邮件模板
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from email_templates import create_crypto_email

# 配置
DAILY_REPORT_DIR = Path("/root/.openclaw/workspace/skills/daily-report")
CONFIG_FILE = DAILY_REPORT_DIR / "config.json"
ALERT_CONFIG = Path(__file__).parent / "crypto_alerts.json"


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_alert_config():
    """加载预警配置"""
    if ALERT_CONFIG.exists():
        with open(ALERT_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "price_alerts": [
            {"symbol": "BTCUSDT", "above": 70000, "below": 60000},
            {"symbol": "ETHUSDT", "above": 4000, "below": 3000},
        ],
        "funding_alerts": True,
        "liquidation_alerts": True,
    }


def save_alert_config(config):
    with open(ALERT_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ============ 币安API ============
BINANCE_FAPI = "https://fapi.binance.com"
BINANCE_SPOT_API = "https://api.binance.com"


def get_market_data(symbol):
    """获取合约市场数据"""
    try:
        # BGB特殊处理
        if symbol == 'BGBUSDT':
            resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitget-token&vs_currencies=usd&include_24hr_change=true",
                timeout=15
            )
            data = resp.json()
            bgb = data['bitget-token']
            return {
                'symbol': symbol,
                'price': bgb['usd'],
                'price_change_24h': bgb.get('usd_24h_change', 0),
                'volume_24h': 0,
                'high_24h': 0,
                'low_24h': 0,
                'open_interest': 0,
                'funding_rate': 0,
            }
        
        # 先尝试合约
        price_resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/ticker/price?symbol={symbol}", timeout=10)
        price_data = price_resp.json()
        
        if 'code' in price_data:
            spot_resp = requests.get(f"{BINANCE_SPOT_API}/api/v3/ticker/24hr?symbol={symbol}", timeout=10)
            spot_data = spot_resp.json()
            
            return {
                'symbol': symbol,
                'price': float(spot_data['lastPrice']),
                'price_change_24h': float(spot_data['priceChangePercent']),
                'volume_24h': float(spot_data['volume']),
                'high_24h': float(spot_data['highPrice']),
                'low_24h': float(spot_data['lowPrice']),
                'open_interest': 0,
                'funding_rate': 0,
            }
        
        price = float(price_data['price'])
        
        stats_resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/ticker/24hr?symbol={symbol}", timeout=10)
        stats = stats_resp.json()
        
        open_interest_resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/openInterest?symbol={symbol}", timeout=10)
        open_interest = float(open_interest_resp.json()['openInterest'])
        
        funding_resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/premiumIndex?symbol={symbol}", timeout=10)
        funding = float(funding_resp.json()['lastFundingRate']) * 100
        
        return {
            'symbol': symbol,
            'price': price,
            'price_change_24h': float(stats['priceChangePercent']),
            'volume_24h': float(stats['volume']),
            'high_24h': float(stats['highPrice']),
            'low_24h': float(stats['lowPrice']),
            'open_interest': open_interest,
            'funding_rate': funding,
        }
    except Exception as e:
        print(f"获取{symbol}数据失败: {e}")
        return None


def get_top_liquidations():
    """获取大额爆仓数据"""
    try:
        resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/allForceOrders?limit=200", timeout=15)
        orders = resp.json()

        # API可能返回错误对象或已下线
        if isinstance(orders, dict):
            error_msg = orders.get('msg', '未知错误')
            print(f"获取爆仓数据API不可用: {error_msg}")
            return []

        liquidations = []
        for order in orders:
            liquidations.append({
                'symbol': order['symbol'],
                'side': '多军爆仓' if order['side'] == 'SELL' else '空军爆仓',
                'qty': float(order['origQty']),
                'price': float(order['avgPrice']),
                'value': float(order['origQty']) * float(order['avgPrice']),
                'time': order['time']
            })

        liquidations.sort(key=lambda x: x['value'], reverse=True)
        return liquidations[:10]
    except Exception as e:
        print(f"获取爆仓数据失败: {e}")
        return []


def get_funding_rates():
    """获取所有币种资金费率"""
    try:
        resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/premiumIndex", timeout=10)
        data = resp.json()
        
        rates = []
        for item in data:
            rate = float(item['lastFundingRate']) * 100
            rates.append({
                'symbol': item['symbol'],
                'rate': rate,
                'mark_price': float(item['markPrice'])
            })
        
        rates.sort(key=lambda x: abs(x['rate']), reverse=True)
        return rates[:15]
    except Exception as e:
        print(f"获取资金费率失败: {e}")
        return []


# ============ 预警检查 ============

def check_price_alerts(prices):
    """检查价格预警"""
    config = load_alert_config()
    alerts = []
    
    for alert in config.get('price_alerts', []):
        symbol = alert['symbol']
        price_data = prices.get(symbol)
        
        if not price_data:
            continue
        
        current_price = price_data['price']
        
        if 'above' in alert and current_price >= alert['above']:
            alerts.append({
                'type': 'price_above',
                'symbol': symbol,
                'price': current_price,
                'threshold': alert['above'],
                'message': f"🚨 {symbol} 价格突破 ${current_price:,.2f} (目标: ${alert['above']:,.2f})"
            })
        
        if 'below' in alert and current_price <= alert['below']:
            alerts.append({
                'type': 'price_below',
                'symbol': symbol,
                'price': current_price,
                'threshold': alert['below'],
                'message': f"🚨 {symbol} 价格跌破 ${current_price:,.2f} (目标: ${alert['below']:,.2f})"
            })
    
    return alerts


def check_funding_alerts(rates):
    """检查资金费率异常"""
    alerts = []
    
    for rate in rates:
        if abs(rate['rate']) > 0.1:
            direction = "多头付费极高" if rate['rate'] > 0 else "空头付费极高"
            alerts.append({
                'type': 'funding_extreme',
                'symbol': rate['symbol'],
                'rate': rate['rate'],
                'message': f"⚠️ {rate['symbol']} 资金费率异常: {rate['rate']:.4f}% ({direction})"
            })
    
    return alerts


# ============ 邮件发送 ============

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
        msg['From'] = f"=?utf-8?b?5p2D5p2D5YW755qE6Jm+77yI5oqV6LWE77yJ?= <{smtp_user}>"
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


# ============ 报告生成 ============

def generate_market_report():
    """生成市场数据报告"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'BGBUSDT', 'HYPEUSDT']
    
    print("📊 获取市场数据...")
    prices = {}
    for symbol in symbols:
        data = get_market_data(symbol)
        if data:
            prices[symbol] = data
            print(f"  ✓ {symbol}: ${data['price']:,.2f}")
    
    print("\n💥 获取爆仓数据...")
    liquidations = get_top_liquidations()
    print(f"  ✓ 获取到 {len(liquidations)} 条爆仓记录")
    
    print("\n💰 获取资金费率...")
    funding_rates = get_funding_rates()
    print(f"  ✓ 获取到 {len(funding_rates)} 个币种费率")
    
    print("\n🔔 检查预警条件...")
    price_alerts = check_price_alerts(prices)
    funding_alerts = check_funding_alerts(funding_rates)
    all_alerts = price_alerts + funding_alerts
    
    for alert in all_alerts:
        print(f"  ⚠️ {alert['message']}")
    
    return prices, liquidations, funding_rates, all_alerts


def generate_report(prices, liquidations, funding_rates, alerts):
    """生成报告 - 使用专业模板"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 使用加密货币主题模板
    email = create_crypto_email("📊 合约市场监控", f"实时数据 · {now}")
    
    # 添加预警
    if alerts:
        alert_items = []
        for alert in alerts:
            alert_type = "up" if "突破" in alert['message'] else "down"
            alert_items.append({
                'icon': '🚨' if "突破" in alert['message'] else '⚠️',
                'text': alert['message'],
                'type': alert_type
            })
        email.add_alert_box("🔔 预警提醒", alert_items, "critical" if any(a['type'].startswith('price') for a in alerts) else "warning")
    
    # 添加价格数据表格
    price_rows = []
    for symbol, data in prices.items():
        change_class = "change-up" if data['price_change_24h'] >= 0 else "change-down"
        change_sign = "+" if data['price_change_24h'] >= 0 else ""
        funding_class = "highlight-high" if abs(data['funding_rate']) > 0.05 else ""
        
        price_rows.append([
            f"<strong>{symbol.replace('USDT', '')}</strong>",
            f"${data['price']:,.2f}",
            f'<span class="{change_class}">{change_sign}{data["price_change_24h"]:.2f}%</span>',
            f"{data['open_interest']/1e6:.2f}M",
            f'<span class="{funding_class}">{data["funding_rate"]:.4f}%</span>'
        ])
    
    if price_rows:
        price_html = '<table>\n<tr><th>币种</th><th>价格</th><th>24h涨跌</th><th>持仓量</th><th>资金费率</th></tr>\n'
        for row in price_rows:
            price_html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>\n"
        price_html += '</table>'
        email.add_section("📈 合约行情", "📈", price_html)
    
    # 添加资金费率排行
    funding_rows = []
    for rate in funding_rates[:10]:
        funding_class = "highlight-high" if abs(rate['rate']) > 0.1 else ("highlight-medium" if abs(rate['rate']) > 0.05 else "")
        direction = "📈" if rate['rate'] > 0 else "📉"
        funding_rows.append([
            rate['symbol'].replace('USDT', ''),
            f'<span class="{funding_class}">{direction} {rate["rate"]:.4f}%</span>',
            f"${rate['mark_price']:,.2f}"
        ])
    
    if funding_rows:
        funding_html = '<table>\n<tr><th>币种</th><th>资金费率</th><th>标记价格</th></tr>\n'
        for row in funding_rows:
            funding_html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>\n"
        funding_html += '</table>'
        email.add_section("💰 资金费率排行", "💰", funding_html)
    
    # 添加爆仓数据
    liq_rows = []
    for liq in liquidations[:10]:
        side_class = "change-down" if liq['side'] == '多军爆仓' else "change-up"
        liq_rows.append([
            liq['symbol'].replace('USDT', ''),
            f'<span class="{side_class}">{liq["side"]}</span>',
            f"{liq['qty']:.4f}",
            f"${liq['value']:,.0f}"
        ])
    
    if liq_rows:
        liq_html = '<table>\n<tr><th>币种</th><th>方向</th><th>数量</th><th>价值</th></tr>\n'
        for row in liq_rows:
            liq_html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>\n"
        liq_html += '</table>'
        email.add_section("💥 近期大额爆仓", "💥", liq_html)
    
    # 添加统计
    email.add_stats_bar([
        {'icon': '📊', 'label': '监控币种', 'value': f"{len(prices)} 个"},
        {'icon': '💥', 'label': '爆仓记录', 'value': f"{len(liquidations)} 条"},
        {'icon': '🔔', 'label': '预警触发', 'value': f"{len(alerts)} 个"},
    ])
    
    # 生成纯文本版本
    text_content = f"""📊 合约市场监控 - {now}

"""
    if alerts:
        text_content += "🔔 预警提醒:\n"
        for alert in alerts:
            text_content += f"  {alert['message']}\n"
        text_content += "\n"
    
    text_content += "📈 合约行情:\n"
    for symbol, data in prices.items():
        change_sign = "+" if data['price_change_24h'] >= 0 else ""
        text_content += f"  {symbol}: ${data['price']:,.2f} ({change_sign}{data['price_change_24h']:.2f}%)\n"
    
    text_content += "\n💰 资金费率排行:\n"
    for rate in funding_rates[:5]:
        direction = "📈" if rate['rate'] > 0 else "📉"
        text_content += f"  {rate['symbol']}: {direction} {rate['rate']:.4f}%\n"
    
    text_content += "\n💥 大额爆仓:\n"
    for liq in liquidations[:5]:
        text_content += f"  {liq['symbol']} {liq['side']}: ${liq['value']:,.0f}\n"
    
    text_content += "\n🦞 由权权龙虾管家生成 · 数据来源: Binance Futures"
    
    return email.render(), text_content


def main():
    print("=" * 60)
    print("📊 合约市场监控系统")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 检查是否在静默时段
    current_hour = datetime.now().hour
    if 1 <= current_hour < 7:
        print(f"\n😴 当前时间 {current_hour}:00 处于静默时段（01:00-07:00）")
        print("💤 合约监控已暂停，凌晨7点后恢复正常推送")
        print("=" * 60)
        return 0
    
    # 获取数据
    prices, liquidations, funding_rates, alerts = generate_market_report()
    
    # 生成报告
    html, text = generate_report(prices, liquidations, funding_rates, alerts)
    
    # 保存预览
    preview_file = '/tmp/crypto_market_report.html'
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n💾 报告已保存: {preview_file}")
    
    # 发送邮件
    now = datetime.now().strftime("%H:%M")
    has_alerts = "🚨" if alerts else "📊"
    subject = f"{has_alerts} 合约市场监控 - {now}"
    success = send_email(subject, html, text)
    
    if alerts:
        print(f"\n🔔 发现 {len(alerts)} 个预警！")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
