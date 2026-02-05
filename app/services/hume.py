import asyncio
import base64
import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


@dataclass
class EmotionScore:
    """Single emotion score at a point in time."""
    emotion: str
    score: float  # 0.0 to 1.0


@dataclass
class EmotionPrediction:
    """Emotion prediction for a segment of audio."""
    start_time: float  # seconds
    end_time: float  # seconds
    emotions: list[EmotionScore]
    dominant_emotion: str
    dominant_score: float


@dataclass
class VoiceAnalysisResult:
    """Complete voice emotion analysis result."""
    predictions: list[EmotionPrediction]
    average_emotions: dict[str, float]  # Averaged across all segments
    dominant_emotion: str  # Overall dominant emotion
    audio_duration: float


# Hume emotion categories (prosody model)
HUME_EMOTIONS = [
    "admiration", "adoration", "aesthetic_appreciation", "amusement", "anger",
    "anxiety", "awe", "awkwardness", "boredom", "calmness", "concentration",
    "confusion", "contemplation", "contempt", "contentment", "craving",
    "determination", "disappointment", "disgust", "distress", "doubt",
    "ecstasy", "embarrassment", "empathic_pain", "entrancement", "envy",
    "excitement", "fear", "guilt", "horror", "interest", "joy", "love",
    "nostalgia", "pain", "pride", "realization", "relief", "romance",
    "sadness", "satisfaction", "shame", "surprise_negative", "surprise_positive",
    "sympathy", "tiredness", "triumph"
]

# Key emotions for call center analysis
RELEVANT_EMOTIONS = [
    "anger", "anxiety", "calmness", "concentration", "confusion",
    "contentment", "disappointment", "distress", "excitement", "fear",
    "frustration", "interest", "joy", "sadness", "satisfaction", "surprise_negative"
]


