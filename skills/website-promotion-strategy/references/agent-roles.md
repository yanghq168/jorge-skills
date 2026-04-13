# 网站宣传策略Agent角色职责说明

## Agent角色总览

| Agent | 职责 | 输入 | 输出 | 依赖 |
|-------|------|------|------|------|
| 网站分析Agent | 爬取分析网站内容 | 网站URL | 网站画像 | 无 |
| 竞品分析Agent | 分析竞品策略 | 行业信息 | 竞品洞察 | 网站分析Agent |
| 宣传策略Agent | 制定宣传方案 | 网站+竞品 | 策略方案 | 竞品分析Agent |
| 内容创作Agent | 创作宣传素材 | 策略方案 | 内容素材 | 宣传策略Agent |
| 渠道规划Agent | 制定投放计划 | 内容+受众 | 渠道计划 | 内容创作Agent |

---

## 1. 网站分析Agent (website_analyzer)

### 核心职责
爬取目标网站，全面分析产品定位、目标受众、核心卖点、视觉风格和内容调性。

### 工作流程
1. **页面爬取**: 使用浏览器自动化访问目标网站
2. **内容提取**: 提取首页、产品页、关于我们等关键页面内容
3. **截图分析**: 捕获页面截图分析视觉风格
4. **信息结构化**: 整理为结构化的网站画像

### 分析维度

#### 基础信息
- 网站/产品名称
- 一句话描述
- 所属行业
- 成立时间（如有）

#### 定位分析
- 市场定位（高端/大众/垂直等）
- 目标用户群体
- 核心价值主张
- 与竞品的差异化

#### 功能/卖点
- 核心功能列表
- 主打卖点（最多3个）
- 技术优势
- 服务特色

#### 风格调性
- 视觉风格（简约/活泼/专业/科技等）
- 色彩方案
- 语调风格（正式/亲切/幽默等）
- 品牌形象

### 输出规范
```yaml
网站画像结构:
  website:
    url: "https://example.com"
    name: "产品名称"
    description: "一句话描述"
    industry: "行业"
    
  positioning:
    market_position: "市场定位"
    target_audience:
      demographics: "人口统计特征"
      psychographics: "心理特征"
      pain_points: ["痛点1", "痛点2"]
    value_proposition: "核心价值主张"
    
  core_features:
    - feature: "功能1"
      benefit: "用户收益"
    - feature: "功能2"
      benefit: "用户收益"
      
  visual_style:
    style: "视觉风格"
    color_scheme: ["主色", "辅色"]
    typography: "字体风格"
    imagery: "图片风格"
    
  tone_of_voice:
    personality: "品牌人格"
    language_style: "语言风格"
    emotional_appeal: "情感诉求"
```

---

## 2. 竞品分析Agent (competitor_analyst)

### 核心职责
分析行业竞品，识别市场机会和差异化空间，为策略制定提供情报支持。

### 工作流程
1. **竞品识别**: 基于行业定位识别主要竞品
2. **策略收集**: 收集竞品的宣传策略和渠道
3. **差异化分析**: 分析竞品优劣势
4. **机会识别**: 发现市场空白和差异化机会

### 分析维度

#### 竞品识别
- 直接竞品（解决同样问题）
- 间接竞品（满足同样需求）
- 替代方案（不同方式解决）

#### 策略分析
- 主打卖点
- 宣传角度
- 渠道选择
- 内容调性

#### 差距分析
- 竞品未覆盖的痛点
- 竞品做得不好的地方
- 市场空白机会
- 差异化切入点

### 输出规范
```yaml
竞品分析结构:
  competitors:
    - name: "竞品A"
      type: "直接竞品"
      positioning: "定位"
      strengths: ["优势1", "优势2"]
      weaknesses: ["劣势1", "劣势2"]
      strategy:
        key_message: "核心信息"
        channels: ["渠道1", "渠道2"]
        
  market_gaps:
    - gap: "市场空白"
      opportunity: "机会描述"
      difficulty: "进入难度"
      
  differentiation_opportunities:
    - opportunity: "差异化机会"
      approach: "切入方式"
      advantage: "优势"
```

---

## 3. 宣传策略Agent (strategy_planner)

### 核心职责
基于网站分析和竞品洞察，制定差异化的宣传策略和传播方案。

### 工作流程
1. **策略定位**: 确定宣传的核心定位和角度
2. **信息设计**: 设计3-5条核心传播信息
3. **创意概念**: 提出2-3个活动创意方向
4. **传播策略**: 制定整体传播策略框架

### 策略要素

#### 定位宣言
- 我们是谁
- 我们为谁服务
- 我们提供什么独特价值
- 我们与竞品的不同

#### 核心信息
- 主信息：最核心的传播点
- 支撑信息：2-4条支撑主信息的论点
- 每条信息都要有差异化

#### 活动创意
- 大创意概念（Big Idea）
- 传播主题
- 创意延展方向

