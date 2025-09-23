"""
User data collection and storage functionality
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes


def _append_user_event(entry: dict, filename: str = "applicant_users.json") -> None:
    """Append user event to JSON file, only if user is new"""
    out_path = Path(filename)
    try:
        if out_path.exists():
            try:
                existing = json.loads(out_path.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            except Exception:
                existing = []
        else:
            existing = []

        # Check if user already exists
        user_id = entry.get("user_id")
        if user_id:
            user_exists = any(user.get("user_id") == user_id for user in existing)
            if not user_exists:
                # Only add essential fields for new users
                clean_entry = {
                    "user_id": entry.get("user_id"),
                    "username": entry.get("username"),
                    "first_name": entry.get("first_name"),
                    "last_name": entry.get("last_name"),
                    "language_code": entry.get("language_code")
                }
                existing.append(clean_entry)
                out_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # Fail silently to avoid breaking bot flow
        pass


async def collect_user_silently(update: Update, context: ContextTypes.DEFAULT_TYPE, filename: str = "applicant_users.json") -> None:
    """Collect user data silently and store it"""
    user = update.effective_user
    chat = update.effective_chat
    collected = {
        "user_id": user.id if user else None,
        "username": user.username if user else None,
        "first_name": user.first_name if user else None,
        "last_name": user.last_name if user else None,
        "language_code": getattr(user, "language_code", None),
        "chat_id": chat.id if chat else None,
        "chat_type": chat.type if chat else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    context.user_data["collected_user"] = collected
    _append_user_event(collected, filename)


def collect_user_data(user_id: Optional[int] = None, username: Optional[str] = None, 
                     first_name: Optional[str] = None, last_name: Optional[str] = None,
                     language_code: Optional[str] = None, filename: str = "applicant_users.json") -> None:
    """Collect user data manually and store it (only essential fields)"""
    collected = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "language_code": language_code,
    }
    _append_user_event(collected, filename)


def get_user_data_from_context(context: ContextTypes.DEFAULT_TYPE) -> Optional[dict]:
    """Get collected user data from context"""
    return context.user_data.get("collected_user")


def clear_user_data_from_context(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear collected user data from context"""
    context.user_data.pop("collected_user", None)
