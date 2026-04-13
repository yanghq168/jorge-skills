# Seedance 2.0视频剧本Agent角色职责说明

## Agent角色总览

| Agent | 职责 | 输入 | 输出 | 依赖 |
|-------|------|------|------|------|
| 需求分析Agent | 理解视频需求 | 用户原始需求 | 需求文档 | 无 |
| 剧本结构Agent | 设计5分钟结构 | 需求文档 | 剧本结构 | 需求分析Agent |
| 分镜设计Agent | 设计详细分镜 | 剧本结构 | 分镜表 | 剧本结构Agent |
| 提示词生成Agent | 生成Seedance提示词 | 分镜表 | 提示词列表 | 分镜设计Agent |
| 审核优化Agent | 检查质量并打包 | 全部内容 | 最终剧本包 | 提示词生成Agent |

---

## 1. 需求分析Agent (requirement_analyst)

### 核心职责
深入理解用户的视频需求，明确主题、风格、受众、核心信息，为后续创作奠定基础。

### 工作流程
1. **需求收集**: 通过提问澄清用户需求
2. **受众分析**: 分析目标受众特征和偏好
3. **信息提炼**: 确定核心传播信息
4. **风格定义**: 明确视觉和叙事风格
5. **参考收集**: 了解用户的参考偏好

### 关键问题清单

#### 基础信息
- 视频主题是什么？
- 这个视频的主要目的是什么？
  - 品牌宣传
  - 产品介绍
  - 教育科普
  - 故事讲述
  - 情感共鸣
- 目标受众是谁？
  - 年龄段
  - 职业/身份
  - 兴趣爱好
  - 痛点需求

#### 内容信息
- 需要传达什么核心信息？（最多3条）
- 希望观众看完视频后做什么？
- 有什么必须包含的内容或元素？

#### 风格偏好
-  preferred视觉风格？
  - 科技感/未来感
  - 温馨/治愈
  - 搞笑/轻松
  - 悬疑/紧张
  - 纪实/真实
  - 华丽/梦幻
- 参考视频或风格？（可提供链接）
- 色彩偏好？

#### 技术要求
- 需要旁白/配音吗？
- 语言是中文还是英文？
- 音乐风格偏好？

### 输出规范
```yaml
需求文档结构:
  requirements:
    topic: "视频主题"
    
    style:
      visual: "视觉风格"
      narrative: "叙事风格"
      color_palette: "配色偏好"
      mood: "整体氛围"
      
    target_audience:
      demographics:
        age: "年龄段"
        gender: "性别倾向"
        occupation: "职业"
      psychographics:
        interests: ["兴趣1", "兴趣2"]
        pain_points: ["痛点1", "痛点2"]
        motivations: ["动机1", "动机2"]
        
    purpose: "视频目的"
    
    key_messages:
      - message: "核心信息1"
        priority: "高"
      - message: "核心信息2"
        priority: "中"
        
    tone: "语调风格"
    
    references:
      - type: "参考视频"
        link: "URL"
        notes: "参考点"
      - type: "风格参考"
        description: "描述"
```

---

## 2. 剧本结构Agent (script_structurer)

### 核心职责
设计5分钟视频的整体叙事结构，合理分配时长，确保故事完整且有节奏感。

### 5分钟剧本结构标准

#### 标准结构（推荐）
```
开头 (0:00-0:30)    - 10%  - 吸引注意，建立情境
发展 (0:30-3:30)   - 60%  - 展开内容，递进信息
高潮 (3:30-4:30)   - 20%  - 核心展示，情感顶点
结尾 (4:30-5:00)   - 10%  - 总结升华，行动号召
```

#### 各段落功能

**开头 (Hook)**
- 目标：3秒内抓住观众
- 技巧：视觉冲击、悬念、问题、冲突
- 内容：建立情境，引入主题

**发展 (Build-up)**
- 目标：层层递进，保持兴趣
- 技巧：信息递进、情绪积累、冲突升级
- 内容：核心内容展开，信息传递

**高潮 (Climax)**
- 目标：情感顶点，核心展示
- 技巧：最强视觉冲击、最强烈情感、核心 reveal
- 内容：产品展示、观点表达、情感爆发

**结尾 (Resolution)**
- 目标：收束全片，留下印象
- 技巧：总结、升华、call-to-action
- 内容：核心信息回顾、品牌展示、行动引导

### 场景设计原则

#### 场景数量
- 5分钟视频：8-12个场景
- 每个场景：2-4个分镜
- 场景之间：要有逻辑连接

#### 场景类型
- **叙事场景**：推进故事
- **展示场景**：展示产品/服务
- **情感场景**：营造氛围
- **过渡场景**：连接转折

