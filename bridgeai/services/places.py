"""Place phrases from supplied text, and checks for coordinates the user already knows.

Notice text is never geocoded. A pin exists only when the person enters both numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

from bridgeai.schemas import ClaimCategory, SourceDocument
from bridgeai.services.evidence import extract_facts


class CoordinateError(ValueError):
    """A latitude or longitude cannot be plotted."""


@dataclass(frozen=True)
class PlaceMention:
    source_id: str
    source_label: str
    place: str
    excerpt: str


def listed_places(sources: list[SourceDocument]) -> list[PlaceMention]:
    mentions: list[PlaceMention] = []
    for source in sources:
        facts, _ambiguous = extract_facts(source)
        for fact in facts:
            if fact.category != ClaimCategory.LOCATION:
                continue
            mentions.append(
                PlaceMention(
                    source_id=fact.source_id,
                    source_label=fact.source_label,
                    place=fact.display,
                    excerpt=fact.excerpt,
                )
            )
    return mentions


def validate_coordinates(latitude: str, longitude: str) -> tuple[float, float] | None:
    """Return a pin, or None when both fields are empty."""
    lat_text = (latitude or "").strip()
    lon_text = (longitude or "").strip()
    if not lat_text and not lon_text:
        return None
    if not lat_text or not lon_text:
        raise CoordinateError("Enter both latitude and longitude, or leave both empty.")
    try:
        lat = float(lat_text)
        lon = float(lon_text)
    except ValueError as exc:
        raise CoordinateError("Latitude and longitude must be numbers.") from exc
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise CoordinateError("Latitude must be between -90 and 90, and longitude between -180 and 180.")
    return lat, lon
