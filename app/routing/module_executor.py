"""
Module Executor
Handles actual module execution with context management
"""

from typing import Dict, Any, Optional
import time

from app.modules.base import BaseModule, ModuleResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModuleExecutor:
    """
    Executes modules with proper context and error handling
    """
    
    def __init__(self):
        """Initialize module executor"""
        self.execution_context: Dict[str, Any] = {}
        logger.debug("ModuleExecutor initialized")
    
    async def execute_module(
        self,
        module: BaseModule,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute a module with given parameters
        
        Args:
            module: Module to execute
            parameters: Execution parameters
            context: Optional execution context
            
        Returns:
            ModuleResult: Execution result
        """
        logger.info(f"🔧 Executing module: {module.name}")
        logger.debug(f"Parameters: {list(parameters.keys())}")
        
        start_time = time.time()
        
        try:
            # Initialize module if needed
            if not module.is_initialized():
                logger.debug(f"Initializing module: {module.name}")
                await module.initialize()
            
            # Merge context
            full_context = {**self.execution_context, **(context or {})}
            
            # Execute
            result = await module.execute(parameters, full_context)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # Update context with result data
            if result.success and result.data is not None:
                self.execution_context[f"{module.name}_result"] = result.data
                self.execution_context["last_result"] = result.data
            
            logger.info(
                f"✅ Module completed: {module.name} "
                f"(success={result.success}, time={execution_time:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Module execution failed: {module.name} - {str(e)}", exc_info=True)
            
            return ModuleResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def get_context(self) -> Dict[str, Any]:
        """Get current execution context"""
        return self.execution_context.copy()
    
    def set_context(self, key: str, value: Any):
        """Set context value"""
        self.execution_context[key] = value
    
    def clear_context(self):
        """Clear execution context"""
        self.execution_context.clear()
        logger.debug("Execution context cleared")
