"""
AAG核心提示词模板
"""

from typing import Dict, Any
from langchain.prompts import PromptTemplate


# 快速略读提示词模板
SKIM_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["document_content", "document_type"],
    template="""请快速浏览以下{document_type}文档，提供结构化的概览信息。

文档内容：
{document_content}

请提供以下信息：
1. 文档类型识别（学术论文/技术报告/商业文档/其他）
2. 核心主题（50字以内概括文档的核心价值）
3. 关键要点（提取3-5个最重要的观点或发现）
4. 目标受众（这份文档主要面向什么人群）
5. 文档质量初评（高/中/低，并简要说明理由）
6. 建议的深度分析方向（基于文档特点，推荐2-3个值得深入分析的方向）

输出格式要求：
请以JSON格式输出，确保可以被解析。示例：
{{
    "document_type": "学术论文",
    "core_topic": "探讨人工智能在医疗诊断中的应用",
    "key_points": [
        "AI诊断准确率达到95%",
        "可减少误诊率30%",
        "需要大量标注数据"
    ],
    "target_audience": "医疗AI研究人员、医院管理者",
    "quality_assessment": {{
        "level": "高",
        "reason": "方法论严谨，数据充分"
    }},
    "analysis_suggestions": [
        "深入分析AI模型的技术细节",
        "评估实际应用的可行性",
        "探讨伦理和隐私问题"
    ]
}}"""
)


# 渐进式摘要提示词模板
PROGRESSIVE_SUMMARY_TEMPLATES = {
    "level_1": PromptTemplate(
        input_variables=["document_content"],
        template="""请用50字以内概括这份文档的核心价值。要求：
- 直击要点，避免冗余
- 使用清晰、专业的语言
- 突出最重要的信息

文档内容：
{document_content}

50字概括："""
    ),
    
    "level_2": PromptTemplate(
        input_variables=["document_content", "level_1_summary"],
        template="""基于以下文档，提供200字的详细摘要。

已有的50字概括：{level_1_summary}

请在200字内总结：
1. 主要论点和核心观点
2. 关键结论和发现
3. 重要的支撑证据

文档内容：
{document_content}

200字摘要："""
    ),
    
    "level_3": PromptTemplate(
        input_variables=["document_content", "level_1_summary", "level_2_summary"],
        template="""基于以下文档，提供500字的详细摘要。

已有摘要参考：
- 50字概括：{level_1_summary}
- 200字摘要：{level_2_summary}

请在500字内详细总结：
1. 文档的背景和目的
2. 主要内容和论述结构
3. 核心论点及其论证过程
4. 关键数据和案例
5. 主要结论和建议
6. 文档的价值和局限性

文档内容：
{document_content}

500字详细摘要："""
    ),
    
    "level_4": PromptTemplate(
        input_variables=["document_content", "level_2_summary"],
        template="""基于以下文档，生成1000字的深度分析摘要。

参考200字摘要：{level_2_summary}

请在1000字内提供深度分析，包括：

## 文档概述
- 文档类型、目的和受众
- 核心议题和研究问题

## 主要内容分析
- 论述结构和逻辑框架
- 各章节/部分的要点
- 关键概念和定义

## 论证分析
- 主要论点及其依据
- 使用的方法论
- 数据来源和可信度

## 发现与结论
- 主要发现
- 得出的结论
- 实际应用价值

## 批判性评价
- 优势和创新点
- 不足和局限性
- 改进建议

文档内容：
{document_content}

1000字深度分析摘要："""
    ),
    
    "level_5": PromptTemplate(
        input_variables=["document_content", "level_4_summary"],
        template="""基于以下文档，生成2000字的完整分析报告。

参考之前的分析：{level_4_summary}

请生成包含以下部分的2000字完整报告：

## 执行摘要
简要概述文档的核心价值和关键发现（200字）

## 背景与目的
- 文档产生的背景
- 研究/写作目的
- 目标受众分析

## 内容深度解析
- 详细的章节分析
- 核心论点深度剖析
- 重要概念详解
- 关键数据解读

## 方法论评估
- 使用的研究方法
- 数据收集和分析方法
- 方法的适当性评价

## 主要发现与洞察
- 关键发现详述
- 创新观点分析
- 与现有知识的关系

## 影响与应用
- 理论贡献
- 实践意义
- 潜在影响分析

## 批判性反思
- 深入的优缺点分析
- 潜在偏见识别
- 未解决的问题

## 建议与展望
- 具体行动建议
- 后续研究方向
- 长期影响预测

## 附录
- 重要引用
- 关键数据表
- 术语解释

文档内容：
{document_content}

2000字完整分析报告："""
    )
}


