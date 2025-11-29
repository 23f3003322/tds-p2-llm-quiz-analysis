"""
Answer Submitter Module
Sends POST requests to TDS quiz submission endpoints
Handles chained quiz responses automatically
"""

import httpx
import json
from typing import Dict, Any, Optional, List
from app.modules.base import BaseModule, ModuleResult, ModuleType
# from app.modules import OutputCapability  # For export capabilities
from app.core.logging import get_logger


logger = get_logger(__name__)


class AnswerSubmitter(BaseModule):
    """Submits answers to TDS quizzes and handles chained responses"""
    
    def __init__(self):
        super().__init__(name="answer_submitter", module_type=ModuleType.EXPORTER)
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        # self.capabilities = OutputCapability.CSV_EXPORTER  # Reuse for HTTP export
        
    def get_capabilities(self):
        """Custom capabilities for answer submission"""
        from app.modules.base import ModuleCapability
        return ModuleCapability(
            can_export_csv=True,
            can_export_json=True,
            supported_input_formats={'dict', 'json'},
            supported_output_formats={'http', 'json'},
            estimated_speed="fast",
            memory_usage="low"
        )
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """Submit answer to TDS quiz endpoint"""
        try:
            submission_url = parameters.get('submission_url')
            email = parameters.get('email')
            secret = parameters.get('secret') or parameters.get('answer')
            quiz_url = parameters.get('quiz_url') or parameters.get('url')
            answer = parameters.get('answer', secret)
            
            if not submission_url:
                return ModuleResult(
                    success=False,
                    error="No submission_url provided",
                    warnings=["Missing required submission_url"]
                )
            
            logger.info(f"📤 Submitting answer to {submission_url}")
            logger.info(f"   Email: {email}")
            logger.info(f"   Secret/Answer: {secret or 'None'}")
            
            # Prepare payload
            payload = {
                "email": email,
                "secret": secret,
                "url": quiz_url,
                "answer": answer
            }
            
            # Send POST request
            response = await self.client.post(submission_url, json=payload)
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            is_correct = response_data.get('correct', False)
            next_url = response_data.get('url')
            reason = response_data.get('reason')
            
            logger.info(f"✅ Submission response: {'CORRECT' if is_correct else 'INCORRECT'}")
            if reason:
                logger.info(f"   Reason: {reason}")
            
            result_data = {
                'success': True,
                'correct': is_correct,
                'response': response_data,
                'submitted_payload': payload
            }
            
            # Chain next quiz if URL provided
            if next_url and is_correct:
                logger.info(f"🔄 Next quiz detected: {next_url}")
                result_data['next_quiz_url'] = next_url
                result_data['chain'] = True
            
            return ModuleResult(
                success=True,
                data=result_data,
                metadata={'status_code': response.status_code, 'next_url': next_url}
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error submitting answer: {e}")
            return ModuleResult(
                success=False,
                error=f"HTTP submission failed: {str(e)}",
                data={'attempted_payload': payload if 'payload' in locals() else None}
            )
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from server")
            return ModuleResult(
                success=False,
                error="Server returned invalid JSON",
                data={'raw_response': response.text if 'response' in locals() else None}
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return ModuleResult(
                success=False,
                error=f"Submission failed: {str(e)}"
            )
    
    async def initialize(self) -> bool:
        """Initialize HTTP client"""
        await super().initialize()
        logger.info("AnswerSubmitter ready")
        return True
    
    async def cleanup(self):
        """Close HTTP client"""
        await self.client.aclose()
        await super().cleanup()
        logger.info("AnswerSubmitter cleaned up")
