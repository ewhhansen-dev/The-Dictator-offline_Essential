from pathlib import Path
from typing import Optional

from fastapi.testclient import TestClient

from backend.main import app
from backend.api import routes


class FakeSpine:
    def __init__(self):
        self.append_calls = []
        self.transcribe_calls = []
        self.refine_calls = []

    def transcribe_file(self, audio_path: Path) -> str:
        self.transcribe_calls.append(audio_path)
        return "transcribed text"

    def append_session_text(self, text: str) -> Path:
        self.append_calls.append(text)
        return Path("transcripts/2026-01-31.md")

    async def refine_text(self, text: str, template: str, provider: Optional[str] = None) -> str:
        self.refine_calls.append({"text": text, "template": template, "provider": provider})
        return f"Refined: {text}"


class FakeSettings:
    class Transcription:
        model = "small"

    class Session:
        directory = Path("./transcripts")

    transcription = Transcription()
    session = Session()


def test_health_reports_hybrid_mode():
    app.dependency_overrides[routes.get_settings] = lambda: FakeSettings()
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["transcription_model"] == "small"
    assert body["mode"] == "hybrid"
    assert body["external_api_enabled"] is True

    app.dependency_overrides.clear()


def test_transcribe_uses_core_spine_and_returns_text():
    fake_spine = FakeSpine()
    app.dependency_overrides[routes.get_spine] = lambda: fake_spine

    client = TestClient(app)
    response = client.post(
        "/api/transcribe",
        files={"file": ("recording.webm", b"dummy-bytes", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "transcribed text"}
    assert len(fake_spine.transcribe_calls) == 1

    app.dependency_overrides.clear()


def test_append_session_uses_core_spine():
    fake_spine = FakeSpine()
    app.dependency_overrides[routes.get_spine] = lambda: fake_spine

    client = TestClient(app)
    response = client.post("/api/session/append", json={"text": "hello spine"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "file": "transcripts/2026-01-31.md",
    }
    assert fake_spine.append_calls == ["hello spine"]

    app.dependency_overrides.clear()


def test_refine_uses_core_spine():
    fake_spine = FakeSpine()
    app.dependency_overrides[routes.get_spine] = lambda: fake_spine

    client = TestClient(app)
    response = client.post(
        "/api/refine",
        json={"text": "raw text", "template": "fix_grammar"}
    )

    assert response.status_code == 200
    assert response.json() == {"text": "Refined: raw text"}
    assert len(fake_spine.refine_calls) == 1
    assert fake_spine.refine_calls[0]["text"] == "raw text"
    assert fake_spine.refine_calls[0]["template"] == "fix_grammar"

    app.dependency_overrides.clear()
