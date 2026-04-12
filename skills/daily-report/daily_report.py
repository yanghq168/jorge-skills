#!/usr/bin/env python3
"""
日报生成与发送系统 - Pro 版
使用统一邮件模板，专业样式
包含权权管家工作模块、Agent优化追踪、全体Agent工作表格
"""

import os
import sys
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# 导入统一邮件模板和Agent追踪
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from email_templates import create_daily_email
from agent_tracker import check_agent_changes, get_today_optimizations

# 配置路径
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SKILL_DIR = WORKSPACE / "skills" / "daily-report"
CONFIG_FILE = SKILL_DIR / "config.json"
AGENTS_DIR = WORKSPACE / "agency-agents"

# Agent 类别映射
AGENT_CATEGORIES = {
    'engineering': '工程开发',
    'specialized': '专业领域',
    'marketing': '市场营销',
    'design': '设计',
    'sales': '销售',
    'testing': '测试QA',
    'paid-media': '付费媒体',
    'project-management': '项目管理',
    'support': '客户支持',
    'spatial-computing': '空间计算',
    'product': '产品',
    'finance': '金融',
    'academic': '学术',
    'game-development': '游戏开发',
    'strategy': '战略'
}


def load_config():
    """加载邮件配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_all_agents():
    """获取所有Agent列表"""
    agents = []
    
    if not AGENTS_DIR.exists():
        return agents
    
    for md_file in AGENTS_DIR.rglob("*.md"):
        relative_path = md_file.relative_to(AGENTS_DIR)
        category = relative_path.parent.name if relative_path.parent.name else 'other'
        
        filename = md_file.stem
        parts = filename.split('-')
        
        if len(parts) > 1 and parts[0].isdigit():
            agent_name = '-'.join(parts[1:])
        else:
            agent_name = filename
        
        agent_name = agent_name.replace('-', ' ').title()
        category_cn = AGENT_CATEGORIES.get(category, category)
        
        agents.append({
            'name': agent_name,
            'category': category_cn,
            'work': ''
        })
    
    agents.sort(key=lambda x: (x['category'], x['name']))
    return agents


def get_quanquan_work(date):
    """获取权权管家的工作记录"""
    import re
    memory_file = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
    
    if not memory_file.exists():
        return ['今日暂无工作记录']
    
    content = memory_file.read_text(encoding='utf-8')
    work_items = []
    
    patterns = [
        r"- \[权权管家\] (.+)",
        r"- \[AI\] (.+)",
        r"- \[我\] (.+)",
        r"- \[暴躁小龙虾\] (.+)"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        work_items.extend(matches)
    
    for line in content.split('\n'):
        if line.startswith('- **') and any(k in line for k in ['完成', '修复', '创建', '配置', '部署', '优化', '添加', '更新', '设置', '生成', '推送', '翻译', '备份', '修复', '新增']):
            item = line.lstrip('- **').rstrip('**').strip()
            # 过滤掉元数据
            if not any(skip in item.lower() for skip in ['最后更新', 'agent 总数', '分类数量']):
                work_items.append(item)
    
    # 新增：匹配 Completed Tasks 下的项目
    if 'Completed Tasks' in content or '### Completed' in content:
        # 匹配 #### 开头的任务标题
        task_matches = re.findall(r'#### \d+\.\s*(.+)', content)
        for match in task_matches:
            match_clean = match.strip()
            # 过滤掉元数据条目
            if match_clean and len(match_clean) > 3 and not any(skip in match_clean.lower() for skip in ['total files', 'all categories', 'translation scope', 'encoding', 'repository', 'files modified']):
                if match_clean not in work_items:
                    work_items.append(match_clean)
        
        # 匹配 - **xxx**: 格式的条目，但只取有意义的
        bullet_matches = re.findall(r'- \*\*(.+?)\*\*[:\s]*(.+)?', content)
        for match in bullet_matches:
            item = match[0].strip()
            # 过滤元数据
            if any(skip in item.lower() for skip in ['total', 'all categories', 'translation scope', 'encoding', 'repository', 'files modified', '最后更新', 'agent 总数', '分类数量']):
                continue
            if match[1]:
                desc = match[1].strip()
                # 过滤掉统计类内容
                if not any(skip in desc.lower() for skip in ['个)', 'agent files', 'categories']):
                    item += f": {desc}"
            if item and item not in work_items and len(item) > 3:
                work_items.append(item)
    
    return work_items if work_items else ['今日暂无工作记录']


def generate_quanquan_section():
    """生成权权管家工作模块"""
    today = datetime.now()
    work_items = get_quanquan_work(today)
    
    html = '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">'
    html += '<h3 style="margin-top: 0; font-size: 18px;">🦞 权权管家今日工作</h3>'
    html += '<ul style="margin: 0; padding-left: 20px;">'
    
    for item in work_items:
        html += f'<li style="margin: 8px 0;">{item}</li>'
    
    html += '</ul></div>'
    return html, work_items


def generate_optimization_section():
    """生成Agent优化追踪模块 - 只显示有变更的"""
    # 先检查变更
    check_agent_changes()
    # 获取今日优化
    optimizations = get_today_optimizations()
    
    if not optimizations:
        # 无变更时不显示此模块
        return None, 0
    
    html = '<div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px;">'
    html += f'<h3 style="margin-top: 0; font-size: 18px; color: #fff;">🚀 今日Agent优化（{len(optimizations)}项）</h3>'
    html += '<div style="overflow: auto; max-height: 400px;">'
    html += '<table style="width: 100%; min-width: 600px; font-size: 14px; border-collapse: collapse;">'
    html += '<tr style="background: rgba(0,0,0,0.3);">'
    html += '<th style="text-align: left; padding: 12px; font-weight: 600; color: #fff; width: 25%;">Agent名称</th>'
    html += '<th style="text-align: left; padding: 12px; font-weight: 600; color: #fff; width: 15%;">类型</th>'
    html += '<th style="text-align: left; padding: 12px; font-weight: 600; color: #fff; width: 60%;">优化内容</th>'
    html += '</tr>'
    
    for opt in optimizations:
        html += f'<tr style="background: rgba(255,255,255,0.9); border-bottom: 1px solid rgba(0,0,0,0.1);">'
        html += f'<td style="padding: 12px; font-weight: 500; color: #000;">{opt["agent"]}</td>'
        html += f'<td style="padding: 12px;"><span style="background: #11998e; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; color: #fff;">{opt["type"]}</span></td>'
        html += f'<td style="padding: 12px; line-height: 1.6; color: #000;">{opt["description"]}</td>'
        html += '</tr>'
    
    html += '</table></div></div>'
    return html, len(optimizations)


def generate_agents_table():
    """生成所有Agent工作表格 - 有工作的排前面"""
    agents = get_all_agents()
    
    # 获取工作记录并排序（有工作的排前面）
    for agent in agents:
        agent['work'] = ''  # 这里可以从tracking_data获取实际工作
    
    # 排序：有工作的在前
    agents.sort(key=lambda x: (0 if x['work'] else 1, x['category'], x['name']))
    
    # 检查是否有工作记录
    has_work = any(a['work'] for a in agents)
    
    if has_work:
        # 有工作时：加滚动条，工作列加宽
        html = '<div style="overflow: auto; max-height: 600px;">'
        html += '<table style="width: 100%; min-width: 800px; border-collapse: collapse; font-size: 12px;">'
        html += '<thead style="position: sticky; top: 0; z-index: 10;"><tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">'
        html += '<th style="padding: 12px; text-align: left; width: 20%;">类别</th>'
        html += '<th style="padding: 12px; text-align: left; width: 25%;">Agent名称</th>'
        html += '<th style="padding: 12px; text-align: left; width: 55%;">今日工作</th>'
    else:
        # 无工作时：保持现状
        html = '<div style="overflow-x: auto; max-height: 600px; overflow-y: auto;">'
        html += '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">'
        html += '<thead style="position: sticky; top: 0; z-index: 10;"><tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">'
        html += '<th style="padding: 12px; text-align: left;">类别</th>'
        html += '<th style="padding: 12px; text-align: left;">Agent名称</th>'
        html += '<th style="padding: 12px; text-align: left;">今日工作</th>'
    
    html += '</tr></thead><tbody>'
    
    for i, agent in enumerate(agents):
        bg_color = '#ffffff' if i % 2 == 0 else '#f8f9fa'
        work_display = agent['work'] if agent['work'] else '<span style="color: #999;">无</span>'
        
        # 有工作的行高亮
        row_style = f'background: {bg_color}; border-bottom: 1px solid #e9ecef;'
        if agent['work']:
            row_style = f'background: #e8f5e9; border-bottom: 1px solid #c8e6c9; font-weight: 500;'
        
        html += f'<tr style="{row_style}">'
        html += f'<td style="padding: 10px; color: #666;"><small>{agent["category"]}</small></td>'
        html += f'<td style="padding: 10px; font-weight: 600 if agent["work"] else 500;">{agent["name"]}</td>'
        html += f'<td style="padding: 10px;">{work_display}</td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    
    return html, len(agents), has_work


def generate_daily_report():
    """生成日报内容"""
    today = datetime.now()
    date_str = today.strftime("%Y年%m月%d日")
    
    # 使用统一模板
    email = create_daily_email("📋 每日工作日报", f"{date_str} · 权权管家指挥中心")
    
    # 1. 添加权权管家工作模块
    quanquan_html, quanquan_work = generate_quanquan_section()
    email.add_section("🦞 权权管家今日工作", "🦞", quanquan_html, highlight=True)
    
    # 2. 添加Agent优化追踪模块（仅当有变更时显示）
    opt_html, opt_count = generate_optimization_section()
    if opt_html:
        email.add_section("🚀 今日Agent优化", "🚀", opt_html, highlight=True)
    
    # 3. 添加全体Agent工作表格
    agents_html, agent_count, has_work = generate_agents_table()
    if has_work:
        email.add_section(f"🤖 全体Agent工作状态（共{agent_count}个，有工作记录已高亮）", "🤖", agents_html)
    else:
        email.add_section(f"🤖 全体Agent工作状态（共{agent_count}个）", "🤖", agents_html)
    
    # 4. 添加统计
    email.add_stats_bar([
        {'icon': '🦞', 'label': '权权管家任务', 'value': f"{len([w for w in quanquan_work if w != '今日暂无工作记录'])} 项"},
        {'icon': '🚀', 'label': 'Agent优化', 'value': f"{opt_count} 项"},
        {'icon': '🤖', 'label': 'Agent总数', 'value': f"{agent_count} 个"},
        {'icon': '📅', 'label': '日期', 'value': date_str},
    ])
    
    # 生成纯文本版本
    text_content = f"""📋 每日工作日报 - {date_str}

