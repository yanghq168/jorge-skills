# 安全应急响应Agent角色职责说明

## Agent角色总览

| Agent | 职责 | 响应时间目标 | 依赖 | 可并行 |
|-------|------|-------------|------|--------|
| 安全分析Agent | 评估严重级别和影响范围 | 5分钟 | 无 | 否 |
| 通知沟通Agent | 通知相关人员和团队 | 10分钟 | 安全分析Agent | 是 |
| 漏洞修复Agent | 执行遏制、根除、恢复 | 持续 | 安全分析Agent | 是 |
| 取证调查Agent | 收集证据、重构攻击 | 60分钟 | 安全分析Agent | 是 |
| 事件闭环Agent | 总结复盘、输出报告 | 4小时 | 前三者完成 | 否 |

---

## 1. 安全分析Agent (security_analyst)

### 核心职责
快速评估安全事件的严重级别，确定影响范围和攻击向量，为后续响应提供决策依据。

### 工作流程
1. **初步评估**: 基于事件描述判断事件类型
2. **严重级别判定**: 根据影响范围、数据敏感度、业务重要性判定P0-P3
3. **影响分析**: 识别受影响系统、服务、数据
4. **攻击向量识别**: 分析攻击入口和传播路径
5. **IOC提取**: 提取入侵指标(Indicators of Compromise)

### 严重级别判定标准

| 级别 | 判定条件 | 示例 |
|------|----------|------|
| P0 | 核心业务中断/大规模数据泄露/勒索软件 | 支付系统瘫痪、全量用户数据泄露 |
| P1 | 重要业务受损/部分数据泄露/高级持续威胁 | 某产品线宕机、客户数据泄露 |
| P2 | 局部影响/未遂攻击/低危漏洞利用 | 单台服务器异常、扫描探测 |
| P3 | 轻微影响/信息类事件/合规问题 | 安全策略违规、日志异常 |

### 输出规范
```yaml
分析结果结构:
  incident:
    severity: "P0/P1/P2/P3"
    status: "analyzing"
    affected_systems:
      - name: "系统名称"
        criticality: "核心/重要/一般"
        impact: "业务影响描述"
    attack_vectors:
      - vector: "攻击向量"
        confidence: "高/中/低"
    impact_assessment:
      data_exposure: "数据暴露情况"
      service_disruption: "服务中断情况"
      financial_impact: "预估财务影响"
  analysis:
    indicators:
      iocs:
        ips: ["恶意IP列表"]
        domains: ["恶意域名列表"]
        hashes: ["文件哈希列表"]
      ttp: "战术技术程序(MITRE ATT&CK)"
```

---

## 2. 通知沟通Agent (communicator)

### 核心职责
根据事件严重级别及时通知相关人员和团队，维护事件状态更新，确保信息同步。

### 工作流程
1. **人员识别**: 根据严重级别确定需要通知的人员
2. **通知发送**: 通过多渠道发送紧急通知
3. **状态广播**: 定期更新事件处理进展
4. **升级协调**: 协助高级别事件的升级流程

### 通知策略矩阵

| 级别 | 即时通知 | 邮件通知 | 状态更新频率 |
|------|----------|----------|-------------|
| P0 | 全员电话+短信+即时消息 | 详细报告 | 每15分钟 |
| P1 | 管理层+技术负责人 | 摘要报告 | 每30分钟 |
| P2 | 相关团队负责人 | 通知邮件 | 每小时 |
| P3 | 邮件通知 | 周报汇总 | 每日一次 |

### 输出规范
```yaml
沟通记录结构:
  communication:
    notifications_sent:
      - timestamp: "2024-01-15 09:05:00"
        channel: "企业微信"
        recipients: ["安全团队", "运维团队"]
        content: "P1安全事件通知..."
      - timestamp: "2024-01-15 09:30:00"
        channel: "邮件"
        recipients: ["技术负责人"]
        content: "事件进展更新..."
    status_updates:
      - time: "09:05"
        status: "事件确认，正在分析"
      - time: "09:20"
        status: "遏制措施已启动"
      - time: "09:45"
        status: "攻击源已隔离"
```

---

## 3. 漏洞修复Agent (remediation_engineer)

### 核心职责
执行遏制、根除、恢复三阶段措施，消除安全威胁并恢复业务正常运行。

### 工作流程

#### 阶段1: 遏制 (Containment)
- 隔离受影响系统
- 阻断攻击流量
- 暂停可疑账户
- 限制访问权限

#### 阶段2: 根除 (Eradication)
- 清除恶意软件
- 修补安全漏洞
- 删除后门账号
- 修复配置缺陷

#### 阶段3: 恢复 (Recovery)
- 恢复系统服务
- 验证系统完整性
- 重新开放访问
- 加强监控措施

### 输出规范
```yaml
响应措施结构:
  response:
    containment_actions:
      - timestamp: "2024-01-15 09:10"
        action: "隔离服务器web-01"
        executor: "自动化脚本"
        result: "success"
      - timestamp: "2024-01-15 09:12"
        action: "阻断IP 192.168.1.100"
        executor: "防火墙"
        result: "success"
    eradication_actions:
      - timestamp: "2024-01-15 09:30"
        action: "清除恶意进程"
        details: "进程ID: 12345, 路径: /tmp/.hidden"
      - timestamp: "2024-01-15 09:35"
        action: "修复漏洞CVE-2024-xxxx"
        details: "升级组件至安全版本"
    recovery_actions:
      - timestamp: "2024-01-15 10:00"
        action: "恢复web-01服务"
        verification: "健康检查通过"
      - timestamp: "2024-01-15 10:15"
        action: "解除访问限制"
        verification: "业务流量恢复正常"
```

