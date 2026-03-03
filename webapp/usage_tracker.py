"""
webapp/usage_tracker.py
-----------------------
IP-based rate limiter. Free tier: 3 conversions/day per IP.
Stores state in memory (reset on server restart) or in a JSON file.
"""

import json
import os
from datetime import date

TRACKER_FILE = os.path.join(os.path.dirname(__file__), ".usage_data.json")
FREE_DAILY_LIMIT = 3


def _load() -> dict:
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save(data: dict):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f)


def get_usage(ip: str) -> int:
    data = _load()
    today = str(date.today())
    return data.get(today, {}).get(ip, 0)


def increment(ip: str):
    data = _load()
    today = str(date.today())
    if today not in data:
        data[today] = {}
    data[today][ip] = data[today].get(ip, 0) + 1
    # Clean up old dates (keep only today)
    data = {today: data[today]}
    _save(data)


def is_premium_key(key: str) -> bool:
    """Validate a premium license key. Replace with real DB/API check."""
    VALID_KEYS = {"RESOLVEDPDF-PREMIUM-2026", "BETA-KEY-001"}
    return key.strip().upper() in VALID_KEYS


def can_convert(ip: str, license_key: str = "") -> tuple:
    """Returns (allowed: bool, message: str, remaining: int)"""
    if license_key and is_premium_key(license_key):
        return True, "premium", -1
    used = get_usage(ip)
    remaining = max(0, FREE_DAILY_LIMIT - used)
    if remaining > 0:
        return True, f"{remaining} conversions left today", remaining
    return False, "Daily free limit reached. Upgrade to Premium.", 0