### 输出规范
```yaml
剧本结构:
  script:
    title: "视频标题"
    logline: "一句话概括视频内容"
    
    structure:
      opening:
        time_range: "0:00-0:30"
        duration_seconds: 30
        purpose: "吸引注意，建立情境"
        key_moment: "关键情节点"
        
      development:
        time_range: "0:30-3:30"
        duration_seconds: 180
        purpose: "展开内容，递进信息"
        beats:
          - beat: "情节点1"
            time: "0:30-1:30"
          - beat: "情节点2"
            time: "1:30-2:30"
          - beat: "情节点3"
            time: "2:30-3:30"
            
      climax:
        time_range: "3:30-4:30"
        duration_seconds: 60
        purpose: "高潮点，核心展示"
        key_moment: "核心展示内容"
        
      ending:
        time_range: "4:30-5:00"
        duration_seconds: 30
        purpose: "总结升华，行动号召"
        call_to_action: "行动号召内容"
    
    scenes:
      - scene_number: 1
        name: "场景名称"
        time_range: "0:00-0:30"
        duration: 30
        description: "场景描述"
        purpose: "场景功能"
        key_elements: ["元素1", "元素2"]
```

---

## 3. 分镜设计Agent (storyboard_designer)

### 核心职责
为每个场景设计详细分镜，精确控制时长，确保画面可被执行。

### 分镜设计原则

#### 分镜数量
- 5分钟视频：20-30个分镜
- 每个分镜：5-20秒
- 平均每个分镜：10-12秒

#### 分镜要素
每个分镜必须包含：
1. **镜头编号**
2. **时间码**（起始-结束）
3. **画面描述**（详细视觉描述）
4. **镜头类型**
5. **运镜方式**
6. **时长**
7. **旁白/对白**（如有）
8. **音效/音乐提示**（如有）

### 镜头类型

| 类型 | 英文 | 用途 |
|------|------|------|
| 远景/ establishing | Wide shot / Establishing shot | 展示环境，建立空间 |
| 全景 | Full shot | 展示人物全身 |
| 中景 | Medium shot | 展示人物腰部以上 |
| 近景 | Medium close-up | 展示人物胸部以上 |
| 特写 | Close-up | 展示面部表情或细节 |
| 大特写 | Extreme close-up | 展示极细节（眼睛、手指等）|
| 过肩镜头 | Over-the-shoulder | 对话场景 |
| POV镜头 | Point-of-view | 主观视角 |
| 航拍 | Aerial shot | 俯瞰视角 |

### 运镜方式

| 方式 | 英文 | 效果 |
|------|------|------|
| 固定 | Static | 稳定、正式 |
| 推 | Dolly in | 强调、聚焦 |
| 拉 | Dolly out | 展开、 reveal |
| 摇 | Pan | 展示空间 |
| 俯仰 | Tilt | 展示高度 |
| 横移 | Truck / Dolly sideways | 跟随移动 |
| 手持 | Handheld | 真实、紧张 |
| 稳定器 | Gimbal | 流畅移动 |

### 输出规范
```yaml
分镜表结构:
  storyboard:
    total_duration: 300  # 总时长秒数
    total_shots: 25      # 总分镜数
    
    shots:
      - shot_number: 1
        scene: 1
        timecode: "0:00-0:05"
        duration: 5
        
        visual:
          description: "画面内容详细描述"
          subject: "主体"
          action: "动作"
          environment: "环境"
          lighting: "光线"
          
        technical:
          shot_type: "镜头类型"
          camera_movement: "运镜方式"
          angle: "角度"
          lens: "镜头焦段"
          
        audio:
          narration: "旁白内容"
          sound_effect: "音效"
          music: "音乐提示"
          
      - shot_number: 2
        # ...
```

---

## 4. 提示词生成Agent (prompt_engineer)

### 核心职责
将分镜转化为Seedance 2.0可用的英文提示词，确保AI能准确理解并生成画面。

### Seedance 2.0提示词结构

#### 标准格式
```
[Subject], [Action], [Environment], [Lighting], [Camera], [Style], [Quality]
```

#### 各组成部分

**Subject（主体）**
- 明确的主体描述
- 外观特征（服装、颜色、形态）
- 避免模糊描述

**Action（动作）**
- 具体动作描述
- 动作速度（slowly, quickly）
- 避免过于复杂的动作

**Environment（环境）**
- 场景设置
- 背景元素
- 氛围描述

**Lighting（光线）**
- 光源类型（natural, artificial, neon）
- 光线质量（soft, harsh, dramatic）
- 时间（golden hour, night, sunset）

**Camera（镜头）**
- 镜头类型（close-up, wide shot）
- 角度（low angle, high angle, eye level）
- 运镜（static, slow pan, handheld）

**Style（风格）**
- cinematic（电影感）
- photorealistic（照片级真实）
- dreamy（梦幻）
- futuristic（未来感）
- vintage（复古）

