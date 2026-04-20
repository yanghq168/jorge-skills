#!/usr/bin/env python3
"""
统一邮件模板系统
所有邮件发送脚本共享的专业 HTML 模板
"""

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
                # 简单提取文本
                import re
                text = re.sub(r'<[^>]+>', '', section['raw_html'])
                text = re.sub(r'\n+', '\n', text)
                lines.append(text.strip())
            else:
                icon = section.get('icon', '')
                title = section.get('title', '')
                content = section.get('content', '')
                lines.append(f"【{icon} {title}】")
                # 去掉 HTML 标签
                import re
                text = re.sub(r'<[^>]+>', '', content)
                text = re.sub(r'\n+', '\n', text)
                lines.append(text.strip())
