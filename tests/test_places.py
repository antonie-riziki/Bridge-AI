"""Place phrases and user-supplied coordinates. No geocoding."""

from __future__ import annotations

import pytest

from bridgeai.services.evidence import validate_source_pairs
from bridgeai.services.places import CoordinateError, listed_places, validate_coordinates
from bridgeai.services.scenarios import SCENARIOS, scenario_pairs


def test_conflict_and_agreement_scenarios_name_a_place() -> None:
    conflict = listed_places(validate_source_pairs(scenario_pairs(SCENARIOS["conflicting_dates"])))
    agreement = listed_places(validate_source_pairs(scenario_pairs(SCENARIOS["agreement"])))
    assert {item.place for item in conflict} == {"market ground"}
    assert {item.source_label for item in conflict} == {"Clinic announcement", "Community notice"}
    assert all(item.excerpt for item in conflict)
    assert {item.place for item in agreement} == {"school hall"}


def test_insufficient_scenario_has_no_place() -> None:
    mentions = listed_places(validate_source_pairs(scenario_pairs(SCENARIOS["insufficient"])))
    assert mentions == []


def test_blank_coordinates_are_not_a_pin() -> None:
    assert validate_coordinates("", "") is None
    assert validate_coordinates("  ", "  ") is None


def test_partial_or_invalid_coordinates_are_rejected() -> None:
    with pytest.raises(CoordinateError, match="both"):
        validate_coordinates("-1.29", "")
    with pytest.raises(CoordinateError, match="numbers"):
        validate_coordinates("south", "36.8")
    with pytest.raises(CoordinateError, match="-90 and 90"):
        validate_coordinates("95", "36.8")
    with pytest.raises(CoordinateError, match="-180 and 180"):
        validate_coordinates("-1.29", "200")


def test_a_known_coordinate_pair_is_returned_unchanged() -> None:
    assert validate_coordinates(" -1.286389 ", "36.817223") == (-1.286389, 36.817223)