**Quality（质量）**
- 8k, highly detailed
- professional photography
- masterpiece, best quality

### 提示词技巧

#### DO（推荐）
- 使用具体、详细的描述
- 指定镜头类型和角度
- 描述光线条件
- 使用专业摄影术语
- 包含风格关键词

#### DON'T（避免）
- 抽象概念（"展示快乐" → "person smiling brightly"）
- 过于复杂的场景
- 快速、剧烈的动作
- 多个主体同时复杂动作
- 文字内容（AI生成文字不稳定）

### 输出规范
```yaml
提示词结构:
  prompts:
    shot_prompts:
      - shot_number: 1
        prompt: |
          Close-up portrait of a young professional woman wearing smart casual outfit, 
          looking at camera with confident smile, modern office background with soft bokeh, 
          natural window lighting, soft and warm, eye-level angle, static shot, 
          cinematic, photorealistic, 8k, highly detailed, professional photography
        negative_prompt: |
          blurry, low quality, distorted face, extra limbs, deformed, 
          cartoon, anime, painting, illustration
          
      - shot_number: 2
        # ...
        
    style_prompts:
      overall_style: "cinematic, photorealistic, 8k"
      color_grading: "warm tones, high contrast"
      mood: "professional, inspiring"
      
    negative_prompts:
      common: |
        blurry, low quality, distorted, deformed, 
        cartoon, anime, painting, illustration, 
        watermark, text, logo, signature
```

---

## 5. 审核优化Agent (quality_reviewer)

### 核心职责
全面检查剧本的完整性、准确性、可行性，确保输出质量。

### 检查清单

#### 结构检查
- [ ] 总时长是否正好5分钟（300秒）
- [ ] 结构比例是否合理（开头10%-发展60%-高潮20%-结尾10%）
- [ ] 叙事是否完整（起承转合）
- [ ] 逻辑是否连贯

#### 分镜检查
- [ ] 分镜数量是否合理（20-30个）
- [ ] 每个分镜时长是否在5-20秒范围内
- [ ] 镜头类型是否多样
- [ ] 运镜方式是否合适
- [ ] 画面描述是否清晰

#### 提示词检查
- [ ] 是否都是英文
- [ ] 描述是否具体详细
- [ ] 是否包含必要的要素（主体、环境、光线等）
- [ ] 是否针对Seedance优化
- [ ] 是否有负面提示词

#### Seedance适配检查
- [ ] 是否有文字内容（应避免）
- [ ] 是否有过于快速的动作
- [ ] 场景复杂度是否适中
- [ ] 人物面部是否清晰（特写效果更好）

### 输出规范
```yaml
审核报告:
  review_report:
    summary:
      total_duration: 300
      total_shots: 25
      status: "通过/需修改"
      
    checks:
      structure:
        status: "通过"
        notes: "结构完整，比例合理"
      storyboard:
        status: "通过"
        notes: "分镜清晰，时长准确"
      prompts:
        status: "需修改"
        issues:
          - "Shot 12描述不够具体"
          - "Shot 18动作可能过快"
        suggestions:
          - "建议细化Shot 12的环境描述"
          - "建议将Shot 18的动作放慢"
          
  final_package:
    script_document: "完整剧本文档（Markdown）"
    storyboard_table: "分镜表（表格格式）"
    prompt_list: "提示词列表（可复制格式）"
    usage_guide: |
      ## Seedance 2.0使用说明
      
      1. 访问 Seedance 2.0平台
      2. 选择"文生视频"模式
      3. 复制下方提示词到输入框
      4. 选择比例（推荐16:9）
      5. 点击生成
      6. 下载生成的视频片段
      7. 使用剪辑软件拼接所有片段
      8. 添加旁白/音乐
      9. 导出最终视频
      
      ### 生成顺序建议
      按分镜编号顺序逐个生成，便于后期拼接
      
      ### 注意事项
      - 每个片段生成可能需要1-5分钟
      - 如生成效果不佳，可微调提示词重试
      - 建议先生成关键镜头测试风格
```

---

## 指挥官调度规则

### 1. 启动顺序
```
需求分析 → 剧本结构 → 分镜设计 → 提示词生成 → 审核优化
```

全串行，每个环节必须完成才能进入下一步。

### 2. 确认点
- **结构确认**: 剧本结构Agent完成后需确认结构方向
- **分镜确认**: 分镜设计Agent完成后需确认分镜细节

### 3. 时长控制
- 剧本结构Agent设定各段落时长
- 分镜设计Agent精确控制每个分镜时长
- 审核优化Agent验证总时长是否为300秒

### 4. 异常处理
- **需求分析失败**: 使用模板需求
- **结构失败**: 使用标准5分钟结构
- **分镜失败**: 简化分镜数量
- **提示词失败**: 手动提供基础提示词
