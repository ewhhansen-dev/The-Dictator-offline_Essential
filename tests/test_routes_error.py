import pytest
import io
from unittest.mock import MagicMock, patch
from pathlib import Path
from fastapi import HTTPException
from backend.api.routes import transcribe_audio

def test_transcribe_audio_error_returns_500():
    # Setup
    mock_spine = MagicMock()
    mock_spine.transcribe_file.side_effect = Exception("Transcription failed")

    mock_file = MagicMock()
    mock_file.filename = "test.wav"
    # Use a real BytesIO to satisfy shutil.copyfileobj
    mock_file.file = io.BytesIO(b"dummy audio data")

    # We need to mock Path.unlink to verify it's called
    # and also Path.exists to return True so unlink is called
    with patch("backend.api.routes.Path") as MockPath:
        # Mocking the Path instance returned by Path(tmp.name) and Path(file.filename)
        mock_path_instance = MagicMock(spec=Path)
        MockPath.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        # Ensure suffix works for the code: suffix = Path(file.filename or "").suffix or ".wav"
        mock_path_instance.suffix = ".wav"

        # Execute and Verify
        with pytest.raises(HTTPException) as exc_info:
            transcribe_audio(file=mock_file, spine=mock_spine)

        assert exc_info.value.status_code == 500
        assert "Transcription failed" in str(exc_info.value.detail)

        # Verify cleanup
        mock_path_instance.unlink.assert_called_once()
