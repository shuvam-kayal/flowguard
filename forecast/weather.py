"""Financial Weather mapping for forecast shock risk."""
from __future__ import annotations

from constants import FORECAST_WEATHER_SHOCK_THRESHOLD, FORECAST_WEATHER_STABLE_THRESHOLD


def to_weather(shock_probability: float) -> str:
    """Translate the contract's 0–1 income-shock probability into a UI state."""
    if shock_probability < FORECAST_WEATHER_STABLE_THRESHOLD:
        return "STABLE"
    if shock_probability <= FORECAST_WEATHER_SHOCK_THRESHOLD:
        return "WATCH"
    return "SHOCK"
