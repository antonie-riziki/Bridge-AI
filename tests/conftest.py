"""Keep the suite offline. Individual tests opt into a fake provider."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _offline_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASI_API_KEY", "")
    monkeypatch.setenv("OMEGA_LLM_ENABLED", "false")
