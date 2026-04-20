#!/usr/bin/env python3
"""
合约交易辅助系统 - 价格预警 + 市场数据 + 链上监控
使用统一邮件模板系统
"""

import requests
import json
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# 导入统一邮件模板
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
    """获取合约市场数据（带现货备用）"""
    try:
        # BGB特殊处理（用CoinGecko）
        if symbol == 'BGBUSDT':
            resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitget-token&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_last_updated_at=true",
                timeout=15
            )
            data = resp.json()
            bgb = data['bitget-token']
            return {
                'symbol': symbol,
                'price': bgb['usd'],
                'price_change_24h': bgb.get('usd_24h_change', 0),
                'volume_24h': bgb.get('usd_24h_vol', 0),
                'high_24h': 0,
                'low_24h': 0,
                'open_interest': 0,
                'funding_rate': 0,
            }
        
        # 先尝试合约
        price_resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/ticker/price?symbol={symbol}", timeout=10)
        price_data = price_resp.json()
        
        if 'code' in price_data:  # 合约不存在，尝试现货
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
        
        # 24h统计
        stats_resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/ticker/24hr?symbol={symbol}", timeout=10)
        stats = stats_resp.json()
        
        # 持仓量
        open_interest_resp = requests.get(f"{BINANCE_FAPI}/fapi/v1/openInterest?symbol={symbol}", timeout=10)
        open_interest = float(open_interest_resp.json()['openInterest'])
        
        # 资金费率
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
        
        # 按金额排序
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
        
        # 按费率绝对值排序
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
        if abs(rate['rate']) > 0.1:  # 资金费率超过0.1%
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
        msg['From'] = f"=?utf-8?b?5p2D5p2D5YW755qE6Jm+77yI5oqV6LWE77yJ?= <{smtp_user}>"
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


# ============ 报告生成 ============

def generate_market_report():
    """生成市场数据报告"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'BGBUSDT']
    
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
    
    # 检查预警
    print("\n🔔 检查预警条件...")
    price_alerts = check_price_alerts(prices)
    funding_alerts = check_funding_alerts(funding_rates)
    all_alerts = price_alerts + funding_alerts
    
    for alert in all_alerts:
        print(f"  ⚠️ {alert['message']}")
    
    return prices, liquidations, funding_rates, all_alerts


def generate_report(prices, liquidations, funding_rates, alerts):
    """生成报告内容"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 使用统一模板
    email = create_crypto_email("📊 合约市场监控", f"实时数据 · {now}")
    
    # 预警区块
    if alerts:
        alert_items = []
        for alert in alerts:
            alert_type = 'danger' if alert['type'].startswith('price') else 'warning'
            alert_items.append({
                'icon': '🚨' if alert_type == 'danger' else '⚠️',
                'text': alert['message'],
                'type': 'down' if alert_type == 'danger' else 'neutral'
            })
        email.add_alert_box("🔔 预警提醒", alert_items, alert_type="warning")
    
    # 合约行情表格
    price_rows = []
    for symbol, data in prices.items():
        change_sign = "+" if data['price_change_24h'] >= 0 else ""
        oi_str = f"{data['open_interest']/1e6:.2f}M" if data['open_interest'] > 0 else "N/A"
        funding_str = f"{data['funding_rate']:.4f}%"
        price_rows.append([
            symbol.replace('USDT', ''),
            f"${data['price']:,.2f}",
            f"{change_sign}{data['price_change_24h']:.2f}%",
            oi_str,
            funding_str
        ])
    
    if price_rows:
        email.add_table(
            "📈 合约行情",
            "📈",
            ["币种", "价格", "24h涨跌", "持仓量", "资金费率"],
            price_rows,
            highlight_column=2,
            highlight_func=lambda x: 'change-up' if '+' in str(x) else ('change-down' if '-' in str(x) else '')
        )
    
    # 资金费率排行表格
    funding_rows = []
    for rate in funding_rates[:10]:
        direction = "📈" if rate['rate'] > 0 else "📉"
        funding_rows.append([
            rate['symbol'].replace('USDT', ''),
            f"{direction} {rate['rate']:.4f}%",
            f"${rate['mark_price']:,.2f}"
        ])
    
    if funding_rows:
        email.add_table(
            "💰 资金费率排行",
            "💰",
            ["币种", "资金费率", "标记价格"],
            funding_rows,
            highlight_column=1,
            highlight_func=lambda x: 'highlight-high' if any(c in str(x) for c in ['📈', '📉']) and abs(float(str(x).split()[1].replace('%', ''))) > 0.1 else ''
        )
    
    # 爆仓数据表格
    liq_rows = []
    for liq in liquidations[:10]:
        liq_rows.append([
            liq['symbol'].replace('USDT', ''),
            liq['side'],
            f"{liq['qty']:.4f}",
            f"${liq['value']:,.0f}"
        ])
    
    if liq_rows:
        email.add_table(
            "💥 近期大额爆仓",
            "💥",
            ["币种", "方向", "数量", "价值"],
            liq_rows
        )
    
    # 统计栏
    email.add_stats_bar([
        {'icon': '📊', 'label': '监控币种', 'value': f'{len(prices)} 个'},
        {'icon': '🔔', 'label': '预警', 'value': f'{len(alerts)} 个'},
        {'icon': '⏰', 'label': '时间', 'value': now},
    ])
    
    # 生成纯文本版本
    text_lines = [f"📊 合约市场监控 - {now}", "=" * 40, ""]
    
    if alerts:
        text_lines.append("【🔔 预警提醒】")
        for alert in alerts:
            text_lines.append(f"  {alert['message']}")
        text_lines.append("")
    
    if prices:
        text_lines.append("【📈 合约行情】")
        for symbol, data in prices.items():
            change_sign = "+" if data['price_change_24h'] >= 0 else ""
            text_lines.append(f"  {symbol}: ${data['price']:,.2f} ({change_sign}{data['price_change_24h']:.2f}%)")
        text_lines.append("")
    
    if funding_rates:
        text_lines.append("【💰 资金费率排行】")
        for rate in funding_rates[:5]:
            direction = "多" if rate['rate'] > 0 else "空"
            text_lines.append(f"  {rate['symbol']}: {rate['rate']:.4f}% ({direction})")
        text_lines.append("")
    
    if liquidations:
        text_lines.append("【💥 近期大额爆仓】")
        for liq in liquidations[:5]:
            text_lines.append(f"  {liq['symbol']} {liq['side']}: ${liq['value']:,.0f}")
        text_lines.append("")
    
    text_lines.append("=" * 40)
    text_lines.append("🦞 权权管家生成 · 数据来源: Binance Futures")
    text_lines.append("⚠️ 仅供参考，不构成投资建议")
    
    return email.render(), '\n'.join(text_lines)


def main():
    print("=" * 60)
    print("📊 合约市场监控系统")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 检查是否在静默时段（凌晨1:00-7:00不推送）
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
    subject = f"📊 合约市场监控 - {now}"
    success = send_email(subject, html, text)
    
    # 如果有预警，额外提示
    if alerts:
        print(f"\n🔔 发现 {len(alerts)} 个预警！")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
