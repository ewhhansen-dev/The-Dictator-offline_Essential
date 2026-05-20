import sys
import io
from unittest.mock import MagicMock
from pathlib import Path

# --- Mocking dependencies for environment without FastAPI/Pydantic ---
mock_fastapi = MagicMock()
def mock_depends(x): return x
mock_fastapi.Depends = mock_depends
mock_fastapi.File = lambda x: x
def mock_decorator(*args, **kwargs):
    def wrapper(func): return func
    return wrapper
mock_fastapi.APIRouter.return_value.get = mock_decorator
mock_fastapi.APIRouter.return_value.post = mock_decorator
class MockHTTPException(Exception):
    def __init__(self, status_code, detail=None):
        self.status_code = status_code
        self.detail = detail
mock_fastapi.HTTPException = MockHTTPException
sys.modules["fastapi"] = mock_fastapi
sys.modules["fastapi.middleware.cors"] = MagicMock()

class MockBaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items(): setattr(self, k, v)
    @classmethod
    def __init_subclass__(cls, **kwargs): pass
    @classmethod
    def __class_getitem__(cls, item): return cls
mock_pydantic = MagicMock()
mock_pydantic.BaseModel = MockBaseModel
sys.modules["pydantic"] = mock_pydantic
sys.modules["faster_whisper"] = MagicMock()

# Now import the routes
from backend.api import routes

def test_transcribe_validation():
    fake_spine = MagicMock()

    # 1. Test invalid extension
    mock_file = MagicMock()
    mock_file.filename = "malicious.sh"
    mock_file.content_type = "text/x-shellscript"
    mock_file.file = io.BytesIO(b"#!/bin/bash")
    try:
        routes.transcribe_audio(file=mock_file, spine=fake_spine)
        assert False, "Should have rejected .sh"
    except MockHTTPException as e:
        assert e.status_code == 400
        assert "Invalid file extension" in e.detail

    # 2. Test invalid MIME type
    mock_file.filename = "audio.wav"
    mock_file.content_type = "text/plain"
    mock_file.file = io.BytesIO(b"RIFF\x00\x00\x00\x00WAVE")
    try:
        routes.transcribe_audio(file=mock_file, spine=fake_spine)
        assert False, "Should have rejected text/plain"
    except MockHTTPException as e:
        assert e.status_code == 400
        assert "Invalid MIME type" in e.detail

    # 3. Test invalid magic bytes
    mock_file.filename = "audio.wav"
    mock_file.content_type = "audio/wav"
    mock_file.file = io.BytesIO(b"NOT_A_WAV")
    try:
        routes.transcribe_audio(file=mock_file, spine=fake_spine)
        assert False, "Should have rejected invalid content"
    except MockHTTPException as e:
        assert e.status_code == 400
        assert "Invalid audio file content" in e.detail

    # 4. Test valid WAV
    mock_file.filename = "audio.wav"
    mock_file.content_type = "audio/wav"
    mock_file.file = io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt ")
    fake_spine.transcribe_file.return_value = "success"
    res = routes.transcribe_audio(file=mock_file, spine=fake_spine)
    assert res.text == "success"

if __name__ == "__main__":
    test_transcribe_validation()
    print("Security validation tests passed.")
