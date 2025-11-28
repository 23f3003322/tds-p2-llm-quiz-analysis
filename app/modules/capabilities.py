"""
Module Capability Definitions
Pre-defined capability sets for different module types
"""

from app.modules.base import ModuleCapability


class ScrapingCapability:
    """Capability definitions for scraping modules"""
    
    STATIC = ModuleCapability(
        can_scrape_static=True,
        can_scrape_dynamic=False,
        can_handle_javascript=False,
        can_authenticate=False,
        supported_input_formats={'html', 'xml'},
        supported_output_formats={'json', 'csv', 'dict'},
        max_concurrent_requests=5,
        estimated_speed="fast",
        memory_usage="low",
        requires_browser=False
    )
    
    DYNAMIC = ModuleCapability(
        can_scrape_static=True,
        can_scrape_dynamic=True,
        can_handle_javascript=True,
        can_authenticate=True,
        supported_input_formats={'html', 'javascript'},
        supported_output_formats={'json', 'csv', 'dict'},
        max_concurrent_requests=2,
        estimated_speed="medium",
        memory_usage="high",
        requires_browser=True
    )
    
    API_CLIENT = ModuleCapability(
        can_handle_api=True,
        supported_input_formats={'api', 'rest', 'graphql'},
        supported_output_formats={'json', 'dict'},
        max_concurrent_requests=10,
        estimated_speed="fast",
        memory_usage="low",
        requires_api_key=True
    )


class ProcessingCapability:
    """Capability definitions for data processing modules"""
    
    DATA_CLEANER = ModuleCapability(
        can_process_data=True,
        can_clean_data=True,
        supported_input_formats={'csv', 'json', 'dict', 'dataframe'},
        supported_output_formats={'csv', 'json', 'dict', 'dataframe'},
        max_concurrent_requests=1,
        estimated_speed="fast",
        memory_usage="medium"
    )
    
    DATA_TRANSFORMER = ModuleCapability(
        can_process_data=True,
        can_transform_data=True,
        can_aggregate=True,
        can_filter=True,
        can_sort=True,
        supported_input_formats={'csv', 'json', 'dict', 'dataframe'},
        supported_output_formats={'csv', 'json', 'dict', 'dataframe'},
        max_concurrent_requests=1,
        estimated_speed="medium",
        memory_usage="medium"
    )


class VisualizationCapability:
    """Capability definitions for visualization modules"""
    
    CHART_CREATOR = ModuleCapability(
        can_visualize=True,
        can_create_charts=True,
        supported_input_formats={'csv', 'json', 'dict', 'dataframe'},
        supported_output_formats={'png', 'jpg', 'svg', 'html'},
        max_concurrent_requests=1,
        estimated_speed="medium",
        memory_usage="medium"
    )
    
    MAP_CREATOR = ModuleCapability(
        can_visualize=True,
        can_create_maps=True,
        supported_input_formats={'csv', 'json', 'dict', 'geojson'},
        supported_output_formats={'html', 'png'},
        max_concurrent_requests=1,
        estimated_speed="slow",
        memory_usage="high"
    )


class OutputCapability:
    """Capability definitions for output/export modules"""
    
    CSV_EXPORTER = ModuleCapability(
        can_export_csv=True,
        supported_input_formats={'dict', 'list', 'dataframe'},
        supported_output_formats={'csv'},
        max_concurrent_requests=1,
        estimated_speed="fast",
        memory_usage="low"
    )
    
    EXCEL_EXPORTER = ModuleCapability(
        can_export_excel=True,
        supported_input_formats={'dict', 'list', 'dataframe'},
        supported_output_formats={'xlsx', 'xls'},
        max_concurrent_requests=1,
        estimated_speed="medium",
        memory_usage="medium"
    )
    
    JSON_EXPORTER = ModuleCapability(
        can_export_json=True,
        supported_input_formats={'dict', 'list', 'dataframe'},
        supported_output_formats={'json'},
        max_concurrent_requests=1,
        estimated_speed="fast",
        memory_usage="low"
    )
