#!/usr/bin/env python3
"""
统一邮件模板系统
所有邮件发送脚本共享的专业 HTML 模板
"""

import re
from datetime import datetime
from typing import List, Dict, Optional


class EmailTheme:
    """邮件主题配色方案"""
    
    # 不同业务的配色方案
    FINANCE = {
        'primary': '#667eea',      # 紫蓝渐变
        'secondary': '#764ba2',
        'accent': '#f39c12',
        'bg_header': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'bg_card': '#f8f9fa',
        'text_primary': '#2c3e50',
        'text_secondary': '#6c757d',
        'alert_up': '#27ae60',
        'alert_down': '#e74c3c',
    }
    
    NEWS = {
        'primary': '#3498db',      # 科技蓝
        'secondary': '#2980b9',
        'accent': '#e74c3c',
        'bg_header': 'linear-gradient(135deg, #3498db 0%, #2980b9 100%)',
        'bg_card': '#f8f9fa',
        'text_primary': '#2c3e50',
        'text_secondary': '#6c757d',
        'alert_up': '#27ae60',
        'alert_down': '#e74c3c',
    }
    
    LOTTERY = {
        'primary': '#e74c3c',      # 喜庆红
        'secondary': '#c0392b',
        'accent': '#f1c40f',
        'bg_header': 'linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)',
        'bg_card': '#fdf2f2',
        'text_primary': '#2c3e50',
        'text_secondary': '#6c757d',
        'alert_up': '#27ae60',
        'alert_down': '#e74c3c',
    }
    
    CRYPTO = {
        'primary': '#f39c12',      # 加密货币橙
        'secondary': '#e67e22',
        'accent': '#27ae60',
        'bg_header': 'linear-gradient(135deg, #f39c12 0%, #e67e22 100%)',
        'bg_card': '#fef9e7',
        'text_primary': '#2c3e50',
        'text_secondary': '#6c757d',
        'alert_up': '#27ae60',
        'alert_down': '#e74c3c',
    }
    
    DAILY = {
        'primary': '#1abc9c',      # 清新绿
        'secondary': '#16a085',
        'accent': '#3498db',
        'bg_header': 'linear-gradient(135deg, #1abc9c 0%, #16a085 100%)',
        'bg_card': '#f0f9f7',
        'text_primary': '#2c3e50',
        'text_secondary': '#6c757d',
        'alert_up': '#27ae60',
        'alert_down': '#e74c3c',
    }


