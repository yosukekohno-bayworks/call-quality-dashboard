"""
Unit tests for LLM analysis service.

Tests use mocks to avoid actual API calls to Anthropic/OpenAI.
"""
import os

# Set test environment before imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["OPENAI_API_KEY"] = "test-openai-key"

# Patch JSONB to JSON for SQLite compatibility
from sqlalchemy import JSON
import sqlalchemy.dialects.postgresql as pg_dialect
pg_dialect.JSONB = JSON

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import (
    LLMService,
    FlowClassificationResult,
    FlowComplianceResult,
    QualityScoreResult,
    SummaryResult,
    FillerAnalysisResult,
)


class TestLLMServiceInit:
    """Tests for LLMService initialization."""

    def test_default_provider_is_anthropic(self):
        """Test default provider is anthropic."""
        service = LLMService()
        assert service.provider == "anthropic"

    def test_custom_provider(self):
        """Test custom provider setting."""
        service = LLMService(provider="openai")
        assert service.provider == "openai"

    def test_clients_lazy_initialized(self):
        """Test that API clients are lazily initialized."""
        service = LLMService()
        assert service._anthropic is None
        assert service._openai is None


class TestParseJsonResponse:
    """Tests for _parse_json_response method."""

    def setup_method(self):
        self.service = LLMService()

    def test_parse_plain_json(self):
        """Test parsing plain JSON string."""
        response = '{"key": "value", "number": 42}'
        result = self.service._parse_json_response(response)

        assert result == {"key": "value", "number": 42}

    def test_parse_json_in_code_block(self):
        """Test parsing JSON inside code block."""
        response = '''Some text before
```json
{"key": "value"}
```
Some text after'''
        result = self.service._parse_json_response(response)

        assert result == {"key": "value"}

    def test_parse_json_embedded_in_text(self):
        """Test parsing JSON embedded in text."""
        response = 'Here is the result: {"score": 85} end of response'
        result = self.service._parse_json_response(response)

        assert result == {"score": 85}

    def test_parse_invalid_json_raises_error(self):
        """Test that completely invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Could not parse JSON"):
            self.service._parse_json_response("no json here at all")

    def test_parse_nested_json(self):
        """Test parsing nested JSON structure."""
        response = json.dumps({
            "overall_score": 85,
            "criteria_scores": {"greeting": 10, "listening": 18},
            "strengths": ["Good greeting"],
        })
        result = self.service._parse_json_response(response)

        assert result["overall_score"] == 85
        assert result["criteria_scores"]["greeting"] == 10


class TestFlowClassification:
    """Tests for classify_flow method."""

    @pytest.mark.asyncio
    async def test_classify_flow_success(self):
        """Test successful flow classification."""
        service = LLMService()

        mock_response = json.dumps({
            "flow_id": "flow-1",
            "flow_name": "Product Inquiry",
            "confidence": 0.95,
            "reasoning": "Customer asked about product details",
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.classify_flow(
                transcript="Customer: I'd like to know about your product X.",
                available_flows=[
                    {"id": "flow-1", "name": "Product Inquiry", "classification_criteria": "Product questions"},
                    {"id": "flow-2", "name": "Complaint", "classification_criteria": "Customer complaints"},
                ],
            )

        assert isinstance(result, FlowClassificationResult)
        assert result.flow_id == "flow-1"
        assert result.flow_name == "Product Inquiry"
        assert result.confidence == 0.95
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_classify_flow_no_match(self):
        """Test flow classification with no matching flow."""
        service = LLMService()

        mock_response = json.dumps({
            "flow_id": None,
            "flow_name": None,
            "confidence": 0.2,
            "reasoning": "No matching flow found",
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.classify_flow(
                transcript="Random conversation",
                available_flows=[
                    {"id": "flow-1", "name": "Product Inquiry", "classification_criteria": "Products"},
                ],
            )

        assert result.flow_id is None
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_classify_flow_empty_flows_list(self):
        """Test flow classification with empty flows list."""
        service = LLMService()

        mock_response = json.dumps({
            "flow_id": None,
            "flow_name": None,
            "confidence": 0.0,
            "reasoning": "No flows available",
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.classify_flow(
                transcript="Any transcript",
                available_flows=[],
            )

        assert result.flow_id is None


class TestFlowCompliance:
    """Tests for check_flow_compliance method."""

    @pytest.mark.asyncio
    async def test_check_compliance_compliant(self):
        """Test compliance check for compliant call."""
        service = LLMService()

        mock_response = json.dumps({
            "is_compliant": True,
            "overall_score": 90,
            "step_results": [
                {"step": "Greeting", "completed": True, "notes": "Proper greeting"},
                {"step": "Identify", "completed": True, "notes": "Issue identified"},
            ],
            "missing_steps": [],
            "issues": [],
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.check_flow_compliance(
                transcript="Agent: Good morning! How can I help?",
                flow_definition={"steps": [{"name": "Greeting"}, {"name": "Identify"}]},
            )

        assert isinstance(result, FlowComplianceResult)
        assert result.is_compliant is True
        assert result.overall_score == 90
        assert len(result.step_results) == 2
        assert len(result.missing_steps) == 0

    @pytest.mark.asyncio
    async def test_check_compliance_non_compliant(self):
        """Test compliance check for non-compliant call."""
        service = LLMService()

        mock_response = json.dumps({
            "is_compliant": False,
            "overall_score": 40,
            "step_results": [
                {"step": "Greeting", "completed": False, "notes": "No proper greeting"},
                {"step": "Closing", "completed": False, "notes": "Abrupt ending"},
            ],
            "missing_steps": ["Greeting", "Closing"],
            "issues": ["No greeting", "No proper closing"],
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.check_flow_compliance(
                transcript="Agent: What do you want?",
                flow_definition={"steps": [{"name": "Greeting"}, {"name": "Closing"}]},
            )

        assert result.is_compliant is False
        assert result.overall_score == 40
        assert len(result.missing_steps) == 2
        assert len(result.issues) == 2


class TestQualityScore:
    """Tests for calculate_quality_score method."""

    @pytest.mark.asyncio
    async def test_quality_score_high(self):
        """Test quality scoring for high quality call."""
        service = LLMService()

        mock_response = json.dumps({
            "overall_score": 92,
            "criteria_scores": {
                "greeting": 10,
                "listening": 18,
                "clarity": 19,
                "problem_solving": 23,
                "closing": 9,
                "language": 13,
            },
            "strengths": ["Excellent greeting", "Clear explanations"],
            "improvements": ["Slightly improve closing"],
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.calculate_quality_score(
                transcript="Agent: Good morning! Thank you for calling...",
            )

        assert isinstance(result, QualityScoreResult)
        assert result.overall_score == 92
        assert result.criteria_scores["greeting"] == 10
        assert len(result.strengths) > 0
        assert len(result.improvements) > 0

    @pytest.mark.asyncio
    async def test_quality_score_low(self):
        """Test quality scoring for low quality call."""
        service = LLMService()

        mock_response = json.dumps({
            "overall_score": 35,
            "criteria_scores": {
                "greeting": 3,
                "listening": 5,
                "clarity": 8,
                "problem_solving": 10,
                "closing": 2,
                "language": 7,
            },
            "strengths": [],
            "improvements": ["Improve greeting", "Better listening", "Follow protocol"],
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.calculate_quality_score(
                transcript="Agent: What?",
            )

        assert result.overall_score == 35
        assert len(result.improvements) > 0

    @pytest.mark.asyncio
    async def test_quality_score_with_custom_prompt(self):
        """Test quality scoring with custom evaluation prompt."""
        service = LLMService()

        mock_response = json.dumps({
            "overall_score": 75,
            "criteria_scores": {"custom_metric": 75},
            "strengths": ["Met custom criteria"],
            "improvements": [],
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response) as mock_call:
            result = await service.calculate_quality_score(
                transcript="Test transcript",
                custom_prompt="Custom evaluation prompt",
            )

            # Verify custom prompt was passed as system prompt
            call_args = mock_call.call_args
            assert call_args[0][0] == "Custom evaluation prompt"

        assert result.overall_score == 75


class TestCallSummary:
    """Tests for summarize_call method."""

    @pytest.mark.asyncio
    async def test_summarize_call_success(self):
        """Test successful call summarization."""
        service = LLMService()

        mock_response = json.dumps({
            "summary": "Customer inquired about order #12345 status. Agent confirmed it was shipped.",
            "inquiry_category": "Order Status",
            "key_points": ["Order #12345", "Shipped yesterday", "Expected delivery Friday"],
            "resolution": "Provided tracking information",
            "follow_up_required": False,
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.summarize_call(
                transcript="Customer: Where is my order #12345?\nAgent: It was shipped yesterday.",
            )

        assert isinstance(result, SummaryResult)
        assert len(result.summary) > 0
        assert result.inquiry_category == "Order Status"
        assert len(result.key_points) > 0
        assert result.resolution is not None
        assert result.follow_up_required is False

    @pytest.mark.asyncio
    async def test_summarize_call_unresolved(self):
        """Test summarization for unresolved call."""
        service = LLMService()

        mock_response = json.dumps({
            "summary": "Customer reported defective product. Issue requires escalation.",
            "inquiry_category": "Complaint",
            "key_points": ["Defective product", "Requires escalation"],
            "resolution": None,
            "follow_up_required": True,
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.summarize_call(
                transcript="Customer: This product is broken!",
            )

        assert result.resolution is None
        assert result.follow_up_required is True


class TestFillerAnalysis:
    """Tests for analyze_fillers method."""

    @pytest.mark.asyncio
    async def test_analyze_fillers_found(self):
        """Test filler analysis with fillers detected."""
        service = LLMService()

        mock_response = json.dumps({
            "filler_count": 5,
            "fillers": [
                {"word": "えーと", "count": 3},
                {"word": "あの", "count": 2},
            ],
            "silence_duration": 8.5,
            "silence_segments": [
                {"description": "Long pause after question", "duration": 5.0},
                {"description": "Brief silence", "duration": 3.5},
            ],
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.analyze_fillers(
                transcript="Agent: えーと、あの、少々お待ちください。えーと...",
            )

        assert isinstance(result, FillerAnalysisResult)
        assert result.filler_count == 5
        assert len(result.fillers) == 2
        assert result.silence_duration == 8.5
        assert len(result.silence_segments) == 2

    @pytest.mark.asyncio
    async def test_analyze_fillers_clean_speech(self):
        """Test filler analysis with clean speech (no fillers)."""
        service = LLMService()

        mock_response = json.dumps({
            "filler_count": 0,
            "fillers": [],
            "silence_duration": 0.0,
            "silence_segments": [],
        })

        with patch.object(service, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await service.analyze_fillers(
                transcript="Agent: Good morning. How can I help you today?",
            )

        assert result.filler_count == 0
        assert len(result.fillers) == 0
        assert result.silence_duration == 0.0


class TestCallLLM:
    """Tests for _call_llm method."""

    @pytest.mark.asyncio
    async def test_call_llm_anthropic(self):
        """Test LLM call with Anthropic provider."""
        service = LLMService(provider="anthropic")

        mock_content = MagicMock()
        mock_content.text = "response text"
        mock_response = MagicMock()
        mock_response.content = [mock_content]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(type(service), "anthropic", new_callable=lambda: property(lambda self: mock_client)):
            result = await service._call_llm("system prompt", "user prompt")

        assert result == "response text"

    @pytest.mark.asyncio
    async def test_call_llm_openai(self):
        """Test LLM call with OpenAI provider."""
        service = LLMService(provider="openai")

        mock_message = MagicMock()
        mock_message.content = "openai response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch.object(type(service), "openai", new_callable=lambda: property(lambda self: mock_client)):
            result = await service._call_llm("system prompt", "user prompt")

        assert result == "openai response"


class TestFullAnalysis:
    """Tests for full_analysis method."""

    @pytest.mark.asyncio
    async def test_full_analysis_with_flows(self):
        """Test full analysis with available flows."""
        service = LLMService()

        with (
            patch.object(service, "classify_flow", new_callable=AsyncMock) as mock_classify,
            patch.object(service, "check_flow_compliance", new_callable=AsyncMock) as mock_compliance,
            patch.object(service, "calculate_quality_score", new_callable=AsyncMock) as mock_quality,
            patch.object(service, "summarize_call", new_callable=AsyncMock) as mock_summary,
            patch.object(service, "analyze_fillers", new_callable=AsyncMock) as mock_fillers,
        ):
            mock_classify.return_value = FlowClassificationResult(
                flow_id="flow-1", flow_name="Test Flow", confidence=0.9, reasoning="Match"
            )
            mock_compliance.return_value = FlowComplianceResult(
                is_compliant=True, overall_score=85, step_results=[], missing_steps=[], issues=[]
            )
            mock_quality.return_value = QualityScoreResult(
                overall_score=88, criteria_scores={}, strengths=[], improvements=[]
            )
            mock_summary.return_value = SummaryResult(
                summary="Test", inquiry_category="Test", key_points=[], resolution=None, follow_up_required=False
            )
            mock_fillers.return_value = FillerAnalysisResult(
                filler_count=2, fillers=[], silence_duration=3.0, silence_segments=[]
            )

            result = await service.full_analysis(
                transcript="Test transcript",
                available_flows=[
                    {"id": "flow-1", "name": "Test Flow", "classification_criteria": "test", "flow_definition": {"steps": []}},
                ],
            )

        assert "flow_classification" in result
        assert "quality_score" in result
        assert "summary" in result
        assert "filler_analysis" in result
        assert result["quality_score"]["overall_score"] == 88

    @pytest.mark.asyncio
    async def test_full_analysis_without_flows(self):
        """Test full analysis without flows (skips classification)."""
        service = LLMService()

        with (
            patch.object(service, "calculate_quality_score", new_callable=AsyncMock) as mock_quality,
            patch.object(service, "summarize_call", new_callable=AsyncMock) as mock_summary,
            patch.object(service, "analyze_fillers", new_callable=AsyncMock) as mock_fillers,
        ):
            mock_quality.return_value = QualityScoreResult(
                overall_score=75, criteria_scores={}, strengths=[], improvements=[]
            )
            mock_summary.return_value = SummaryResult(
                summary="Test", inquiry_category="Other", key_points=[], resolution=None, follow_up_required=False
            )
            mock_fillers.return_value = FillerAnalysisResult(
                filler_count=0, fillers=[], silence_duration=0.0, silence_segments=[]
            )

            result = await service.full_analysis(transcript="Test transcript")

        assert "flow_classification" not in result
        assert "flow_compliance" not in result
        assert "quality_score" in result
        assert "summary" in result
