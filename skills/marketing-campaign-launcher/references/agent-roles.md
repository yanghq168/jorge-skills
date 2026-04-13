# 营销活动启动Agent角色职责说明

## Agent角色总览

| Agent | 职责 | 输入 | 输出 | 依赖 |
|-------|------|------|------|------|
| 需求分析Agent | 收集和分析需求 | 用户原始需求 | 需求文档 | 无 |
| 策略制定Agent | 制定营销策略 | 需求文档 | 策略方案 | 需求分析Agent |
| 内容创作Agent | 创作营销内容 | 策略方案 | 内容素材包 | 策略制定Agent |
| 渠道分发Agent | 制定分发计划 | 内容素材+渠道策略 | 发布计划 | 内容创作Agent |
| 数据监控Agent | 设计监控方案 | KPI指标+发布计划 | 监控配置 | 策略制定Agent |

---

## 1. 需求分析Agent (requirement_analyst)

### 核心职责
收集用户营销活动需求，提炼关键信息，形成结构化的需求文档。

### 工作流程
1. **活动类型识别**: 判断是新品发布、促销活动、品牌宣传还是其他类型
2. **产品信息收集**: 了解产品特点、卖点、差异化优势
3. **目标受众分析**: 明确受众画像、痛点、需求场景
4. **资源确认**: 确认预算范围、时间周期、可用资源
5. **目标设定**: 明确活动的核心目标（曝光/转化/留存等）

### 输出规范
```yaml
需求文档结构:
  campaign_name: "活动名称"
  campaign_type: "活动类型"
  product_info:
    name: "产品名称"
    features: ["特点1", "特点2"]
    usp: "核心卖点"
  target_audience:
    demographics: "人口统计特征"
    psychographics: "心理特征"
    pain_points: ["痛点1", "痛点2"]
  budget:
    total: 总预算
    allocation: {渠道: 金额}
  timeline:
    start_date: "开始日期"
    end_date: "结束日期"
    milestones: [关键节点]
  goals:
    primary: "主要目标"
    secondary: ["次要目标"]
```

---

## 2. 策略制定Agent (strategy_planner)

### 核心职责
基于需求文档制定营销策略，包括定位、核心信息、渠道选择和KPI设计。

### 工作流程
1. **市场定位**: 确定产品在市场中的位置和差异化定位
2. **核心信息提炼**: 设计3-5条核心传播信息
3. **渠道策略**: 选择合适渠道并分配资源权重
4. **KPI设计**: 设定可衡量的关键绩效指标
5. **风险评估**: 识别潜在风险并提出应对预案

### 输出规范
```yaml
策略方案结构:
  positioning:
    statement: "定位宣言"
    differentiation: "差异化优势"
  key_messages:
    - message: "核心信息1"
      priority: "高/中/低"
    - message: "核心信息2"
  channels:
    - name: "渠道名称"
      weight: 权重百分比
      rationale: "选择理由"
  kpis:
    - metric: "指标名称"
      target: 目标值
      measurement: "衡量方式"
  risk_mitigation:
    - risk: "风险描述"
      solution: "应对方案"
```

---

## 3. 内容创作Agent (content_creator)

### 核心职责
根据策略方案创作各类营销内容素材。

### 工作流程
1. **文案创作**: 撰写各渠道适配的文案
2. **视觉概念**: 设计海报、banner的视觉概念
3. **多媒体规划**: 规划视频、音频等多媒体内容
4. **内容审核**: 确保内容符合品牌调性和合规要求

### 输出规范
```yaml
内容素材包结构:
  copywriting:
    headlines: ["主标题", "副标题"]
    body_copy: "正文文案"
    cta: "行动号召"
    variations:
      wechat: "微信版本"
      weibo: "微博版本"
      douyin: "抖音版本"
  visual_concepts:
    - type: "海报"
      concept: "视觉概念描述"
      color_scheme: "配色方案"
      key_elements: ["元素1", "元素2"]
    - type: "Banner"
      concept: "视觉概念描述"
  multimedia:
    videos:
      - type: "15秒短视频"
        script_outline: "脚本大纲"
      - type: "3分钟产品介绍"
        script_outline: "脚本大纲"
```

