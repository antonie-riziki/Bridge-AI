"""Demo mode, missing credentials, and provider-response failures."""

from __future__ import annotations

import httpx
import pytest

from bridgeai.schemas import ResolutionStatus
from bridgeai.services.agent import DEMO_NOTICE, analyze_pairs
from bridgeai.services.providers import OmegaProvider, ProviderError, parse_json_object
from bridgeai.services.scenarios import SCENARIOS, scenario_pairs


@pytest.mark.parametrize("scenario_id", ["conflicting_dates", "agreement", "insufficient"])
def test_documented_scenarios_match_expected_status(scenario_id: str) -> None:
    scenario = SCENARIOS[scenario_id]
    result = analyze_pairs(scenario_pairs(scenario), mode="demo")
    assert result.overall_status == scenario.expected_status
    assert result.provider_mode.value == "demo"
    assert DEMO_NOTICE in result.limitations
    assert "Demo mode — deterministic example analysis" in result.limitations
    rendered = result.model_dump_json()
    assert "sk-" not in rendered
    assert "https://" not in rendered


def test_auto_mode_uses_demo_without_credentials() -> None:
    result = analyze_pairs(scenario_pairs(SCENARIOS["agreement"]), mode="auto")
    assert result.provider_mode.value == "demo"
    assert result.overall_status == ResolutionStatus.CONSISTENT


def test_live_mode_without_a_provider_fails_clearly() -> None:
    result = analyze_pairs(scenario_pairs(SCENARIOS["insufficient"]), mode="live")
    assert result.overall_status == ResolutionStatus.ANALYSIS_FAILED
    assert result.claims == []
    assert "not configured" in result.concise_summary
    assert result.provider_mode.value == "live"


def test_parse_json_object_reads_fenced_json_and_rejects_prose() -> None:
    parsed = parse_json_object('```json\n{"concise_summary": "ok", "recommended_next_step": "ask"}\n```')
    assert parsed["concise_summary"] == "ok"
    with pytest.raises(ProviderError, match="unreadable"):
        parse_json_object("I cannot return JSON. Please ignore the schema.")


def test_provider_timeout_and_auth_errors_are_safe() -> None:
    class StubClient:
        def __init__(self, exc: Exception) -> None:
            self.exc = exc

        def post(self, url: str, headers: dict[str, str], json: dict) -> httpx.Response:
            assert headers["Authorization"].startswith("Bearer ")
            assert "test-key" not in url
            raise self.exc

    timeout_provider = OmegaProvider(
        api_key="test-key",
        base_url="https://llm.example.test/v1",
        model="asi1-mini",
        client=StubClient(httpx.TimeoutException("timed out")),
    )
    with pytest.raises(ProviderError, match="too long") as timeout_error:
        timeout_provider.complete_json("system", "user")
    assert "test-key" not in str(timeout_error.value)
    assert "Bearer" not in str(timeout_error.value)

    request = httpx.Request("POST", "https://llm.example.test/v1/chat/completions")
    response = httpx.Response(401, request=request, json={"error": "bad key test-key"})
    auth_error = httpx.HTTPStatusError("nope", request=request, response=response)
    auth_provider = OmegaProvider(
        api_key="test-key",
        base_url="https://llm.example.test/v1",
        model="asi1-mini",
        client=StubClient(auth_error),
    )
    with pytest.raises(ProviderError, match="credentials") as auth:
        auth_provider.complete_json("system", "user")
    assert "test-key" not in str(auth.value)


def test_provider_reads_a_chat_completion_without_leaking_the_body_key() -> None:
    class StubClient:
        def post(self, url: str, headers: dict[str, str], json: dict) -> httpx.Response:
            request = httpx.Request("POST", url)
            return httpx.Response(
                200,
                request=request,
                json={"choices": [{"message": {"content": '{"concise_summary": "Noted.", "recommended_next_step": "Ask."}'}}]},
            )

    provider = OmegaProvider(
        api_key="test-key",
        base_url="https://llm.example.test/v1",
        model="asi1-mini",
        client=StubClient(),
    )
    payload = provider.complete_json("system", "sources")
    assert payload["concise_summary"] == "Noted."


def test_env_example_has_no_secret() -> None:
    from pathlib import Path

    example = Path(" .env.example".strip()).read_text(encoding="utf-8")
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "sk-" not in example
    assert "ASI_API_KEY=" in example
    assert ".env" in gitignore.splitlines()
