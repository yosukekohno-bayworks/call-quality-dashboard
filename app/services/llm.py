import json
import re
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings


@dataclass
class FlowClassificationResult:
    """Result of flow classification."""
    flow_id: str | None
    flow_name: str | None
    confidence: float
    reasoning: str


@dataclass
class FlowComplianceResult:
    """Result of flow compliance check."""
    is_compliant: bool
    overall_score: float  # 0-100
    step_results: list[dict[str, Any]]  # Per-step compliance
    missing_steps: list[str]
    issues: list[str]


@dataclass
class QualityScoreResult:
    """Result of quality scoring."""
    overall_score: float  # 0-100
    criteria_scores: dict[str, float]  # Per-criteria scores
    strengths: list[str]
    improvements: list[str]


@dataclass
class SummaryResult:
    """Result of call summary."""
    summary: str
    inquiry_category: str
    key_points: list[str]
    resolution: str | None
    follow_up_required: bool


@dataclass
class FillerAnalysisResult:
    """Result of filler word analysis."""
    filler_count: int
    fillers: list[dict[str, Any]]  # {word, count, timestamps}
    silence_duration: float  # Total silence in seconds
    silence_segments: list[dict[str, Any]]  # {start, end, duration}


class LLMService:
    """
    Service for LLM-based call analysis using Claude or GPT.
    """

    def __init__(self, provider: str = "anthropic"):
        self.provider = provider
        self._anthropic: AsyncAnthropic | None = None
        self._openai: AsyncOpenAI | None = None

    @property
    def anthropic(self) -> AsyncAnthropic:
        if self._anthropic is None:
            self._anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._anthropic

    @property
    def openai(self) -> AsyncOpenAI:
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
    ) -> str:
        """Call LLM with given prompts."""
        if self.provider == "anthropic":
            response = await self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        else:
            response = await self.openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content or ""

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Extract and parse JSON from LLM response."""
        # Try to find JSON block
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try to parse entire response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError(f"Could not parse JSON from response: {response[:500]}")

    async def classify_flow(
        self,
        transcript: str,
        available_flows: list[dict[str, Any]],
    ) -> FlowClassificationResult:
        """
        Classify which operation flow the call belongs to.

        Args:
            transcript: Call transcript text
            available_flows: List of flows with {id, name, classification_criteria}

        Returns:
            FlowClassificationResult with matched flow
        """
        flows_desc = "\n".join([
            f"- ID: {f['id']}, Name: {f['name']}, Criteria: {f.get('classification_criteria', 'N/A')}"
            for f in available_flows
        ])

        system_prompt = """あなたはコールセンターの通話分類エキスパートです。
通話内容を分析し、最も適切なオペレーションフローを判定してください。

レスポンスは以下のJSON形式で返してください：
```json
{
    "flow_id": "選択したフローのID（該当なしの場合はnull）",
    "flow_name": "選択したフロー名",
    "confidence": 0.0-1.0の信頼度,
    "reasoning": "判定理由の説明"
}
```"""

        user_prompt = f"""以下の通話内容を分析し、最も適切なオペレーションフローを選択してください。

## 利用可能なフロー:
{flows_desc}

## 通話内容:
{transcript}

どのフローに該当するか判定してください。"""

        response = await self._call_llm(system_prompt, user_prompt)
        data = self._parse_json_response(response)

        return FlowClassificationResult(
            flow_id=data.get("flow_id"),
            flow_name=data.get("flow_name"),
            confidence=float(data.get("confidence", 0.0)),
            reasoning=data.get("reasoning", ""),
        )

    async def check_flow_compliance(
        self,
        transcript: str,
        flow_definition: dict[str, Any],
    ) -> FlowComplianceResult:
        """
        Check if the call follows the operation flow.

        Args:
            transcript: Call transcript text
            flow_definition: Flow definition with steps

        Returns:
            FlowComplianceResult with compliance details
        """
        flow_json = json.dumps(flow_definition, ensure_ascii=False, indent=2)

        system_prompt = """あなたはコールセンターの品質管理エキスパートです。
