from __future__ import annotations

from typing import Optional, List
from pathlib import Path
import base64
import httpx

from app.core.logging import get_logger
from app.core.exceptions import AnswerGenerationError

logger = get_logger(__name__)


class AudioProcessor:
    """
    Transcribe audio using OpenRouter (via aipipe) by sending audio to an
    audio-capable model and asking it to transcribe.

    This is designed for Project2 Q5: return lowercase transcription including 3-digit code.
    """

    def __init__(
        self,
        aipipe_token: Optional[str] = None,
        base_url: str = "https://aipipe.org/openrouter/v1",
        # Best default from your available list for transcription:
        primary_model: str = "mistralai/voxtral-small-24b-2507",
        # Fallbacks (all appear in your /models list):
        fallback_models: Optional[List[str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.primary_model = primary_model
        self.fallback_models = fallback_models or [
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            "google/gemini-2.5-flash-lite",
        ]

        if aipipe_token is None:
            import os
            aipipe_token = os.getenv("AIPIPE_TOKEN")

        if not aipipe_token:
            raise ValueError("AIPIPE_TOKEN not found in environment or constructor")

        self.aipipe_token = aipipe_token
        logger.info(
            "✓ AudioProcessor(OpenRouter) initialized "
            f"primary_model={self.primary_model}"
        )

    def _models_to_try(self) -> List[str]:
        # Keep order: primary first, then fallbacks
        models = [self.primary_model]
        for m in self.fallback_models:
            if m not in models:
                models.append(m)
        return models

    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = "en",
        lowercase: bool = True,
    ) -> str:
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise AnswerGenerationError(f"Audio file not found: {audio_file_path}")

        audio_bytes = audio_path.read_bytes()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Most of your quiz files are .opus
        fmt = "opus" if audio_path.suffix.lower() == ".opus" else "wav"

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.aipipe_token}",
            "Content-Type": "application/json",
        }

        prompt = (
            "Task: Transcribe the provided audio exactly.\n"
            "Output rules:\n"
            "- Return ONLY the transcription text.\n"
            "- Lowercase only.\n"
            "- Include the 3-digit number exactly.\n"
            "- Do not add explanations.\n"
            "- Do not refuse.\n"
        )
        if language:
            prompt += f"Language hint: {language}.\n"

        last_err = None

        for model in self._models_to_try():
            payload = {
                "model": model,
                "temperature": 0,
                # Strongly encourage plain text output
                "response_format": {"type": "text"},
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_b64,
                                    "format": fmt,
                                },
                            },
                        ],
                    }
                ],
            }

            logger.info(f"🎤 Transcribing via OpenRouter: model={model}")
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(url, headers=headers, json=payload)

            if resp.status_code != 200:
                last_err = f"{resp.status_code} - {resp.text}"
                logger.warning(f"Model failed: {model} -> {last_err}")
                continue

            data = resp.json()
            try:
                text = data["choices"][0]["message"]["content"]
            except Exception:
                last_err = f"Unexpected response shape: {data}"
                logger.warning(f"Model returned unexpected shape: {model}")
                continue

            transcription = (text or "").strip()
            transcription = " ".join(transcription.split())
            if lowercase:
                transcription = transcription.lower()

            # Guard against refusals
            low = transcription.lower()
            if "can't process audio" in low or "cannot process audio" in low or "i can't" in low:
                last_err = f"Model refused audio: {model} -> {transcription}"
                logger.warning(last_err)
                continue

            # Success
            logger.info(f"✓ Transcription success with {model}: '{transcription}'")
            return transcription

        raise AnswerGenerationError(
            "All OpenRouter audio-capable models failed for transcription. "
            f"Last error: {last_err}"
        )
