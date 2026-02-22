from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765

class AudioConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    normalize: bool = True

class TranscriptionConfig(BaseModel):
    model: str = "small"
    device: Literal["cpu", "cuda"] = "cpu"
    compute_type: Literal["int8", "float16", "float32"] = "int8"
    language: str = "en"

class VadConfig(BaseModel):
    enabled: bool = True
    threshold: float = 0.5
    min_speech_duration: float = 0.25
    min_silence_duration: float = 1.0

class SessionConfig(BaseModel):
    directory: Path = Path("./transcripts")
    date_format: str = "%Y-%m-%d"
    include_timestamps: bool = True

class AnthropicConfig(BaseModel):
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024

class OpenAIConfig(BaseModel):
    model: str = "gpt-4o"
    max_tokens: int = 1024

class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"

class LLMConfig(BaseModel):
    default_provider: Literal["anthropic", "openai", "ollama"] = "anthropic"
    anthropic: Optional[AnthropicConfig] = None
    openai: Optional[OpenAIConfig] = None
    ollama: Optional[OllamaConfig] = None


class CoreConfig(BaseModel):
    enable_refine: bool = False

class ClusterConfig(BaseModel):
    enabled: bool = False
    endpoint: str = "http://hivecluster.local:8080"

class TemplatesConfig(BaseModel):
    directory: Path = Path("./prompts")
    default: str = "fix_grammar"

class Settings(BaseModel):
    server: ServerConfig
    audio: AudioConfig
    transcription: TranscriptionConfig
    vad: VadConfig
    session: SessionConfig
    llm: LLMConfig
    cluster: ClusterConfig
    templates: TemplatesConfig
    core: CoreConfig = Field(default_factory=CoreConfig)
