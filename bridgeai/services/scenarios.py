"""Fixed community-information scenarios for demo mode and tests."""

from __future__ import annotations

from dataclasses import dataclass

from bridgeai.schemas import ResolutionStatus


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    title: str
    description: str
    label_a: str
    text_a: str
    label_b: str
    text_b: str
    expected_status: ResolutionStatus


SCENARIOS: dict[str, Scenario] = {
    "conflicting_dates": Scenario(
        scenario_id="conflicting_dates",
        title="Conflicting outreach dates",
        description="Two clinic notices name the same outreach, but not the same date.",
        label_a="Clinic announcement",
        text_a=(
            "The community clinic will hold an outreach clinic on 12 March 2026 "
            "at the market ground from 9:00 to 13:00. Free blood pressure checks will be offered."
        ),
        label_b="Community notice",
        text_b=(
            "The community clinic outreach day is on 15 March 2026 at the market ground. "
            "Blood pressure checks are free."
        ),
        expected_status=ResolutionStatus.CONFLICTING,
    ),
    "agreement": Scenario(
        scenario_id="agreement",
        title="Sources agree",
        description="Two notices state the same vaccination day, place, and opening time.",
        label_a="School notice",
        text_a=(
            "Vaccination day will be held on 4 April 2026 at the school hall. Doors open at 8:00."
        ),
        label_b="Chief announcement",
        text_b=(
            "Vaccination day will be held on 4 April 2026 at the school hall. Doors open at 8:00."
        ),
        expected_status=ResolutionStatus.CONSISTENT,
    ),
    "insufficient": Scenario(
        scenario_id="insufficient",
        title="Not enough evidence",
        description="Two short notes do not state a checkable fact.",
        label_a="Neighbourhood rumour",
        text_a="Some people say the water is unsafe.",
        label_b="Posted note",
        text_b="A notice was posted near the tap.",
        expected_status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
    ),
}


def scenario_pairs(scenario: Scenario) -> list[tuple[str, str]]:
    return [(scenario.label_a, scenario.text_a), (scenario.label_b, scenario.text_b)]