# 多维大纲提取模板
MULTI_DIM_OUTLINE_TEMPLATE = PromptTemplate(
    input_variables=["document_content"],
    template="""请从以下角度分析文档结构，生成多维度大纲：

文档内容：
{document_content}

请提供以下四个维度的大纲：

1. 逻辑大纲（Logical Outline）：
   - 展示章节层级结构
   - 标注各部分的逻辑关系
   - 突出论述流程

2. 主题大纲（Thematic Outline）：
   - 识别核心概念和主题
   - 展示概念之间的关系网络
   - 标注主题的重要性等级

3. 时间线大纲（Temporal Outline）：
   - 如文档包含时序信息，整理时间顺序
   - 标注关键时间节点
   - 展示事件发展脉络

4. 因果链大纲（Causal Chain Outline）：
   - 识别原因-结果关系
   - 构建因果推理链条
   - 标注因果关系的强度

输出格式：
请以结构化的JSON格式输出，包含以上四个维度的详细大纲。"""
)


# 知识图谱构建模板
KNOWLEDGE_GRAPH_TEMPLATE = PromptTemplate(
    input_variables=["document_content"],
    template="""构建这份文档的知识图谱。请识别和提取：

文档内容：
{document_content}

请提取以下信息：

1. 核心实体（Entities）：
   - 人物：姓名、角色、所属组织
   - 组织：名称、类型、地点
   - 概念：专业术语、理论、方法
   - 技术：工具、平台、算法

2. 关系类型（Relations）：
   - 定义关系：A定义了B
   - 包含关系：A包含B
   - 影响关系：A影响B
   - 对比关系：A与B对比
   - 使用关系：A使用B
   - 创建关系：A创建了B

3. 属性标注（Attributes）：
   - 重要性等级（高/中/低）
   - 出现频次
   - 首次出现位置
   - 相关上下文

输出格式：
{{
    "entities": [
        {{
            "id": "entity_1",
            "name": "实体名称",
            "type": "person|organization|concept|technology",
            "attributes": {{
                "importance": "high|medium|low",
                "frequency": 数字,
                "first_occurrence": "页码或段落"
            }}
        }}
    ],
    "relations": [
        {{
            "source": "entity_1",
            "target": "entity_2",
            "type": "defines|contains|influences|contrasts|uses|creates",
            "weight": 0.0-1.0
        }}
    ]
}}"""
)


# 分析规划提示词模板
ANALYSIS_PLANNER_TEMPLATE = PromptTemplate(
    input_variables=["document_info", "user_goals", "analysis_depth"],
    template="""你是一位专业的研究分析规划师。请基于以下信息制定详细的分析计划：

文档信息：
{document_info}

用户目标：
{user_goals}

分析深度：{analysis_depth}（basic|standard|deep|expert|comprehensive）

请制定一个结构化的分析计划，包括：

1. 分析步骤列表
   - 每个步骤包含：
     * 步骤ID和名称
     * 步骤目的和预期产出
     * 预计耗时（分钟）
     * 所需前置步骤（依赖关系）
     * 是否需要用户确认

2. 关键决策点
   - 需要用户参与决策的环节
   - 可能的分支路径

3. 预期产出物
   - 每个步骤的具体产出
   - 最终交付物清单

4. 资源需求
   - 预计token使用量
   - 预计总耗时

输出格式：
{{
    "analysis_plan": {{
        "total_steps": 步骤总数,
        "estimated_time_minutes": 预计总耗时,
        "estimated_tokens": 预计token用量,
        "steps": [
            {{
                "id": "step_1",
                "name": "步骤名称",
                "purpose": "步骤目的",
                "estimated_time": 预计耗时（分钟）,
                "dependencies": ["前置步骤ID列表"],
                "requires_user_input": true/false,
                "expected_output": "预期产出描述"
            }}
        ],
        "decision_points": [
            {{
                "step_id": "step_x",
                "description": "决策描述",
                "options": ["选项1", "选项2"]
            }}
        ],
        "deliverables": [
            "最终产出物1",
            "最终产出物2"
        ]
    }}
}}"""
)


# 深度分析提示词集合
DEEP_ANALYSIS_TEMPLATES = {
    # 证据链追踪
    "evidence_chain": PromptTemplate(
        input_variables=["document_content", "claim"],
        template="""对文档中的核心论点进行证据链追踪分析。

核心论点：{claim}

文档内容：
{document_content}

请进行以下分析：

1. 证据识别
   - 找出所有支撑该论点的证据
   - 标注证据在文档中的位置

2. 证据分类
   - 数据证据（统计数据、实验结果）
   - 文献引用（其他研究支持）
   - 案例证据（实际案例）
   - 逻辑推理（理论推导）

3. 证据强度评估
   - 强：直接、明确、可验证
   - 中：间接、需要推理
   - 弱：模糊、存在争议

4. 逻辑链条分析
   - 证据如何支撑论点
   - 推理过程是否严密
   - 是否存在逻辑跳跃

5. 潜在问题识别
   - 证据不足之处
   - 可能的反驳论点
   - 需要补充的证据

输出详细的证据链分析报告。"""
    ),
    
    # 交叉引用分析
    "cross_reference": PromptTemplate(
        input_variables=["document_content", "concept"],
        template="""执行跨章节的交叉引用分析。

目标概念：{concept}

文档内容：
{document_content}

分析任务：

1. 概念定位
   - 找出所有提到'{concept}'的段落
   - 记录每次出现的上下文

2. 表述对比
   - 比较不同位置的表述差异
   - 识别概念定义的演变

3. 关联分析
   - 该概念与其他概念的关联
   - 在不同章节中的作用

4. 一致性检查
   - 是否存在矛盾表述
   - 需要澄清的歧义

5. 概念图谱
   - 构建该概念的关系网络
   - 标注重要程度

输出结构化的交叉引用分析结果。"""
    ),
    
    # 批判性思维分析
    "critical_thinking": PromptTemplate(
        input_variables=["document_content", "analysis_focus"],
        template="""从批判性思维角度深度分析文档。

分析焦点：{analysis_focus}

文档内容：
{document_content}

请从以下视角进行分析：

1. 方法论审视
   - 研究方法是否科学严谨？
   - 样本选择是否合理充分？
   - 数据分析是否恰当？
   - 结论是否有充分支撑？

2. 假设检验
   - 识别显性假设（明确说明的）
   - 挖掘隐性假设（未言明的）
   - 评估假设的合理性
   - 假设变化对结论的影响

3. 利益相关者分析
   - 谁会从这个观点受益？
   - 谁的利益可能受损？
   - 是否存在利益冲突？
   - 潜在的偏见来源

4. 时代性和适用性
   - 在当前环境下的适用性
   - 可能过时的观点
   - 需要更新的内容

5. 替代视角
   - 其他学科会如何看待？
   - 是否存在反例？
   - 不同文化背景的解读

提供平衡、深入的批判性分析报告。"""
    )
}