class HumeService:
    """
    Service for voice emotion analysis using Hume AI API.
    """

    BASE_URL = "https://api.hume.ai/v0"

    def __init__(self):
        self._api_key = settings.HUME_API_KEY

    def _get_headers(self) -> dict[str, str]:
        """Get authorization headers."""
        return {
            "X-Hume-Api-Key": self._api_key,
            "Content-Type": "application/json",
        }

    async def analyze_voice_emotions(
        self,
        audio_content: bytes,
        filename: str = "audio.mp3",
    ) -> VoiceAnalysisResult:
        """
        Analyze emotions in voice audio using Hume AI.

        Args:
            audio_content: Audio file content as bytes
            filename: Filename with extension

        Returns:
            VoiceAnalysisResult with emotion predictions
        """
        # Start batch job
        job_id = await self._start_batch_job(audio_content, filename)

        # Poll for completion
        result = await self._wait_for_job(job_id)

        return self._parse_result(result)

    async def _start_batch_job(
        self,
        audio_content: bytes,
        filename: str,
    ) -> str:
        """Start a batch inference job."""
        # Encode audio as base64
        audio_base64 = base64.b64encode(audio_content).decode("utf-8")

        # Determine content type
        ext = filename.split(".")[-1].lower()
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "m4a": "audio/mp4",
        }
        content_type = content_type_map.get(ext, "audio/mpeg")

        payload = {
            "models": {
                "prosody": {}  # Voice emotion analysis
            },
            "urls": [],
            "files": [
                {
                    "filename": filename,
                    "content_type": content_type,
                    "data": audio_base64,
                }
            ],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.BASE_URL}/batch/jobs",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["job_id"]

    async def _wait_for_job(
        self,
        job_id: str,
        max_wait_seconds: int = 300,
        poll_interval: float = 2.0,
    ) -> dict[str, Any]:
        """Wait for batch job to complete."""
        elapsed = 0.0

        async with httpx.AsyncClient(timeout=30) as client:
            while elapsed < max_wait_seconds:
                response = await client.get(
                    f"{self.BASE_URL}/batch/jobs/{job_id}",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                status = data.get("state", {}).get("status")
                if status == "COMPLETED":
                    # Get predictions
                    pred_response = await client.get(
                        f"{self.BASE_URL}/batch/jobs/{job_id}/predictions",
                        headers=self._get_headers(),
                    )
                    pred_response.raise_for_status()
                    return pred_response.json()
                elif status == "FAILED":
                    raise Exception(f"Hume job failed: {data.get('state', {}).get('message')}")

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

        raise TimeoutError(f"Hume job {job_id} did not complete within {max_wait_seconds}s")

    def _parse_result(self, result: dict[str, Any]) -> VoiceAnalysisResult:
        """Parse Hume API result into structured format."""
        predictions: list[EmotionPrediction] = []
        emotion_totals: dict[str, list[float]] = {e: [] for e in HUME_EMOTIONS}
        total_duration = 0.0

        # Navigate the nested result structure
        for file_result in result:
            if "results" not in file_result:
                continue

            for model_result in file_result.get("results", {}).get("predictions", []):
                if "models" not in model_result:
                    continue

                prosody = model_result.get("models", {}).get("prosody", {})
                grouped_preds = prosody.get("grouped_predictions", [])

                for group in grouped_preds:
                    for pred in group.get("predictions", []):
                        time_info = pred.get("time", {})
                        start_time = time_info.get("begin", 0.0)
                        end_time = time_info.get("end", 0.0)
                        total_duration = max(total_duration, end_time)

                        emotions_data = pred.get("emotions", [])
                        emotion_scores = []

                        for emotion_data in emotions_data:
                            emotion_name = emotion_data.get("name", "")
                            score = emotion_data.get("score", 0.0)

                            emotion_scores.append(EmotionScore(
                                emotion=emotion_name,
                                score=score,
                            ))

                            if emotion_name in emotion_totals:
                                emotion_totals[emotion_name].append(score)

                        # Find dominant emotion for this segment
                        if emotion_scores:
                            dominant = max(emotion_scores, key=lambda x: x.score)
                            predictions.append(EmotionPrediction(
                                start_time=start_time,
                                end_time=end_time,
                                emotions=emotion_scores,
                                dominant_emotion=dominant.emotion,
                                dominant_score=dominant.score,
                            ))

        # Calculate average emotions
        average_emotions = {}
        for emotion, scores in emotion_totals.items():
            if scores:
                average_emotions[emotion] = sum(scores) / len(scores)
            else:
                average_emotions[emotion] = 0.0

        # Find overall dominant emotion
        overall_dominant = max(average_emotions.items(), key=lambda x: x[1])

        return VoiceAnalysisResult(
            predictions=predictions,
            average_emotions=average_emotions,
            dominant_emotion=overall_dominant[0] if overall_dominant else "neutral",
            audio_duration=total_duration,
        )

    def get_relevant_emotions(
        self,
        result: VoiceAnalysisResult,
    ) -> dict[str, float]:
        """
        Get only the emotions relevant for call center analysis.

        Returns a subset of emotions that are most useful for
        evaluating customer service quality.
        """
        return {
            emotion: score
            for emotion, score in result.average_emotions.items()
            if emotion in RELEVANT_EMOTIONS
        }

    def calculate_sentiment_score(
        self,
        result: VoiceAnalysisResult,
    ) -> float:
        """
        Calculate an overall sentiment score from -1 (negative) to 1 (positive).

        Based on the balance of positive vs negative emotions.
        """
        positive_emotions = [
            "calmness", "contentment", "excitement", "interest",
            "joy", "satisfaction", "surprise_positive"
        ]
        negative_emotions = [
            "anger", "anxiety", "confusion", "disappointment",
            "distress", "fear", "frustration", "sadness", "surprise_negative"
        ]

        positive_sum = sum(
            result.average_emotions.get(e, 0.0) for e in positive_emotions
        )
        negative_sum = sum(
            result.average_emotions.get(e, 0.0) for e in negative_emotions
        )

        total = positive_sum + negative_sum
        if total == 0:
            return 0.0

        # Normalize to -1 to 1 range
        return (positive_sum - negative_sum) / total

    def predictions_to_dict(
        self,
        predictions: list[EmotionPrediction],
    ) -> list[dict[str, Any]]:
        """Convert predictions to dict format for JSON storage."""
        return [
            {
                "start_time": p.start_time,
                "end_time": p.end_time,
                "dominant_emotion": p.dominant_emotion,
                "dominant_score": p.dominant_score,
                "emotions": {e.emotion: e.score for e in p.emotions},
            }
            for p in predictions
        ]


# Singleton instance
hume_service = HumeService()


def get_hume_service() -> HumeService:
    return hume_service
