"""
User action tracking system for detailed analytics
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from telegram import Update
from telegram.ext import ContextTypes


# Action types constants
class ActionType:
    START = "start"
    GOT_VIDEO = "got_video"
    ASKED_ABOUT_WATCHED_VIDEO = "asked_about_watched_video"
    ANSWERED_ABOUT_WATCHED_VIDEO = "answered_about_watched_video"
    ASKED_TO_SHOOT_VIDEO = "asked_to_shoot_video"
    ANSWERED_TO_SHOOT_VIDEO = "answered_to_shoot_video"
    GOT_INSTRUCTIONS = "got_instructions"
    SENT_VIDEO = "sent_video"
    ASKED_TO_CONFIRM_SENDING = "asked_to_confirm_sending"
    ANSWERED_CONFIRM_SENDING = "answered_confirm_sending"
    ASKED_TO_CONFIRM_PRIVACY = "asked_to_confirm_privacy"
    ANSWERED_CONFIRM_PRIVACY = "answered_confirm_privacy"
    ASKED_WHY_HESITANT_OR_REJECT = "asked_why_hesitant_or_reject"
    ANSWERED_WHY_HESITANT_OR_REJECT = "answered_why_hesitant_or_reject"
    START_TRIGGERED_AGAIN = "start_triggered_again"


def _get_user_id_from_update(update: Update) -> Optional[int]:
    """Extract user ID from update"""
    if update.effective_user:
        return update.effective_user.id
    return None


def _log_action(action_type: str, user_id: int, additional_data: Optional[Dict[str, Any]] = None, 
                filename: str = "user_actions.json") -> None:
    """Log a user action with timestamp and additional data"""
    action_entry = {
        "action_type": action_type,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    if additional_data:
        action_entry.update(additional_data)
    
    _append_action_to_file(action_entry, filename)


def _append_action_to_file(action_entry: dict, filename: str = "user_actions.json") -> None:
    """Append action entry to JSON file"""
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

        existing.append(action_entry)
        out_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # Fail silently to avoid breaking bot flow
        pass


# Action logging functions
def log_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when user starts the bot"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.START, user_id)


def log_got_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when user receives manager video"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.GOT_VIDEO, user_id)


def log_asked_about_watched_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when bot asks about watched video"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ASKED_ABOUT_WATCHED_VIDEO, user_id)


def log_answered_about_watched_video(update: Update, context: ContextTypes.DEFAULT_TYPE, answer: str) -> None:
    """Log user's answer about watched video"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ANSWERED_ABOUT_WATCHED_VIDEO, user_id, {"answer": answer})


def log_asked_to_shoot_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when bot asks if user wants to shoot video"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ASKED_TO_SHOOT_VIDEO, user_id)


def log_answered_to_shoot_video(update: Update, context: ContextTypes.DEFAULT_TYPE, answer: str) -> None:
    """Log user's answer about shooting video"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ANSWERED_TO_SHOOT_VIDEO, user_id, {"answer": answer})


def log_got_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when user receives video shooting instructions"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.GOT_INSTRUCTIONS, user_id)


def log_sent_video(update: Update, context: ContextTypes.DEFAULT_TYPE, video_info: Optional[Dict[str, Any]] = None) -> None:
    """Log when user sends a video"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        additional_data = video_info or {}
        _log_action(ActionType.SENT_VIDEO, user_id, additional_data)


def log_asked_to_confirm_sending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when bot asks to confirm video sending"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ASKED_TO_CONFIRM_SENDING, user_id)


def log_answered_confirm_sending(update: Update, context: ContextTypes.DEFAULT_TYPE, answer: str) -> None:
    """Log user's answer about confirming video sending"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ANSWERED_CONFIRM_SENDING, user_id, {"answer": answer})


def log_asked_to_confirm_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when bot asks to confirm privacy policy"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ASKED_TO_CONFIRM_PRIVACY, user_id)


def log_answered_confirm_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE, answer: str) -> None:
    """Log user's answer about confirming privacy policy"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ANSWERED_CONFIRM_PRIVACY, user_id, {"answer": answer})


def log_asked_why_hesitant_or_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when bot asks why user is hesitant or rejects"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ASKED_WHY_HESITANT_OR_REJECT, user_id)


def log_answered_why_hesitant_or_reject(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str) -> None:
    """Log user's reason for being hesitant or rejecting"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.ANSWERED_WHY_HESITANT_OR_REJECT, user_id, {"reason": reason})


def log_start_triggered_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log when user triggers start command again"""
    user_id = _get_user_id_from_update(update)
    if user_id:
        _log_action(ActionType.START_TRIGGERED_AGAIN, user_id)


def get_user_actions(user_id: int, filename: str = "user_actions.json") -> list:
    """Get all actions for a specific user"""
    out_path = Path(filename)
    if not out_path.exists():
        return []
    
    try:
        actions = json.loads(out_path.read_text(encoding="utf-8"))
        if not isinstance(actions, list):
            return []
        
        return [action for action in actions if action.get("user_id") == user_id]
    except Exception:
        return []


def get_user_action_summary(user_id: int, filename: str = "user_actions.json") -> Dict[str, Any]:
    """Get a summary of user actions"""
    actions = get_user_actions(user_id, filename)
    
    if not actions:
        return {"user_id": user_id, "total_actions": 0, "actions": []}
    
    # Count actions by type
    action_counts = {}
    for action in actions:
        action_type = action.get("action_type", "unknown")
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
    
    # Get first and last action timestamps
    timestamps = [action.get("timestamp") for action in actions if action.get("timestamp")]
    timestamps.sort()
    
    return {
        "user_id": user_id,
        "total_actions": len(actions),
        "first_action": timestamps[0] if timestamps else None,
        "last_action": timestamps[-1] if timestamps else None,
        "action_counts": action_counts,
        "actions": actions
    }