### 输出规范
```yaml
策略方案结构:
  positioning_statement: |
    对于[target_audience]来说，
    [product_name]是[category]中唯一[unique_attribute]的选择，
    因为[reason_to_believe]
    
  key_messages:
    primary: "核心主信息"
    supporting:
      - "支撑信息1"
      - "支撑信息2"
      - "支撑信息3"
      
  differentiation:
    from_competitor_A: "与竞品A的差异化"
    from_competitor_B: "与竞品B的差异化"
    unique_value: "独特价值主张"
    
  campaign_concepts:
    - concept: "创意概念A"
      theme: "传播主题"
      tagline: "标语"
      visual_direction: "视觉方向"
    - concept: "创意概念B"
      theme: "传播主题"
      tagline: "标语"
      visual_direction: "视觉方向"
```

---

## 4. 内容创作Agent (content_creator)

### 核心职责
根据策略方案创作各类宣传内容素材，包括文案、视觉概念、视频脚本。

### 工作流程
1. **标语创作**: 创作多个版本的主标语
2. **文案撰写**: 撰写各渠道适配的文案
3. **视觉概念**: 设计海报、banner的视觉概念
4. **视频脚本**: 撰写宣传视频脚本

### 内容类型

#### 标语口号
- 主标语（10字以内）
- 副标语（15字以内）
- 系列标语（3-5条）

#### 渠道文案
- 社交媒体文案（微博/微信/抖音）
- 广告文案（信息流/搜索广告）
- 落地页文案
- 邮件文案

#### 视觉概念
- 主视觉概念描述
- 海报设计方向
- Banner设计方向
- 社交媒体配图方向

#### 视频脚本
- 15秒短视频脚本
- 30秒广告脚本
- 3分钟品牌片脚本

### 输出规范
```yaml
内容素材结构:
  taglines:
    primary: "主标语"
    secondary: "副标语"
    alternatives: ["备选1", "备选2", "备选3"]
    
  copy_variations:
    social_media:
      weibo: "微博版本文案"
      wechat: "微信版本文案"
      douyin: "抖音版本文案"
    ads:
      feed: "信息流广告文案"
      search: "搜索广告文案"
    landing_page:
      headline: "落地页主标题"
      subheadline: "副标题"
      cta: "行动号召"
      
  visual_concepts:
    - type: "主视觉"
      description: "概念描述"
      elements: ["元素1", "元素2"]
      color_palette: "配色方案"
      mood: "氛围"
    - type: "海报"
      description: "概念描述"
      layout: "版式"
      key_visual: "核心视觉"
      
  video_scripts:
    - duration: "15秒"
      format: "竖屏"
      script: |
        [0-5s] 画面：...
        旁白：...
        [5-10s] 画面：...
        旁白：...
        [10-15s] 画面：...
        旁白：...
```

---

## 5. 渠道规划Agent (channel_planner)

### 核心职责
制定渠道组合策略、预算分配方案和投放时间线。

### 工作流程
1. **渠道筛选**: 根据目标受众选择合适渠道
2. **预算分配**: 合理分配各渠道预算
3. **时间规划**: 制定投放时间线和节奏
4. **KPI设定**: 设定各渠道的关键指标

### 渠道类型

#### 付费渠道
- 信息流广告（字节系/腾讯系/百度系）
- 搜索广告（SEM）
- 社交媒体广告
- KOL/KOC合作

#### 自有渠道
- 官网/落地页
- 公众号/视频号
- 邮件营销
- 私域社群

####  earned渠道
- SEO/内容营销
- 媒体报道
- 用户口碑
- 社媒传播

### 输出规范
```yaml
渠道计划结构:
  channel_mix:
    paid:
      - channel: "信息流广告"
        platform: ["抖音", "微信朋友圈"]
        budget_percent: 40
        objective: "曝光+转化"
        kpis:
          - metric: "曝光量"
            target: "100万+"
          - metric: "点击率"
            target: "3%+"
            
    owned:
      - channel: "公众号"
        content_type: "深度文章"
        frequency: "每周2篇"
        objective: "品牌认知"
        
    earned:
      - channel: "媒体报道"
        approach: "新闻稿+专访"
        target_media: ["36氪", "虎嗅"]
        
  budget_allocation:
    total_budget: "总预算"
    by_channel:
      "信息流广告": "40%"
      "KOL合作": "30%"
      "内容制作": "20%"
      "其他": "10%"
      
  timeline:
    phase_1:
      name: "预热期"
      duration: "1周"
      activities: ["活动1", "活动2"]
    phase_2:
      name: "爆发期"
      duration: "2周"
      activities: ["活动3", "活动4"]
    phase_3:
      name: "持续期"
      duration: "1个月"
      activities: ["活动5"]
```

---

## 指挥官调度规则

### 1. 启动顺序
```
网站分析 → 竞品分析 → 宣传策略 → [内容创作 || 渠道规划]
```

### 2. 数据传递
- 网站分析输出 → 竞品分析输入
- 竞品分析输出 + 网站分析输出 → 宣传策略输入
- 宣传策略输出 → 内容创作 + 渠道规划输入

### 3. 确认点
- **策略方向确认**: 宣传策略Agent完成后需用户确认方向正确，再生成内容

### 4. 异常处理
- **网站分析失败**: 重试2次，仍失败询问用户是否手动提供信息
- **竞品分析失败**: 重试1次，仍失败跳过继续
- **策略制定失败**: 重试2次，仍失败使用模板策略
