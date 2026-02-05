import io
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from app.config import settings


@dataclass
class TranscriptSegment:
    """A segment of transcribed text with timing information."""
    id: int
    start: float  # seconds
    end: float  # seconds
    text: str
    speaker: str | None = None  # For diarization (future)


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""
    text: str  # Full transcript text
    segments: list[TranscriptSegment]
    language: str
    duration: float  # Total audio duration in seconds


class WhisperService:
    """
    Service for audio transcription using OpenAI Whisper API.
    """

    def __init__(self):
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def transcribe(
        self,
        audio_content: bytes,
        filename: str = "audio.mp3",
        language: str | None = None,
        response_format: str = "verbose_json",
    ) -> TranscriptionResult:
        """
        Transcribe audio content to text with timestamps.

        Args:
            audio_content: Audio file content as bytes
            filename: Filename with extension for format detection
            language: Optional language code (e.g., 'ja' for Japanese)
            response_format: Response format (verbose_json for timestamps)

        Returns:
            TranscriptionResult with full text, segments, and metadata
        """
        # Create file-like object from bytes
        audio_file = io.BytesIO(audio_content)
        audio_file.name = filename

        # Call Whisper API
        kwargs: dict[str, Any] = {
            "model": "whisper-1",
            "file": audio_file,
            "response_format": response_format,
        }

        if language:
            kwargs["language"] = language

        # Request word-level timestamps
        if response_format == "verbose_json":
            kwargs["timestamp_granularities"] = ["segment"]

        response = await self.client.audio.transcriptions.create(**kwargs)

        # Parse response based on format
        if response_format == "verbose_json":
            segments = [
                TranscriptSegment(
                    id=i,
                    start=seg.start,
                    end=seg.end,
                    text=seg.text.strip(),
                )
                for i, seg in enumerate(response.segments or [])
            ]
            return TranscriptionResult(
                text=response.text,
                segments=segments,
                language=response.language or "unknown",
                duration=response.duration or 0.0,
            )
        else:
            # Simple text response
            return TranscriptionResult(
                text=str(response),
                segments=[],
                language="unknown",
                duration=0.0,
            )

    async def transcribe_with_translation(
        self,
        audio_content: bytes,
        filename: str = "audio.mp3",
    ) -> TranscriptionResult:
        """
        Transcribe and translate audio to English.

        Useful for non-English audio when English output is needed.
        """
        audio_file = io.BytesIO(audio_content)
        audio_file.name = filename

        response = await self.client.audio.translations.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
        )

        segments = [
            TranscriptSegment(
                id=i,
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
            )
            for i, seg in enumerate(response.segments or [])
        ]

        return TranscriptionResult(
            text=response.text,
            segments=segments,
            language="en",  # Translation is always to English
            duration=response.duration or 0.0,
        )

    def format_transcript_with_timestamps(
        self,
        result: TranscriptionResult,
        include_timestamps: bool = True,
    ) -> str:
        """
        Format transcript with optional timestamps.

        Args:
            result: TranscriptionResult from transcribe()
            include_timestamps: Whether to include timestamps

        Returns:
            Formatted transcript string
        """
        if not include_timestamps or not result.segments:
            return result.text

        lines = []
        for seg in result.segments:
            start_time = self._format_timestamp(seg.start)
            end_time = self._format_timestamp(seg.end)
            lines.append(f"[{start_time} - {end_time}] {seg.text}")

        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def segments_to_dict(self, segments: list[TranscriptSegment]) -> list[dict]:
        """Convert segments to dict format for JSON storage."""
        return [
            {
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "speaker": seg.speaker,
            }
            for seg in segments
        ]


# Singleton instance
whisper_service = WhisperService()


def get_whisper_service() -> WhisperService:
    return whisper_service
