#!/usr/bin/env python3
"""
多用户记忆管理系统
为每个飞书用户创建独立的记忆空间
"""

import os
import json
from pathlib import Path
from datetime import datetime

class UserMemoryManager:
    """管理多用户记忆隔离"""
    
    def __init__(self, base_path="/root/.openclaw/workspace"):
        self.base_path = Path(base_path)
        self.users_dir = self.base_path / "users"
        self.users_dir.mkdir(exist_ok=True)
    
    def get_user_dir(self, user_id):
        """获取用户专属目录"""
        user_dir = self.users_dir / user_id
        user_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (user_dir / "memory").mkdir(exist_ok=True)
        (user_dir / "config").mkdir(exist_ok=True)
        (user_dir / "skills").mkdir(exist_ok=True)
        
        return user_dir
    
    def get_user_memory_file(self, user_id, date=None):
        """获取用户每日记忆文件路径"""
        if date is None:
            date = datetime.now()
        
        user_dir = self.get_user_dir(user_id)
        memory_file = user_dir / "memory" / f"{date.strftime('%Y-%m-%d')}.md"
        return memory_file
    
    def get_user_longterm_memory(self, user_id):
        """获取用户长期记忆文件路径"""
        user_dir = self.get_user_dir(user_id)
        return user_dir / "MEMORY.md"
    
    def get_user_config(self, user_id):
        """获取用户配置文件路径"""
        user_dir = self.get_user_dir(user_id)
        return user_dir / "config" / "user_config.json"
    
    def init_user(self, user_id, user_info=None):
        """初始化新用户"""
        user_dir = self.get_user_dir(user_id)
        
        # 创建默认配置文件
        config_file = self.get_user_config(user_id)
        if not config_file.exists():
            default_config = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "email": None,
                "timezone": "GMT+8",
                "preferences": {
                    "model": "kimi-coding/k2p5",
                    "language": "zh-CN"
                },
                "crypto_alerts": {
                    "price_alerts": [],
                    "funding_alerts": True,
                    "liquidation_alerts": True
                },
                "email_schedule": {
                    "morning_news": "07:00",
                    "daily_report": "19:00",
                    "email_summary": "20:00",
                    "evening_news": "21:00"
                }
            }
            
            if user_info:
                default_config.update(user_info)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        # 创建默认长期记忆文件
        memory_file = self.get_user_longterm_memory(user_id)
        if not memory_file.exists():
            default_memory = f"""# MEMORY.md - 用户 {user_id} 的长期记忆

## 🦞 暴躁小龙虾的记忆

**用户ID**: {user_id}  
**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 👤 关于用户

- **Name**: 
- **Timezone**: GMT+8
- **沟通渠道**: 飞书(Feishu)
- **用户ID**: {user_id}

## ⚙️ 个人配置

### 默认模型
- **当前模型**: Kimi K2.5 (`kimi-coding/k2p5`)

### 已安装技能
- (待记录)

## 📝 重要记忆

(这里记录与用户相关的重要信息、偏好设置、历史决策等)

---
*记忆隔离模式已启用 - 此记忆仅对用户 {user_id} 可见*
"""
            with open(memory_file, 'w', encoding='utf-8') as f:
                f.write(default_memory)
        
        return user_dir
    
    def load_user_config(self, user_id):
        """加载用户配置"""
        config_file = self.get_user_config(user_id)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_user_config(self, user_id, config):
        """保存用户配置"""
        config_file = self.get_user_config(user_id)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def append_memory(self, user_id, content, date=None):
        """追加用户每日记忆"""
        memory_file = self.get_user_memory_file(user_id, date)
        
        timestamp = datetime.now().strftime('%H:%M')
        entry = f"\n## [{timestamp}]\n\n{content}\n\n---\n"
        
        if memory_file.exists():
            with open(memory_file, 'a', encoding='utf-8') as f:
                f.write(entry)
        else:
            # 创建新的每日记忆文件
            header = f"# {datetime.now().strftime('%Y-%m-%d')} - 用户 {user_id} 的记忆日志\n\n"
            with open(memory_file, 'w', encoding='utf-8') as f:
                f.write(header + entry)
        
        return memory_file
    
    def list_users(self):
        """列出所有用户"""
        if not self.users_dir.exists():
            return []
        
        users = []
        for user_dir in self.users_dir.iterdir():
            if user_dir.is_dir():
                user_id = user_dir.name
                config = self.load_user_config(user_id)
                users.append({
                    "user_id": user_id,
                    "config": config,
                    "created_at": config.get("created_at") if config else None
                })
        
        return users

# 全局实例
_memory_manager = None

def get_memory_manager():
    """获取全局记忆管理器实例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = UserMemoryManager()
    return _memory_manager

if __name__ == "__main__":
    # 测试
    manager = UserMemoryManager()
    
    # 初始化测试用户
    test_user = "ou_test123"
    manager.init_user(test_user, {
        "name": "Test User",
        "email": "test@example.com"
    })
    
    # 追加记忆
    manager.append_memory(test_user, "测试记忆内容")
    
    print(f"用户目录: {manager.get_user_dir(test_user)}")
    print(f"记忆文件: {manager.get_user_memory_file(test_user)}")
    print(f"长期记忆: {manager.get_user_longterm_memory(test_user)}")
    print(f"配置文件: {manager.get_user_config(test_user)}")