---

## 4. 渠道分发Agent (channel_distributor)

### 核心职责
制定内容分发计划，配置各渠道参数，确保内容在正确时间触达正确受众。

### 工作流程
1. **发布排期**: 制定详细的发布时间表
2. **渠道配置**: 配置各渠道的发送参数
3. **受众定向**: 设置各渠道的受众定向条件
4. **预算分配**: 细化各渠道的广告投放预算

### 输出规范
```yaml
发布计划结构:
  schedule:
    - datetime: "2024-01-15 09:00"
      channel: "微信公众号"
      content_type: "图文"
      content_ref: "content.copywriting.wechat"
    - datetime: "2024-01-15 10:00"
      channel: "微博"
      content_type: "图文"
      content_ref: "content.copywriting.weibo"
  channel_configs:
    wechat:
      account: "公众号名称"
      targeting: "受众定向条件"
      budget: 分配金额
    weibo:
      targeting: "粉丝+兴趣定向"
      promotion_budget: 推广预算
  automation_rules:
    - trigger: "发布时间到达"
      action: "自动发布"
    - trigger: "互动率>5%"
      action: "追加推广预算"
```

---

## 5. 数据监控Agent (data_monitor)

### 核心职责
设计数据监控方案，配置追踪指标和告警阈值，确保活动效果可衡量。

### 工作流程
1. **指标设计**: 设计多维度监控指标体系
2. **数据源配置**: 配置各渠道数据接入
3. **告警设置**: 设置关键指标的告警阈值
4. **报表设计**: 设计自动化报表模板

### 输出规范
```yaml
监控方案结构:
  metrics:
    exposure:
      - name: "曝光量"
        source: "各渠道API"
        frequency: "实时"
      - name: "触达人数"
        source: "各渠道API"
        frequency: "实时"
    engagement:
      - name: "点击率"
        formula: "点击数/曝光数"
        target: "3%"
      - name: "互动率"
        formula: "互动数/曝光数"
        target: "5%"
    conversion:
      - name: "转化率"
        formula: "转化数/点击数"
        target: "2%"
      - name: "ROI"
        formula: "收益/成本"
        target: "150%"
  alert_thresholds:
    - metric: "点击率"
      condition: "< 1%"
      severity: "warning"
      notify: ["营销负责人"]
    - metric: "ROI"
      condition: "< 100%"
      severity: "critical"
      notify: ["营销负责人", "财务负责人"]
  dashboard:
    refresh_interval: "5分钟"
    sections:
      - "实时数据概览"
      - "渠道对比"
      - "趋势分析"
      - "告警列表"
```

---

## 指挥官调度规则

### 1. 启动顺序
```
需求分析 → 策略制定 → [内容创作 || 数据监控] → 渠道分发
```

### 2. 数据传递
- 每个Agent完成任务后，将输出写入共享上下文
- 下游Agent从上下文中读取依赖数据
- 指挥官负责维护上下文的一致性和完整性

### 3. 异常处理
- **需求分析失败**: 重试2次，仍失败则询问用户手动输入
- **策略制定失败**: 重试1次，仍失败则使用默认模板
- **内容创作失败**: 重试2次，仍失败则跳过继续
- **其他失败**: 通知用户并等待决策

### 4. 用户确认点
- **策略方案审批**: 用户确认策略方案后再继续内容创作
- **内容审核**: 用户确认内容素材后再继续分发

### 5. 输出整合
指挥官将所有Agent的输出整合为一份完整的营销活动方案文档，包含：
- 活动概述
- 营销策略
- 内容素材清单
- 分发计划表
- 监控方案
