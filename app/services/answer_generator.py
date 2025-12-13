from typing import Dict, Any, List, Optional
import json
import re
from app.core.logging import get_logger
from app.core.exceptions import AnswerGenerationError
from app.models.answer import AnswerResult
from app.models.analysis import QuestionAnalysis
from app.services.audio_processor import AudioProcessor
logger = get_logger(__name__)


class AnswerGenerator:
    """
    Generates answers based on question analysis.
    Uses LLM with rich context for flexibility with unknown questions.
    """
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM client with run_agent() method
        """
        self.llm_client = llm_client
        self._generator_agent = None
        self.audio_processor = AudioProcessor() 
    
    async def initialize(self):
        """Initialize LLM agent for answer generation"""
        self._generator_agent = self.llm_client.create_agent(
            output_type=AnswerResult,
            system_prompt=(
                "You are an expert at solving technical quiz questions. "
                "Generate precise, exact answers based on the provided analysis and context. "
                "Follow all constraints strictly. "
                "Be thorough in your reasoning to ensure correctness."
            ),
            retries=2
        )
        logger.info("✓ Answer generator initialized")
    
    async def generate(
        self,
        analysis: 'QuestionAnalysis',
        question_metadata: Dict[str, Any],
        base_url: str,
        user_email: str,
        downloaded_files: List[Dict[str, Any]]
    ) -> str:
        """
        Generate answer based on question analysis.
        
        Args:
            analysis: Question analysis from analyzer
            question_metadata: Original metadata with instructions
            base_url: Base URL for the quiz
            user_email: User's email address
            downloaded_files: List of downloaded files with local_path
        
        Returns:
            str: Final answer ready to submit
        
        Raises:
            AnswerGenerationError: If generation fails
        """
        logger.info(f"💡 Generating answer for {analysis.question_type}...")
        
        try:
            if analysis.question_type == 'audio_transcription':
                logger.info("🎤 Audio transcription task detected")
                
                # Find audio file
                audio_file = next(
                    (f for f in downloaded_files 
                     if f['type'] in ['.opus', '.mp3', '.wav', '.m4a', '.ogg']),
                    None
                )
                
                if not audio_file:
                    raise AnswerGenerationError(
                        "Audio file not found. Expected .opus, .mp3, or .wav file."
                    )
                
                logger.info(f"  Found audio file: {audio_file['filename']}")
                
                # Transcribe audio
                answer = await self.audio_processor.transcribe_audio(
                    audio_file_path=audio_file['local_path'],
                    language='en',  # English for Q5
                    lowercase=True  # Q5 requires lowercase
                )
                
                logger.info(f"✓ Audio transcribed successfully")
                logger.info(f"  Answer: {answer}")
                
                return answer
            
            # Step 1: Build comprehensive context for LLM
            context = self._build_generation_context(
                analysis=analysis,
                question_metadata=question_metadata,
                base_url=base_url,
                user_email=user_email,
                downloaded_files=downloaded_files
            )
            
            # Step 2: Generate answer with LLM
            result = await self._generate_with_llm(context)
            
            logger.info(f"✓ Generated answer (confidence: {result.confidence:.2f})")
            logger.debug(f"Reasoning: {result.reasoning}")
            
            # Step 3: Apply personalization if needed
            if analysis.requires_personalization and not result.personalization_applied:
                logger.info("Applying personalization...")
                result.answer = self._apply_personalization(
                    answer=result.answer,
                    analysis=analysis,
                    user_email=user_email
                )
                result.personalization_applied = True
            
            # Step 4: Validate format
            is_valid, validation_message = self._validate_format(
                result.answer,
                analysis
            )
            
            if not is_valid:
                logger.warning(f"Format validation issue: {validation_message}")
                # Try to auto-correct common issues
                result.answer = self._auto_correct_format(
                    result.answer,
                    analysis,
                    validation_message
                )
                logger.info("Applied auto-correction")
            
            # Step 5: Check constraints
            constraints_met, violations = self._check_constraints(
                result.answer,
                analysis
            )
            
            if not constraints_met:
                logger.warning(f"Constraint violations: {violations}")
                if result.confidence < 0.8:
                    raise AnswerGenerationError(
                        f"Low confidence ({result.confidence}) with constraint violations: {violations}"
                    )
            
            logger.info(f"✓ Final answer: {result.answer[:100]}...")
            
            return result.answer
            
        except Exception as e:
            logger.error(f"❌ Answer generation failed: {e}", exc_info=True)
            raise AnswerGenerationError(f"Failed to generate answer: {str(e)}")
    
    def _build_generation_context(
        self,
        analysis: 'QuestionAnalysis',
        question_metadata: Dict[str, Any],
        base_url: str,
        user_email: str,
        downloaded_files: List[Dict[str, Any]]
    ) -> str:
        """
        Build comprehensive context prompt for LLM.
        
        Returns:
            str: Rich context prompt
        """
        # Format instructions
        instructions_text = "\n".join(
            f"{i+1}. {inst}"
            for i, inst in enumerate(question_metadata.get('instructions', []))
        )
        
        # Format key components
        components_text = json.dumps(analysis.key_components, indent=2)
        
        # Format constraints
        constraints_text = "\n".join(
            f"- {constraint}"
            for constraint in analysis.critical_constraints
        ) if analysis.critical_constraints else "None specified"
        
        # Format files
        files_text = "\n".join(
            f"- {f['filename']} (type: {f['type']}, path: {f['local_path']})"
            for f in downloaded_files
        ) if downloaded_files else "None"
        
        # Build personalization info
        personalization_text = "Not required"
        if analysis.requires_personalization:
            personalization_text = f"""