class EmailTemplate:
    """专业邮件模板生成器"""
    
    def __init__(self, theme: Dict, title: str, subtitle: str = ""):
        self.theme = theme
        self.title = title
        self.subtitle = subtitle
        self.sections = []
        self.timestamp = datetime.now()
    
    def add_section(self, title: str, icon: str, content: str, highlight: bool = False):
        """添加内容区块"""
        self.sections.append({
            'title': title,
            'icon': icon,
            'content': content,
            'highlight': highlight
        })
    
    def add_table(self, title: str, icon: str, headers: List[str], rows: List[List], 
                  highlight_column: int = -1, highlight_func=None):
        """添加表格区块"""
        table_html = self._generate_table(headers, rows, highlight_column, highlight_func)
        self.add_section(title, icon, table_html)
    
    def add_alert_box(self, title: str, alerts: List[Dict], alert_type: str = "warning"):
        """添加告警框
        alerts: [{'icon': '📈', 'text': '内容', 'type': 'up/down/neutral'}]
        """
        alert_html = f'<div class="alert-box {alert_type}">\n'
        alert_html += f'<div class="section-title">{title}</div>\n'
        for alert in alerts:
            css_class = ""
            if alert.get('type') == 'up':
                css_class = "change-up"
            elif alert.get('type') == 'down':
                css_class = "change-down"
            alert_html += f'<div class="alert-item {css_class}">{alert["icon"]} {alert["text"]}</div>\n'
        alert_html += '</div>\n'
        self.sections.append({'raw_html': alert_html})
    
    def add_stats_bar(self, stats: List[Dict]):
        """添加统计栏
        stats: [{'icon': '📊', 'label': '标签', 'value': '值'}]
        """
        self.stats = stats
    
    def _generate_table(self, headers: List[str], rows: List[List], 
                       highlight_column: int, highlight_func) -> str:
        """生成表格 HTML"""
        html = '<table>\n<tr>'
        for h in headers:
            html += f'<th>{h}</th>'
        html += '</tr>\n'
        
        for row in rows:
            html += '<tr>'
            for i, cell in enumerate(row):
                css_class = ""
                if highlight_column == i and highlight_func:
                    css_class = highlight_func(cell)
                if css_class:
                    html += f'<td class="{css_class}">{cell}</td>'
                else:
                    html += f'<td>{cell}</td>'
            html += '</tr>\n'
        html += '</table>'
        return html
    
    def render_text(self) -> str:
        """生成纯文本版本用于邮件备选"""
        lines = []
        lines.append(f"{'='*40}")
        lines.append(self.title)
        if self.subtitle:
            lines.append(self.subtitle)
        lines.append(f"⏰ {self.timestamp.strftime('%Y年%m月%d日 %H:%M')}")
        lines.append(f"{'='*40}")
        lines.append("")
        
        for section in self.sections:
            if 'raw_html' in section:
                text = re.sub(r'<[^>]+>', '', section['raw_html'])
                text = re.sub(r'\n+', '\n', text)
                lines.append(text.strip())
            else:
                icon = section.get('icon', '')
                title = section.get('title', '')
                content = section.get('content', '')
                lines.append(f"【{icon} {title}】")
                text = re.sub(r'<[^>]+>', '', content)
                text = re.sub(r'\n+', '\n', text)
                lines.append(text.strip())
            lines.append("")
        
        # 统计栏
        if hasattr(self, 'stats'):
            lines.append("-" * 40)
            for stat in self.stats:
                lines.append(f"{stat['icon']} {stat['label']}: {stat['value']}")
            lines.append("")
        
        lines.append(f"{'='*40}")
        lines.append(f"🦞 权权管家 · {self.title} · 专业数据服务")
        lines.append(f"{'='*40}")
        
        return '\n'.join(lines)
    
    def render(self) -> str:
        """渲染完整 HTML 邮件"""
        t = self.theme
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: {t['text_primary']};
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: {t['bg_header']};
        }}
        .container {{
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .header {{
            background: {t['bg_header']};
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.5px;
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
        .section {{
            background: {t['bg_card']};
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }}
        .section.highlight {{
            border: 2px solid {t['primary']};
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: {t['text_primary']};
        }}
        .alert-box {{
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border-left: 5px solid {t['accent']};
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .alert-box.critical {{
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border-left-color: #e74c3c;
        }}
        .alert-box.success {{
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-left-color: #27ae60;
        }}
        .alert-item {{
            padding: 8px 0;
            border-bottom: 1px dashed #dee2e6;
        }}
        .alert-item:last-child {{
            border-bottom: none;
        }}
        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 14px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: {t['bg_header']};
            color: white;
            padding: 14px 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 14px 12px;
            border-bottom: 1px solid #e9ecef;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .highlight-high {{
            color: #e74c3c;
            font-weight: 700;
            font-size: 16px;
        }}
        .highlight-medium {{
            color: #e67e22;
            font-weight: 700;
            font-size: 16px;
        }}
        .highlight-low {{
            color: #27ae60;
            font-weight: 700;
            font-size: 16px;
        }}
        .change-up {{
            color: {t['alert_up']};
            font-weight: 700;
        }}
        .change-down {{
            color: {t['alert_down']};
            font-weight: 700;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin: 4px;
        }}
        .badge-new {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-removed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 30px;
            padding-top: 24px;
            border-top: 2px solid #e9ecef;
            font-size: 13px;
            color: {t['text_secondary']};
        }}
        .stats-bar strong {{
            color: {t['text_primary']};
        }}
        .risk-notice {{
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            padding: 20px;
            border-radius: 12px;
            margin-top: 24px;
            font-size: 13px;
            color: #856404;
            text-align: center;
            border: 1px solid {t['accent']};
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
            .section {{ padding: 16px; }}
            th, td {{ padding: 10px 8px; font-size: 13px; }}
            .stats-bar {{ flex-wrap: wrap; gap: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.title}</h1>
            {f'<div class="subtitle">{self.subtitle}</div>' if self.subtitle else ''}
            <div class="meta">⏰ {self.timestamp.strftime('%Y年%m月%d日 %H:%M')} · 🤖 权权管家自动生成</div>
        </div>
        <div class="content">
"""
        
        # 添加各区块
        for section in self.sections:
            if 'raw_html' in section:
                html += section['raw_html']
            else:
                highlight_class = ' highlight' if section.get('highlight') else ''
                html += f'<div class="section{highlight_class}">\n'
                html += f'<div class="section-title">{section["icon"]} {section["title"]}</div>\n'
                html += section['content']
                html += '</div>\n'
        
        # 统计栏
        if hasattr(self, 'stats'):
            html += '<div class="stats-bar">\n'
            for stat in self.stats:
                html += f'<div>{stat["icon"]} {stat["label"]}: <strong>{stat["value"]}</strong></div>\n'
            html += '</div>\n'
        
        # 页脚
        html += f"""
        </div>
        <div class="footer">
            🦞 权权管家 · {self.title} · 专业数据服务
        </div>
    </div>
</body>
</html>"""
        
        return html


# 便捷函数
def create_finance_email(title: str, subtitle: str = "") -> EmailTemplate:
    """创建理财类邮件"""
    return EmailTemplate(EmailTheme.FINANCE, title, subtitle)

def create_news_email(title: str, subtitle: str = "") -> EmailTemplate:
    """创建新闻类邮件"""
    return EmailTemplate(EmailTheme.NEWS, title, subtitle)

def create_lottery_email(title: str, subtitle: str = "") -> EmailTemplate:
    """创建彩票类邮件"""
    return EmailTemplate(EmailTheme.LOTTERY, title, subtitle)

def create_crypto_email(title: str, subtitle: str = "") -> EmailTemplate:
    """创建加密货币类邮件"""
    return EmailTemplate(EmailTheme.CRYPTO, title, subtitle)

def create_daily_email(title: str, subtitle: str = "") -> EmailTemplate:
    """创建日报类邮件"""
    return EmailTemplate(EmailTheme.DAILY, title, subtitle)


if __name__ == '__main__':
    # 测试示例
    email = create_finance_email("📊 理财看板 Pro", "实时追踪您的投资组合")
    
    email.add_alert_box("🚨 重要变动提醒", [
        {'icon': '📈', 'text': 'USDE @ Ethereal APY 上涨 2.5% (13.5% → 16.0%)', 'type': 'up'},
        {'icon': '📉', 'text': 'USDT @ 币安 APY 下跌 1.2% (6.0% → 4.8%)', 'type': 'down'},
        {'icon': '✨', 'text': '新上线: WBTC @ 币安钱包 - 12.0%', 'type': 'neutral'},
    ])
    
    email.add_table(
        "🔥 高收益推荐",
        "🔥",
        ["币种", "平台", "APY", "期限"],
        [
            ["USDE", "Ethereal", "16.0%", "长期"],
            ["USDGO", "Bitget", "15.0%", "剩余 45 天"],
            ["WBTC", "币安钱包", "12.0%", "长期"],
        ],
        highlight_column=2,
        highlight_func=lambda x: 'highlight-high' if '%' in str(x) and float(x.replace('%','')) >= 15 else ''
    )
    
    email.add_stats_bar([
        {'icon': '📊', 'label': '追踪天数', 'value': '15 天'},
        {'icon': '📝', 'label': '总记录', 'value': '86 条'},
        {'icon': '💰', 'label': '最高 APY', 'value': '16.0%'},
    ])
    
    print("=== HTML 版本 ===")
    print(email.render())
    print("\n=== 纯文本版本 ===")
    print(email.render_text())