🦞 权权管家今日工作:
"""
    for item in quanquan_work:
        text_content += f"  • {item}\n"
    
    text_content += f"\n🚀 今日Agent优化（{opt_count}项）:\n"
    if opt_count > 0:
        opts = get_today_optimizations()
        for opt in opts:
            text_content += f"  • [{opt['type']}] {opt['agent']}: {opt['description']}\n"
    
    text_content += f"\n🤖 全体Agent工作状态（共{agent_count}个）:\n"
    text_content += "  详见HTML邮件表格\n"
    
    text_content += "\n🦞 权权管家指挥中心自动生成"
    
    return email.render(), text_content


def send_email(subject, html_content, text_content, to_email=None):
    """发送邮件"""
    config = load_config()
    
    smtp_server = config.get('smtp_server', 'smtp.qq.com')
    smtp_port = config.get('smtp_port', 465)
    smtp_user = config.get('smtp_user')
    smtp_pass = config.get('smtp_pass')
    
    if not smtp_user or not smtp_pass:
        print("错误: 邮件配置不完整")
        return False
    
    if not to_email:
        to_email = config.get('to_email', smtp_user)
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"=?utf-8?b?5p2D5p2D5YW755qE6Jm+77yI566h5a6277yJ?= <{smtp_user}>"
        msg['To'] = to_email
        
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        if smtp_port == 465 or 'qq.com' in smtp_server:
            server = smtplib.SMTP_SSL(smtp_server, 465)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        
        print(f"✓ 邮件发送成功: {to_email}")
        return True
        
    except Exception as e:
        print(f"✗ 邮件发送失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='日报生成与发送')
    parser.add_argument('--send', action='store_true', help='立即发送日报')
    parser.add_argument('--preview', action='store_true', help='预览日报内容')
    
    args = parser.parse_args()
    
    html_report, text_report = generate_daily_report()
    
    if args.preview:
        print(text_report)
        return
    
    if args.send:
        today = datetime.now().strftime("%Y年%m月%d日")
        subject = f"📋 日报 - {today}"
        success = send_email(subject, html_report, text_report)
        sys.exit(0 if success else 1)
    
    print(text_report)


if __name__ == '__main__':
    main()