# 知识整合模板
SYNTHESIS_TEMPLATE = PromptTemplate(
    input_variables=["artifacts", "synthesis_goal"],
    template="""基于多个分析结果进行知识整合。

整合目标：{synthesis_goal}

已有分析材料：
{artifacts}

请进行以下整合工作：

1. 信息汇总
   - 整合所有相关发现
   - 识别共同主题
   - 发现信息模式

2. 观点综合
   - 构建完整论述
   - 调和不同观点
   - 形成综合结论

3. 洞察提炼
   - 提取关键洞察
   - 识别创新点
   - 总结核心价值

4. 应用建议
   - 实践指导
   - 决策建议
   - 后续行动

5. 知识产品
   - 执行摘要
   - 详细报告
   - 可视化呈现

输出综合性的知识整合报告。"""
)


# 分析规划模板
ANALYSIS_PLANNER_TEMPLATE = PromptTemplate(
    input_variables=["document_content", "analysis_goal", "user_requirements", "time_budget", "cost_budget"],
    template="""你是一个专业的文档分析规划专家。你的任务是基于文档特征、用户目标和资源限制，制定最优的分析方案。

分析规划原则：
1. 高效性：在预算内最大化分析价值
2. 针对性：根据文档特征选择合适的分析方法
3. 渐进性：先快速了解，再深入分析
4. 实用性：确保分析结果对用户有实际价值

文档类别识别：
- academic_paper: 有摘要、引言、方法、结果、讨论、参考文献
- technical_report: 技术方案、系统设计、实施细节
- business_document: 商业计划、市场分析、财务报告
- news_article: 新闻报道、时事评论
- book_chapter: 书籍章节、教材内容
- general_text: 其他一般性文本

分析类型及其特点：
1. skim (5s, $0.01): 快速概览，适合初步了解
2. summary_level_X (5-30s, $0.01-0.08): 不同深度的摘要
3. knowledge_graph (10-30s, $0.03-0.10): 实体关系提取
4. outline (10-40s, $0.02-0.08): 多维度大纲提取
5. evidence_chain (20s, $0.05): 论证质量评估
6. cross_reference (20s, $0.05): 内部一致性检查
7. critical_thinking (25s, $0.06): 批判性分析

请根据输入制定详细的分析计划。"""
)


def get_prompt_template(template_name: str, **kwargs) -> PromptTemplate:
    """获取指定的提示词模板"""
    templates = {
        "skim": SKIM_PROMPT_TEMPLATE,
        "progressive_summary_level_1": PROGRESSIVE_SUMMARY_TEMPLATES["level_1"],
        "progressive_summary_level_2": PROGRESSIVE_SUMMARY_TEMPLATES["level_2"],
        "progressive_summary_level_3": PROGRESSIVE_SUMMARY_TEMPLATES["level_3"],
        "progressive_summary_level_4": PROGRESSIVE_SUMMARY_TEMPLATES["level_4"],
        "progressive_summary_level_5": PROGRESSIVE_SUMMARY_TEMPLATES["level_5"],
        "outline": MULTI_DIM_OUTLINE_TEMPLATE,
        "knowledge_graph": KNOWLEDGE_GRAPH_TEMPLATE,
        "planner": ANALYSIS_PLANNER_TEMPLATE,
        "evidence_chain": DEEP_ANALYSIS_TEMPLATES["evidence_chain"],
        "cross_reference": DEEP_ANALYSIS_TEMPLATES["cross_reference"],
        "critical_thinking": DEEP_ANALYSIS_TEMPLATES["critical_thinking"],
        "synthesis": SYNTHESIS_TEMPLATE
    }
    
    template = templates.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")
    
    return template