Required: Yes
Type: {analysis.personalization_type}
Details: {analysis.personalization_details}
User Email: {user_email}
Email Length: {len(user_email)}
"""
        
        # Build complete prompt
        prompt = f"""Generate the exact answer for this technical quiz question.

# QUESTION METADATA
- Title: {question_metadata.get('title', 'Unknown')}
- Difficulty: {question_metadata.get('difficulty', 'Unknown')}/5
- Question Type: {analysis.question_type}
- Answer Format: {analysis.answer_format}

# ORIGINAL INSTRUCTIONS
{instructions_text}

# EXTRACTED COMPONENTS
The following components were extracted from the instructions:
{components_text}

# USER CONTEXT
- Base URL: {base_url}
- User Email: {user_email}

# PERSONALIZATION
{personalization_text}

# AVAILABLE FILES
{files_text}

# CRITICAL CONSTRAINTS
{constraints_text}

# ANSWER FORMAT REQUIREMENTS
Format: {analysis.answer_format}

"""
        
        # Add format-specific guidance
        if analysis.answer_format == 'plain_string':
            prompt += """
Return PLAIN TEXT ONLY:
- No JSON wrapping
- No quotes around the answer
- No extra formatting
- Just the raw string
"""
        elif analysis.answer_format == 'json_object':
            prompt += """
Return VALID JSON OBJECT:
- Must be a dictionary {{"key": "value"}}
- Properly escaped quotes
- Valid JSON syntax
"""
        elif analysis.answer_format == 'json_array':
            prompt += """
Return VALID JSON ARRAY:
- Must be a list ["item1", "item2"]
- Properly formatted
- Valid JSON syntax
"""
        elif analysis.answer_format == 'number':
            prompt += """
Return NUMBER ONLY:
- Just the numeric value
- No units or extra text
- Integer or float as appropriate
"""
        elif analysis.answer_format == 'single_letter':
            prompt += """
Return SINGLE LETTER:
- Just one character (A, B, C, etc.)
- No explanation or extra text
"""
        
        # Add question-type specific guidance
        if analysis.question_type == 'cli_command':
            prompt += """