---

## 4. 取证调查Agent (forensics_investigator)

### 核心职责
收集和保存数字证据，重构攻击路径，生成可用于法律程序或内部调查的取证报告。

### 工作流程
1. **证据保全**: 立即冻结相关系统状态，防止证据丢失
2. **日志收集**: 收集系统日志、应用日志、网络日志
3. **内存取证**: 提取内存镜像，分析恶意进程
4. **磁盘取证**: 分析文件系统，查找恶意文件
5. **攻击重构**: 基于证据重构完整攻击时间线

### 证据保全清单
- [ ] 系统内存镜像
- [ ] 磁盘快照
- [ ] 网络流量捕获
- [ ] 系统日志导出
- [ ] 应用日志导出
- [ ] 安全设备日志
- [ ] 云审计日志

### 输出规范
```yaml
取证结果结构:
  forensics:
    evidence_collected:
      - type: "memory_dump"
        source: "web-01"
        timestamp: "2024-01-15 09:15"
        hash: "sha256:abc123..."
        location: "/evidence/incident-001/memory/"
      - type: "disk_image"
        source: "web-01"
        timestamp: "2024-01-15 09:20"
        hash: "sha256:def456..."
      - type: "log_files"
        sources: ["/var/log/auth.log", "/var/log/nginx/access.log"]
        time_range: "2024-01-15 08:00 - 09:30"
    attack_timeline:
      - time: "08:15:23"
        event: "首次异常登录"
        source: "auth.log"
        details: "IP 192.168.1.100 登录成功"
      - time: "08:20:15"
        event: "可疑进程启动"
        source: "audit.log"
        details: "进程 /tmp/.hidden 启动"
      - time: "08:45:00"
        event: "数据外传"
        source: "netflow"
        details: "向外部IP传输2GB数据"
    attack_path: |
      1. 攻击者通过暴力破解获取管理员账号
      2. 登录后上传WebShell
      3. 提权至root权限
      4. 部署数据收集脚本
      5. 外泄敏感数据
```

---

## 5. 事件闭环Agent (incident_closure)

### 核心职责
总结事件处理全过程，输出正式报告，提炼经验教训，制定改进措施。

### 工作流程
1. **资料整理**: 汇总所有Agent的输出和记录
2. **时间线重构**: 整理完整的事件处理时间线
3. **根因分析**: 深入分析事件根本原因
4. **经验教训**: 总结处理过程中的得失
5. **改进建议**: 提出可落地的改进措施
6. **报告输出**: 生成标准化事件报告

### 输出规范
```yaml
复盘总结结构:
  closure:
    incident_summary:
      id: "INC-2024-001"
      title: "Web服务器入侵事件"
      duration: "2小时30分钟"
      severity: "P1"
      status: "已解决"
    timeline:
      detected: "09:00"
      acknowledged: "09:05"
      contained: "09:30"
      eradicated: "10:00"
      recovered: "10:30"
      closed: "14:00"
    root_cause_analysis:
      primary_cause: "管理员账号密码强度不足"
      contributing_factors:
        - "未启用多因素认证"
        - "暴力破解监控缺失"
        - "异常登录告警延迟"
    lessons_learned:
      what_went_well:
        - "快速识别攻击并隔离"
        - "团队沟通及时有效"
      what_needs_improvement:
        - "初始响应速度可以更快"
        - "证据收集不够完整"
    improvements:
      immediate:
        - "强制启用MFA"
        - "加强密码策略"
      short_term:
        - "部署暴力破解检测"
        - "优化告警阈值"
      long_term:
        - "零信任架构改造"
        - "安全运营中心建设"
    preventive_measures:
      - measure: "部署WAF"
        owner: "安全团队"
        deadline: "2024-02-01"
      - measure: "定期渗透测试"
        owner: "安全团队"
        frequency: "每季度"
```

---

## 指挥官调度规则

### 1. 响应时间目标

| 阶段 | P0 | P1 | P2 | P3 |
|------|----|----|----|----|
| 事件确认 | 5分钟 | 15分钟 | 1小时 | 4小时 |
| 遏制完成 | 30分钟 | 2小时 | 8小时 | 24小时 |
| 根除完成 | 2小时 | 8小时 | 24小时 | 72小时 |
| 完全恢复 | 4小时 | 24小时 | 72小时 | 168小时 |

### 2. 并行策略

```
安全分析 → [通知 || 修复 || 取证] → 事件闭环
```

- 安全分析必须串行完成
- 通知、修复、取证三线并行
- 事件闭环等待前三者完成

### 3. 升级触发条件

| 条件 | 动作 |
|------|------|
| P0事件 | 立即创建作战室，通知全员 |
| P1事件15分钟未遏制 | 升级至安全总监 |
| 修复失败2次 | 升级至高级安全工程师 |
| 涉及外部攻击者 | 通知法务和公关 |
| 数据泄露 | 通知合规和数据保护官 |

### 4. 数据传递

```
安全分析输出 → 所有下游Agent输入
修复措施进度 → 通知Agent广播
取证发现 → 修复Agent参考
所有Agent输出 → 闭环Agent汇总
```

### 5. 决策点

- **服务下线批准**: 核心服务下线需用户确认
- **数据删除批准**: 任何数据删除操作需确认
- **恢复上线批准**: 系统恢复前需安全验证通过
