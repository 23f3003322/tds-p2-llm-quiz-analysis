"""
Visualization Utilities
Helper functions for chart creation
"""

from typing import List, Dict, Any
import base64
from io import BytesIO

from app.core.logging import get_logger

logger = get_logger(__name__)


def generate_chart_base64(fig) -> str:
    """
    Convert matplotlib/plotly figure to base64
    
    Args:
        fig: Matplotlib or Plotly figure
        
    Returns:
        Base64 encoded string
    """
    try:
        # For matplotlib
        if hasattr(fig, 'savefig'):
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            return img_base64
        
        # For plotly
        elif hasattr(fig, 'to_image'):
            img_bytes = fig.to_image(format='png')
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return img_base64
        
    except Exception as e:
        logger.error(f"Failed to generate base64: {e}")
        return ""


def extract_chart_data(
    data: List[Dict[str, Any]],
    x_column: str,
    y_column: str
) -> tuple[List, List]:
    """
    Extract X and Y data from records
    
    Args:
        data: List of records
        x_column: Column for X axis
        y_column: Column for Y axis
        
    Returns:
        Tuple of (x_values, y_values)
    """
    x_values = []
    y_values = []
    
    for record in data:
        if x_column in record and y_column in record:
            x_values.append(record[x_column])
            y_values.append(record[y_column])
    
    return x_values, y_values


def get_chart_color_scheme(chart_type: str) -> List[str]:
    """Get appropriate color scheme for chart type"""
    
    schemes = {
        'bar': ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'],
        'line': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12'],
        'pie': ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c'],
        'scatter': ['#3498db'],
        'histogram': ['#2ecc71'],
        'heatmap': ['#d7191c', '#fdae61', '#ffffbf', '#abd9e9', '#2c7bb6']
    }
    
    return schemes.get(chart_type, ['#3498db'])
