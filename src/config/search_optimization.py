"""
搜索优化配置
定义不同场景下的优化策略和参数
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class SearchScenario(str, Enum):
    """搜索场景"""
    FACTUAL = "factual"  # 事实查询
    CONCEPTUAL = "conceptual"  # 概念理解
    PROCEDURAL = "procedural"  # 步骤流程
    EXPLORATORY = "exploratory"  # 探索性查询
    COMPARISON = "comparison"  # 比较分析


@dataclass
class OptimizationProfile:
    """优化配置文件"""
    name: str
    description: str
    search_strategy: str  # dense, sparse, hybrid
    query_expansion: bool
    rerank_strategy: str  # similarity, relevance, hybrid
    cache_ttl: int  # 缓存时间（秒）
    retrieval_params: Dict[str, Any]


# 预定义的优化配置
OPTIMIZATION_PROFILES = {
    SearchScenario.FACTUAL: OptimizationProfile(
        name="事实查询优化",
        description="优化精确事实信息的检索",
        search_strategy="dense",
        query_expansion=False,
        rerank_strategy="similarity",
        cache_ttl=3600,  # 1小时
        retrieval_params={
            "top_k": 10,
            "score_threshold": 0.7,
            "use_mmr": False  # 不使用最大边际相关性
        }
    ),
    
    SearchScenario.CONCEPTUAL: OptimizationProfile(
        name="概念理解优化",
        description="优化概念和原理的深度理解",
        search_strategy="hybrid",
        query_expansion=True,
        rerank_strategy="hybrid",
        cache_ttl=7200,  # 2小时
        retrieval_params={
            "top_k": 15,
            "score_threshold": 0.6,
            "use_mmr": True,
            "diversity": 0.3
        }
    ),
    
    SearchScenario.PROCEDURAL: OptimizationProfile(
        name="流程步骤优化",
        description="优化步骤和流程信息的检索",
        search_strategy="hybrid",
        query_expansion=True,
        rerank_strategy="relevance",
        cache_ttl=1800,  # 30分钟
        retrieval_params={
            "top_k": 20,
            "score_threshold": 0.5,
            "sequence_aware": True  # 考虑顺序
        }
    ),
    
    SearchScenario.EXPLORATORY: OptimizationProfile(
        name="探索性查询优化",
        description="优化开放式探索性查询",
        search_strategy="hybrid",
        query_expansion=True,
        rerank_strategy="hybrid",
        cache_ttl=900,  # 15分钟
        retrieval_params={
            "top_k": 25,
            "score_threshold": 0.4,
            "use_mmr": True,
            "diversity": 0.5
        }
    ),
    
    SearchScenario.COMPARISON: OptimizationProfile(
        name="比较分析优化",
        description="优化多个实体的比较分析",
        search_strategy="dense",
        query_expansion=True,
        rerank_strategy="hybrid",
        cache_ttl=1800,
        retrieval_params={
            "top_k": 20,
            "score_threshold": 0.6,
            "entity_aware": True  # 实体感知
        }
    )
}


class QueryPreprocessor:
    """查询预处理器"""
    
    @staticmethod
    def preprocess(query: str) -> Dict[str, Any]:
        """预处理查询"""
        # 清理查询
        cleaned_query = query.strip()
        
        # 检测语言
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)
        
        # 提取时间信息
        import re
        time_patterns = [
            r'\d{4}年',
            r'\d{1,2}月',
            r'最新',
            r'最近',
            r'当前'
        ]
        
        has_time_constraint = any(
            re.search(pattern, query) 
            for pattern in time_patterns
        )
        
        return {
            "original": query,
            "cleaned": cleaned_query,
            "language": "zh" if is_chinese else "en",
            "has_time_constraint": has_time_constraint,
            "length": len(cleaned_query)
        }
    
    @staticmethod
    def detect_scenario(query: str) -> SearchScenario:
        """检测查询场景"""
        query_lower = query.lower()
        
        # 关键词映射
        scenario_keywords = {
            SearchScenario.FACTUAL: [
                "是什么", "有哪些", "多少", "何时", "谁", 
                "what is", "how many", "when", "who"
            ],
            SearchScenario.CONCEPTUAL: [
                "原理", "概念", "定义", "理论", "为什么",
                "principle", "concept", "definition", "theory", "why"
            ],
            SearchScenario.PROCEDURAL: [
                "如何", "怎么", "步骤", "流程", "方法",
                "how to", "steps", "process", "method"
            ],
            SearchScenario.COMPARISON: [
                "比较", "区别", "不同", "对比", "优缺点",
                "compare", "difference", "versus", "vs"
            ],
            SearchScenario.EXPLORATORY: [
                "探索", "了解", "研究", "分析", "应用",
                "explore", "understand", "research", "analyze"
            ]
        }
        
        # 计算每个场景的匹配分数
        scores = {}
        for scenario, keywords in scenario_keywords.items():
            score = sum(
                1 for keyword in keywords 
                if keyword in query_lower
            )
            scores[scenario] = score
        
        # 返回最高分的场景
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        # 默认为探索性查询
        return SearchScenario.EXPLORATORY


class SearchOptimizer:
    """搜索优化器"""
    
    def __init__(self):
        self.preprocessor = QueryPreprocessor()
    
    def get_optimization_config(
        self, 
        query: str,
        override_scenario: Optional[SearchScenario] = None
    ) -> Dict[str, Any]:
        """获取查询的优化配置"""
        # 预处理查询
        query_info = self.preprocessor.preprocess(query)
        
        # 检测或使用指定的场景
        scenario = override_scenario or self.preprocessor.detect_scenario(query)
        
        # 获取对应的优化配置
        profile = OPTIMIZATION_PROFILES[scenario]
        
        # 根据查询特征调整配置
        config = {
            "query_info": query_info,
            "scenario": scenario,
            "profile": profile,
            "adjustments": self._get_adjustments(query_info, profile)
        }
        
        return config
    
    def _get_adjustments(
        self, 
        query_info: Dict[str, Any], 
        profile: OptimizationProfile
    ) -> Dict[str, Any]:
        """根据查询特征调整配置"""
        adjustments = {}
        
        # 短查询可能需要更多扩展
        if query_info["length"] < 10:
            adjustments["boost_expansion"] = True
        
        # 有时间约束的查询需要时间过滤
        if query_info["has_time_constraint"]:
            adjustments["add_time_filter"] = True
            adjustments["reduce_cache_ttl"] = 0.5  # 减半缓存时间
        
        # 中文查询可能需要特殊处理
        if query_info["language"] == "zh":
            adjustments["use_jieba"] = True
        
        return adjustments


# 批量查询优化策略
class BatchOptimizationStrategy:
    """批量查询优化策略"""
    
    @staticmethod
    def group_queries(queries: List[str]) -> Dict[SearchScenario, List[str]]:
        """将查询按场景分组"""
        preprocessor = QueryPreprocessor()
        groups = {}
        
        for query in queries:
            scenario = preprocessor.detect_scenario(query)
            if scenario not in groups:
                groups[scenario] = []
            groups[scenario].append(query)
        
        return groups
    
    @staticmethod
    def optimize_batch_execution(
        grouped_queries: Dict[SearchScenario, List[str]]
    ) -> List[Dict[str, Any]]:
        """优化批量执行计划"""
        execution_plan = []
        
        # 按优先级排序场景
        priority_order = [
            SearchScenario.FACTUAL,  # 最快
            SearchScenario.COMPARISON,
            SearchScenario.CONCEPTUAL,
            SearchScenario.PROCEDURAL,
            SearchScenario.EXPLORATORY  # 最慢
        ]
        
        for scenario in priority_order:
            if scenario in grouped_queries:
                queries = grouped_queries[scenario]
                profile = OPTIMIZATION_PROFILES[scenario]
                
                execution_plan.append({
                    "scenario": scenario,
                    "queries": queries,
                    "batch_size": min(5, len(queries)),  # 批量大小
                    "profile": profile,
                    "parallel": scenario in [SearchScenario.FACTUAL, SearchScenario.COMPARISON]
                })
        
        return execution_plan


# 性能监控配置
PERFORMANCE_THRESHOLDS = {
    "query_latency_ms": {
        "excellent": 500,
        "good": 1000,
        "acceptable": 2000,
        "poor": 5000
    },
    "cache_hit_rate": {
        "excellent": 0.8,
        "good": 0.6,
        "acceptable": 0.4,
        "poor": 0.2
    },
    "relevance_score": {
        "excellent": 0.85,
        "good": 0.7,
        "acceptable": 0.5,
        "poor": 0.3
    }
}