通話内容がオペレーションフローに沿っているか確認してください。

レスポンスは以下のJSON形式で返してください：
```json
{
    "is_compliant": true/false,
    "overall_score": 0-100のスコア,
    "step_results": [
        {"step": "ステップ名", "completed": true/false, "notes": "備考"}
    ],
    "missing_steps": ["欠落したステップ名のリスト"],
    "issues": ["発見された問題点のリスト"]
}
```"""

        user_prompt = f"""以下の通話内容が、オペレーションフローに沿っているか確認してください。

## オペレーションフロー:
{flow_json}

## 通話内容:
{transcript}

各ステップの遵守状況を評価してください。"""

        response = await self._call_llm(system_prompt, user_prompt)
        data = self._parse_json_response(response)

        return FlowComplianceResult(
            is_compliant=data.get("is_compliant", False),
            overall_score=float(data.get("overall_score", 0)),
            step_results=data.get("step_results", []),
            missing_steps=data.get("missing_steps", []),
            issues=data.get("issues", []),
        )

    async def calculate_quality_score(
        self,
        transcript: str,
        custom_prompt: str | None = None,
    ) -> QualityScoreResult:
        """
        Calculate quality score for the call.

        Args:
            transcript: Call transcript text
            custom_prompt: Optional custom evaluation prompt

        Returns:
            QualityScoreResult with scores and feedback
        """
        system_prompt = custom_prompt or """あなたはコールセンターの品質評価エキスパートです。
通話内容を以下の基準で評価してください：

1. 挨拶・名乗り (10点)
2. 傾聴・共感 (20点)
3. 説明の明確さ (20点)
4. 問題解決力 (25点)
5. クロージング (10点)
6. 言葉遣い・敬語 (15点)

レスポンスは以下のJSON形式で返してください：
```json
{
    "overall_score": 0-100の総合スコア,
    "criteria_scores": {
        "greeting": 0-10,
        "listening": 0-20,
        "clarity": 0-20,
        "problem_solving": 0-25,
        "closing": 0-10,
        "language": 0-15
    },
    "strengths": ["良かった点のリスト"],
    "improvements": ["改善点のリスト"]
}
```"""

        user_prompt = f"""以下の通話内容を評価してください。

## 通話内容:
{transcript}

品質スコアを算出してください。"""

        response = await self._call_llm(system_prompt, user_prompt)
        data = self._parse_json_response(response)

        return QualityScoreResult(
            overall_score=float(data.get("overall_score", 0)),
            criteria_scores=data.get("criteria_scores", {}),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", []),
        )

    async def summarize_call(
        self,
        transcript: str,
        custom_prompt: str | None = None,
    ) -> SummaryResult:
        """
        Generate call summary and categorization.

        Args:
            transcript: Call transcript text
            custom_prompt: Optional custom summary prompt

        Returns:
            SummaryResult with summary and categorization
        """
        system_prompt = custom_prompt or """あなたはコールセンターの通話分析エキスパートです。
通話内容を分析し、要約と分類を行ってください。

レスポンスは以下のJSON形式で返してください：
```json
{
    "summary": "通話内容の要約（100-200文字）",
    "inquiry_category": "問い合わせ種別（例：注文確認、商品問い合わせ、クレーム、技術サポート等）",
    "key_points": ["重要ポイントのリスト"],
    "resolution": "解決内容（未解決の場合はnull）",
    "follow_up_required": true/false
}
```"""

        user_prompt = f"""以下の通話内容を要約・分類してください。

## 通話内容:
{transcript}