# COMMAND GENERATION GUIDANCE
- Assemble command from components in correct order
- Use exact formatting for flags and arguments
- Pay attention to quote style (single vs double)
- Include all required parts (tool, subcommand, arguments, flags)
- Do NOT include shell prompt ($, >, #)
- Return the COMMAND STRING itself, not its output
"""
        elif analysis.question_type == 'file_path':
            prompt += """

# FILE PATH GUIDANCE
- Return the exact path as specified
- No markdown formatting []()
- No HTML tags
- No quotes unless specifically required
- Exact string match is critical
"""
        
        prompt += """

# YOUR TASK
Generate the EXACT answer that should be submitted based on all the information above.

IMPORTANT:
1. Use the extracted components to build the answer
2. Replace any placeholders with actual values (base_url, user_email)
3. Follow ALL critical constraints precisely
4. Match the required answer format exactly
5. Provide detailed reasoning for your answer

Generate the answer now.
"""
        
        return prompt
    
    async def _generate_with_llm(self, context: str) -> AnswerResult:
        """
        Call LLM to generate answer.
        
        Args:
            context: Rich context prompt
        
        Returns:
            AnswerResult: Structured answer with reasoning
        """
        try:
            result: AnswerResult = await self.llm_client.run_agent(
                self._generator_agent,
                context
            )
            return result
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise AnswerGenerationError(f"LLM generation failed: {str(e)}")
    
    def _apply_personalization(
        self,
        answer: str,
        analysis: 'QuestionAnalysis',
        user_email: str
    ) -> str:
        """
        Apply email-based personalization to answer.
        
        Args:
            answer: Base answer from LLM
            analysis: Question analysis
            user_email: User's email
        
        Returns:
            str: Personalized answer
        """
        if not analysis.requires_personalization:
            return answer
        
        email_length = len(user_email)
        
        if analysis.personalization_type == 'email_length_offset':
            # Parse offset formula from personalization_details
            # Example: "Add (len(email) mod 5) to base sum"
            
            match = re.search(r'mod\s+(\d+)', analysis.personalization_details or '')
            if match:
                mod_value = int(match.group(1))
                offset = email_length % mod_value
                
                # Try to parse answer as number and add offset
                try:
                    base_value = float(answer)
                    final_value = base_value + offset
                    
                    # Return as int if it's a whole number
                    if final_value.is_integer():
                        return str(int(final_value))
                    return str(final_value)
                    
                except ValueError:
                    logger.warning(f"Cannot apply offset to non-numeric answer: {answer}")
                    return answer
        
        elif analysis.personalization_type == 'email_length_conditional':
            # Example: If even, use option A; if odd, use option B
            # This should already be handled by LLM based on email_length in context
            pass
        
        return answer
    
    def _validate_format(
        self,
        answer: str,
        analysis: 'QuestionAnalysis'
    ) -> tuple[bool, str]:
        """
        Validate answer matches expected format.
        
        Returns:
            tuple: (is_valid, message)
        """
        answer_format = analysis.answer_format
        
        if answer_format == 'plain_string':
            # Should not be JSON
            if answer.strip().startswith(('{', '[')):
                return False, "Should be plain string, not JSON"
            return True, "Valid plain string"
        
        elif answer_format == 'json_object':
            try:
                parsed = json.loads(answer)
                if not isinstance(parsed, dict):
                    return False, "Should be JSON object (dict), not array"
                return True, "Valid JSON object"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON: {str(e)}"
        
        elif answer_format == 'json_array':
            try:
                parsed = json.loads(answer)
                if not isinstance(parsed, list):
                    return False, "Should be JSON array (list), not object"
                return True, "Valid JSON array"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON: {str(e)}"
        
        elif answer_format == 'number':
            try:
                float(answer.strip())
                return True, "Valid number"
            except ValueError:
                return False, "Should be a numeric value"
        
        elif answer_format == 'single_letter':
            if len(answer.strip()) == 1 and answer.strip().isalpha():
                return True, "Valid single letter"
            return False, "Should be exactly one letter"
        
        return True, "Format not strictly validated"
    
    def _check_constraints(
        self,
        answer: str,
        analysis: 'QuestionAnalysis'
    ) -> tuple[bool, List[str]]:
        """
        Check answer against critical constraints.
        
        Returns:
            tuple: (all_met, violations_list)
        """
        violations = []
        
        for constraint in analysis.critical_constraints:
            constraint_lower = constraint.lower()
            
            # Check: "command string not output"
            if 'command string' in constraint_lower and 'not output' in constraint_lower:
                if answer.startswith(('$', '>', '#', 'Output:', 'Result:')):
                    violations.append("Answer looks like output/prompt, should be command only")
            
            # Check: "no markdown formatting"
            if 'no markdown' in constraint_lower or 'no formatting' in constraint_lower:
                if re.search(r'\[.+\]\(.+\)', answer):
                    violations.append("Should not have markdown links []() formatting")
            
            # Check: "double quotes"
            if 'double quote' in constraint_lower:
                if "'" in answer and '"' not in answer:
                    violations.append("Should use double quotes, not single quotes")
            
            # Check: "exact string"
            if 'exact string' in constraint_lower:
                # Can't validate without knowing expected value
                pass
            
            # Check: "lowercase"
            if 'lowercase' in constraint_lower:
                if answer != answer.lower():
                    violations.append("Should be lowercase")
            
            # Check: "no quotes" or "plain path"
            if 'no quotes' in constraint_lower or 'plain' in constraint_lower:
                if answer.startswith(('"', "'")) and answer.endswith(('"', "'")):
                    violations.append("Should not be wrapped in quotes")
        
        return len(violations) == 0, violations
    
    def _auto_correct_format(
        self,
        answer: str,
        analysis: 'QuestionAnalysis',
        validation_message: str
    ) -> str:
        """
        Attempt to auto-correct common format issues.
        
        Args:
            answer: Original answer
            analysis: Question analysis
            validation_message: What was wrong
        
        Returns:
            str: Corrected answer
        """
        corrected = answer
        
        # Remove JSON wrapping if should be plain string
        if analysis.answer_format == 'plain_string':
            if corrected.startswith('"') and corrected.endswith('"'):
                corrected = corrected[1:-1]
            if corrected.startswith("'") and corrected.endswith("'"):
                corrected = corrected[1:-1]
        
        # Strip whitespace
        corrected = corrected.strip()
        
        # Remove shell prompts
        for prefix in ['$ ', '> ', '# ', 'Output: ', 'Result: ']:
            if corrected.startswith(prefix):
                corrected = corrected[len(prefix):]
        
        return corrected

