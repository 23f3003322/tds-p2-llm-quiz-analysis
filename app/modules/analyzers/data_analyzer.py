"""
Data Analyzer - UPDATED
Dynamic LLM-driven analysis that handles any analytical question
"""

from typing import Dict, Any, Optional, List
import time

from app.modules.analyzers.base_analyzer import BaseAnalyzer, AnalysisResult
from app.modules.analyzers.analysis_planner import AnalysisPlanner
from app.modules.analyzers.statistical_analyzer import StatisticalAnalyzer
from app.modules.analyzers.insight_generator import InsightGenerator
from app.modules.base import ModuleCapability, ModuleResult
from app.modules.capabilities import ProcessingCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataAnalyzer(BaseAnalyzer):
    """
    Complete dynamic data analyzer
    Uses LLM to plan analysis, statistics to calculate, LLM to interpret
    """
    
    def __init__(self):
        super().__init__(name="data_analyzer")
        self.planner = AnalysisPlanner()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.insight_generator = InsightGenerator()
        logger.debug("DataAnalyzer initialized (dynamic mode)")
    
    def get_capabilities(self) -> ModuleCapability:
        """Get module capabilities"""
        return ProcessingCapability.TRANSFORM
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute data analysis
        
        Args:
            parameters: Analysis parameters
                - data: Data to analyze (required)
                - question: User's analytical question (optional but recommended)
                - columns: Specific columns (optional)
                - generate_insights: Use LLM for insights (default: True)
                - context: Domain context
            context: Execution context
            
        Returns:
            ModuleResult: Analysis result
        """
        data = parameters.get('data')
        
        if not data:
            return ModuleResult(
                success=False,
                error="Data parameter is required"
            )
        
        logger.info("[DATA ANALYZER] Starting dynamic analysis")
        
        start_time = time.time()
        
        # Check if user has a specific question
        user_question = parameters.get('question')
        
        if user_question:
            # Dynamic question-driven analysis
            result = await self.analyze_with_question(
                data=data,
                user_question=user_question,
                context=parameters.get('context', {})
            )
        else:
            # General comprehensive analysis
            result = await self.analyze(
                data=data,
                options={
                    'columns': parameters.get('columns'),
                    'correlations': parameters.get('correlations', []),
                    'detect_outliers': parameters.get('detect_outliers', True),
                    'generate_insights': parameters.get('generate_insights', True),
                    'context': parameters.get('context', {})
                }
            )
        
        execution_time = time.time() - start_time
        
        if result.success:
            return ModuleResult(
                success=True,
                data={
                    'statistics': result.statistics,
                    'insights': result.insights,
                    'analysis_type': result.analysis_type
                },
                metadata={
                    'rows_analyzed': result.rows_analyzed,
                    'has_insights': bool(result.insights),
                    'question_driven': bool(user_question)
                },
                execution_time=execution_time
            )
        else:
            return ModuleResult(
                success=False,
                error=result.error,
                execution_time=execution_time
            )
    
    async def analyze_with_question(
        self,
        data: List[Dict[str, Any]],
        user_question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Analyze data to answer specific user question
        Dynamic and flexible - handles any analytical question
        
        Args:
            data: Data to analyze
            user_question: User's analytical question
            context: Additional context
            
        Returns:
            AnalysisResult with question-specific insights
        """
        logger.info(f"Question-driven analysis: '{user_question}'")
        
        # Phase 1: LLM plans what analysis to perform
        logger.debug("Phase 1: Planning analysis strategy")
        plan = await self.planner.plan_analysis(user_question, data, context)
        
        logger.info(f"Analysis plan: {plan.get('primary_focus', 'comprehensive')}")
        
        # Phase 2: Execute statistical analysis based on plan
        logger.debug("Phase 2: Executing statistical analysis")
        options = self._plan_to_options(plan, data)
        stat_result = await self.statistical_analyzer.analyze(data, options)
        
        if not stat_result.success:
            return stat_result
        
        # Phase 3: LLM generates question-specific insights
        logger.debug("Phase 3: Generating insights")
        insights = await self.insight_generator.generate_question_specific_insights(
            question=user_question,
            statistics=stat_result.statistics,
            plan=plan,
            context=context
        )
        
        logger.info("✓ Question-driven analysis complete")
        
        return AnalysisResult(
            success=True,
            statistics=stat_result.statistics,
            insights=insights,
            rows_analyzed=len(data),
            analysis_type="question_driven"
        )
    
    async def analyze(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        General comprehensive analysis
        
        Args:
            data: Data to analyze
            options: Analysis options
            
        Returns:
            AnalysisResult
        """
        options = options or {}
        
        logger.info(f"General analysis of {len(data) if isinstance(data, list) else '?'} records")
        
        # Statistical analysis
        stat_result = await self.statistical_analyzer.analyze(data, options)
        
        if not stat_result.success:
            return stat_result
        
        # Generate general insights
        insights = {}
        
        if options.get('generate_insights', True):
            try:
                insights = await self.insight_generator.generate_insights(
                    statistics=stat_result.statistics,
                    context=options.get('context', {})
                )
            except Exception as e:
                logger.error(f"Insight generation failed: {e}")
        
        return AnalysisResult(
            success=True,
            statistics=stat_result.statistics,
            insights=insights,
            rows_analyzed=stat_result.rows_analyzed,
            analysis_type="comprehensive"
        )
    
    def _plan_to_options(
        self,
        plan: Dict[str, Any],
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Convert LLM analysis plan to statistical analyzer options
        
        Args:
            plan: LLM-generated analysis plan
            data: Data being analyzed
            
        Returns:
            Options for statistical analyzer
        """
        options = {}
        
        # Columns to analyze
        if 'columns_to_analyze' in plan and plan['columns_to_analyze']:
            options['columns'] = plan['columns_to_analyze']
        
        # Correlations
        if 'correlations' in plan and plan['correlations']:
            options['correlations'] = [tuple(pair) for pair in plan['correlations']]
        
        # Segmentation
        if plan.get('segment_by'):
            options['segment_by'] = plan['segment_by']
            options['segment_metric'] = plan.get('segment_metric')
        
        # Trends
        if plan.get('trend_column'):
            options['trend_column'] = plan['trend_column']
        
        # Outliers
        if plan.get('detect_outliers'):
            options['detect_outliers'] = True
            if plan.get('outlier_columns'):
                options['columns'] = plan['outlier_columns']
        
        return options
