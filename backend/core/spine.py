from pathlib import Path
from typing import Optional

from backend.config import Settings
from backend.engine import Transcriber, LLMEngine
from backend.output import SessionLogger


class CoreSpine:
    """Core offline dictation flow: transcribe audio, append session logs, and optional LLM refinement."""

    def __init__(self, settings: Settings):
        self.transcriber = Transcriber(settings)
        self.session_logger = SessionLogger(settings)
        self.llm_engine = LLMEngine(settings)

    def transcribe_file(self, audio_path: Path) -> str:
        return self.transcriber.transcribe(audio_path)

    def append_session_text(self, text: str) -> Path:
        return self.session_logger.append(text)

    async def refine_text(self, text: str, template: str, provider: Optional[str] = None) -> str:
        """
        Refine text using the LLM engine.
        """
        return await self.llm_engine.refine_text(text=text, template_name=template, provider=provider)
