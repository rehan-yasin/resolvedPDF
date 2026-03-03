"""
usage_tracker.py
----------------
Tracks how many conversions a user has done today.
Free tier: 3 per day. Saves state in a local JSON file.
"""

import json
import os
from datetime import date

TRACKER_FILE = os.path.join(os.path.expanduser("~"), ".resolved_plugin_usage.json")
FREE_DAILY_LIMIT = 3


def _load() -> dict:
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as f:
            return json.load(f)
    return {}


def _save(data: dict):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f)


def get_usage_today() -> int:
    """Return how many conversions have been done today."""
    data = _load()
    today = str(date.today())
    return data.get(today, 0)


def increment_usage():
    """Increment today's usage count by 1."""
    data = _load()
    today = str(date.today())
    data[today] = data.get(today, 0) + 1
    _save(data)


def is_premium() -> bool:
    """Check if user has an active premium license key."""
    data = _load()
    return data.get("premium", False)


def activate_premium(license_key: str) -> bool:
    """
    Validate and activate a premium license key.
    Right now this is a static check — replace with your API call.
    """
    VALID_KEYS = {"RESOLVED-PREMIUM-2026", "BETA-TESTER-KEY"}  # Replace with real check
    if license_key.strip().upper() in VALID_KEYS:
        data = _load()
        data["premium"] = True
        data["license_key"] = license_key.strip()
        _save(data)
        return True
    return False


def can_convert() -> tuple[bool, str]:
    """
    Returns (True, "") if conversion is allowed.
    Returns (False, reason_message) if not.
    """
    if is_premium():
        return True, ""
    used = get_usage_today()
    if used < FREE_DAILY_LIMIT:
        remaining = FREE_DAILY_LIMIT - used
        return True, f"{remaining} free conversion(s) left today"
    return False, (
        f"You've used all {FREE_DAILY_LIMIT} free conversions for today.\n"
        "Upgrade to Premium for unlimited conversions!"
    )