要約と問い合わせ種別を判定してください。"""

        response = await self._call_llm(system_prompt, user_prompt)
        data = self._parse_json_response(response)

        return SummaryResult(
            summary=data.get("summary", ""),
            inquiry_category=data.get("inquiry_category", "その他"),
            key_points=data.get("key_points", []),
            resolution=data.get("resolution"),
            follow_up_required=data.get("follow_up_required", False),
        )

    async def analyze_fillers(
        self,
        transcript: str,
        segments: list[dict[str, Any]] | None = None,
    ) -> FillerAnalysisResult:
        """
        Analyze filler words and silences in the call.

        Args:
            transcript: Call transcript text
            segments: Optional list of transcript segments with timestamps

        Returns:
            FillerAnalysisResult with filler and silence analysis
        """
        system_prompt = """あなたは言語分析エキスパートです。
通話内容からフィラー（えーと、あの、その等）と間（沈黙）を分析してください。

レスポンスは以下のJSON形式で返してください：
```json
{
    "filler_count": フィラーの総数,
    "fillers": [
        {"word": "フィラー語", "count": 出現回数}
    ],
    "silence_duration": 推定沈黙時間（秒）,
    "silence_segments": [
        {"description": "沈黙の説明", "duration": 推定秒数}
    ]
}
```"""

        user_prompt = f"""以下の通話内容からフィラーと沈黙を分析してください。

## 通話内容:
{transcript}

フィラーの使用状況と沈黙を分析してください。"""

        response = await self._call_llm(system_prompt, user_prompt)
        data = self._parse_json_response(response)

        return FillerAnalysisResult(
            filler_count=int(data.get("filler_count", 0)),
            fillers=data.get("fillers", []),
            silence_duration=float(data.get("silence_duration", 0)),
            silence_segments=data.get("silence_segments", []),
        )

    async def full_analysis(
        self,
        transcript: str,
        available_flows: list[dict[str, Any]] | None = None,
        selected_flow: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Perform full analysis of a call.

        Combines flow classification, compliance check, quality scoring,
        summary, and filler analysis.

        Args:
            transcript: Call transcript text
            available_flows: List of available operation flows
            selected_flow: Pre-selected flow (skips classification)

        Returns:
            Combined analysis results
        """
        results: dict[str, Any] = {}

        # Flow classification (if flows available and not pre-selected)
        if available_flows and not selected_flow:
            flow_result = await self.classify_flow(transcript, available_flows)
            results["flow_classification"] = {
                "flow_id": flow_result.flow_id,
                "flow_name": flow_result.flow_name,
                "confidence": flow_result.confidence,
                "reasoning": flow_result.reasoning,
            }
            # Find the selected flow for compliance check
            if flow_result.flow_id:
                selected_flow = next(
                    (f for f in available_flows if f["id"] == flow_result.flow_id),
                    None
                )

        # Flow compliance check
        if selected_flow and selected_flow.get("flow_definition"):
            compliance_result = await self.check_flow_compliance(
                transcript, selected_flow["flow_definition"]
            )
            results["flow_compliance"] = {
                "is_compliant": compliance_result.is_compliant,
                "overall_score": compliance_result.overall_score,
                "step_results": compliance_result.step_results,
                "missing_steps": compliance_result.missing_steps,
                "issues": compliance_result.issues,
            }

        # Quality score
        quality_result = await self.calculate_quality_score(transcript)
        results["quality_score"] = {
            "overall_score": quality_result.overall_score,
            "criteria_scores": quality_result.criteria_scores,
            "strengths": quality_result.strengths,
            "improvements": quality_result.improvements,
        }

        # Summary
        summary_result = await self.summarize_call(transcript)
        results["summary"] = {
            "summary": summary_result.summary,
            "inquiry_category": summary_result.inquiry_category,
            "key_points": summary_result.key_points,
            "resolution": summary_result.resolution,
            "follow_up_required": summary_result.follow_up_required,
        }

        # Filler analysis
        filler_result = await self.analyze_fillers(transcript)
        results["filler_analysis"] = {
            "filler_count": filler_result.filler_count,
            "fillers": filler_result.fillers,
            "silence_duration": filler_result.silence_duration,
        }

        return results


# Singleton instance
llm_service = LLMService(provider="anthropic")


def get_llm_service() -> LLMService:
    return llm_service
