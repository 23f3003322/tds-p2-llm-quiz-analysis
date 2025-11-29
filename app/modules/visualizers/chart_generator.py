"""
Chart Generator
Creates actual charts using matplotlib
"""

from typing import Dict, Any, Optional, List
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import time

from app.modules.visualizers.base_visualizer import BaseVisualizer, VisualizationResult
from app.modules.visualizers.chart_detector import ChartDetector
from app.modules.visualizers.visualization_utils import (
    generate_chart_base64,
    extract_chart_data,
    get_chart_color_scheme
)
from app.modules.base import ModuleCapability, ModuleResult
from app.modules.capabilities import VisualizationCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChartGenerator(BaseVisualizer):
    """
    Chart generator for quiz answers
    Only creates charts when explicitly requested
    """
    
    def __init__(self):
        super().__init__(name="chart_generator")
        self.detector = ChartDetector()
        logger.debug("ChartGenerator initialized")
    
    def get_capabilities(self) -> ModuleCapability:
        """Get module capabilities"""
        return VisualizationCapability.CHART
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute chart generation
        
        Args:
            parameters: Chart parameters
                - question: User's question (to detect if chart needed)
                - data: Data to visualize
                - chart_type: Chart type (optional, auto-detected)
                - x_column: X axis column
                - y_column: Y axis column
                - title: Chart title
            context: Execution context
            
        Returns:
            ModuleResult: Chart result
        """
        question = parameters.get('question', '')
        data = parameters.get('data')
        
        if not data:
            return ModuleResult(
                success=False,
                error="Data parameter is required"
            )
        
        logger.info("[CHART GENERATOR] Processing request")
        
        start_time = time.time()
        
        # Detect if chart is needed
        data_summary = {
            'columns': list(data[0].keys()) if data else [],
            'rows': len(data)
        }
        
        requirement = await self.detector.detect_chart_requirement(question, data_summary)
        
        if not requirement['requires_chart']:
            # No chart needed
            return ModuleResult(
                success=True,
                data={'chart_created': False},
                metadata={'requires_chart': False},
                execution_time=time.time() - start_time
            )
        
        # Create chart
        result = await self.visualize(
            data=data,
            options={
                'chart_type': parameters.get('chart_type') or requirement['chart_type'],
                'x_column': parameters.get('x_column') or requirement['x_axis'],
                'y_column': parameters.get('y_column') or requirement['y_axis'],
                'title': parameters.get('title') or requirement['title']
            }
        )
        
        execution_time = time.time() - start_time
        
        if result.success:
            return ModuleResult(
                success=True,
                data={
                    'chart_created': True,
                    'chart_type': result.chart_type,
                    'chart_base64': result.chart_base64,
                    'title': result.title
                },
                metadata={
                    'requires_chart': True,
                    'chart_type': result.chart_type
                },
                execution_time=execution_time
            )
        else:
            return ModuleResult(
                success=False,
                error=result.error,
                execution_time=execution_time
            )
    
    async def visualize(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> VisualizationResult:
        """
        Create visualization
        
        Args:
            data: Data to visualize (list of dicts)
            options: Visualization options
                - chart_type: Type of chart
                - x_column: X axis column
                - y_column: Y axis column
                - title: Chart title
            
        Returns:
            VisualizationResult
        """
        options = options or {}
        
        chart_type = options.get('chart_type', 'bar')
        x_column = options.get('x_column')
        y_column = options.get('y_column')
        title = options.get('title', 'Chart')
        
        if not x_column or not y_column:
            return VisualizationResult(
                success=False,
                error="x_column and y_column are required"
            )
        
        logger.info(f"Creating {chart_type} chart: {x_column} vs {y_column}")
        
        try:
            # Extract data
            x_values, y_values = extract_chart_data(data, x_column, y_column)
            
            if not x_values or not y_values:
                return VisualizationResult(
                    success=False,
                    error=f"No data found for columns: {x_column}, {y_column}"
                )
            
            # Create chart
            fig = self._create_chart(
                chart_type=chart_type,
                x_values=x_values,
                y_values=y_values,
                title=title,
                x_label=x_column,
                y_label=y_column
            )
            
            # Convert to base64
            chart_base64 = generate_chart_base64(fig)
            
            # Clean up
            plt.close(fig)
            
            logger.info(f"✓ Chart created: {chart_type}")
            
            return VisualizationResult(
                success=True,
                chart_created=True,
                chart_type=chart_type,
                chart_base64=chart_base64,
                title=title
            )
            
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            return VisualizationResult(
                success=False,
                error=str(e)
            )
    
    def _create_chart(
        self,
        chart_type: str,
        x_values: List,
        y_values: List,
        title: str,
        x_label: str,
        y_label: str
    ):
        """Create matplotlib chart"""
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Get colors
        colors = get_chart_color_scheme(chart_type)
        
        # Create chart based on type
        if chart_type == 'bar':
            ax.bar(x_values, y_values, color=colors[0])
        
        elif chart_type == 'line':
            ax.plot(x_values, y_values, color=colors[0], marker='o', linewidth=2)
        
        elif chart_type == 'scatter':
            ax.scatter(x_values, y_values, color=colors[0], s=100, alpha=0.6)
        
        elif chart_type == 'pie':
            ax.pie(y_values, labels=x_values, colors=colors, autopct='%1.1f%%')
            ax.axis('equal')
        
        elif chart_type == 'histogram':
            ax.hist(y_values, bins=20, color=colors[0], edgecolor='black')
        
        else:
            # Default to bar chart
            ax.bar(x_values, y_values, color=colors[0])
        
        # Set labels and title
        if chart_type != 'pie':
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Grid for readability
        if chart_type in ['bar', 'line', 'scatter']:
            ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        return fig
