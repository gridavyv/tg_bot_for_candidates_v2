"""
Video handling functionality
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from user_data_handler import collect_user_silently
from action_tracker import log_sent_video, log_answered_confirm_sending

VIDEO_SAVED_TEXT = "🚀Поздравляю, я отправил видео руководителю.\nРуководитель посмотрит его и ответит напрямую, если ваши вайбы совпали.\nХорошего дня!😊"
MAX_DURATION_SECS = 90

def _validate_incoming_video(file_size: int, duration: int, max_duration: int = MAX_DURATION_SECS) -> str:
    """Validate incoming video file and return error message if invalid, empty string if valid"""
    # Check duration
    if duration > max_duration:
        return f"Видео слишком длиннее. Пожалуйста, перезапиши более короткое до 60 секунд."
    
    # Check file size (50MB limit)
    if file_size:
        file_size_mb = file_size / (1024 * 1024)
        if file_size_mb > 50:
            return f"Видео больше максимального размера 50 MB. Пожалуйста, запиши кружочек, он точно меньше 50 MB."
    
    return ""


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE, ask_to_confirm_sending_func) -> None:
    """Handle incoming video messages"""
    if not update.message:
        return
    
    # Collect user data silently (in case it wasn't collected before)
    await collect_user_silently(update, context)

    tg_video = update.message.video
    tg_vnote = update.message.video_note
    tg_doc = update.message.document if update.message.document and (update.message.document.mime_type or "").startswith("video/") else None

    file_id = None
    kind = None
    duration = None
    file_size = None
    
    if tg_video:
        file_id = tg_video.file_id
        kind = "video"
        duration = tg_video.duration
        file_size = getattr(tg_video, 'file_size', None)
    elif tg_vnote:
        file_id = tg_vnote.file_id
        kind = "video_note"
        duration = tg_vnote.duration
        file_size = getattr(tg_vnote, 'file_size', None)
    elif tg_doc:
        file_id = tg_doc.file_id
        kind = "document_video"
        file_size = getattr(tg_doc, 'file_size', None)

    if not file_id:
        await update.message.reply_text("Не удалось определить видео. Пришли, пожалуйста, именно видео.")
        return

    # Validate video using the helper function
    error_msg = _validate_incoming_video(file_size or 0, duration or 0)
    if error_msg:
        await update.message.reply_text(error_msg)
        return

    context.user_data["pending_file_id"] = file_id
    context.user_data["pending_kind"] = kind
    context.user_data["pending_duration"] = duration

    # Log that user sent a video
    video_info = {
        "kind": kind,
        "duration": duration,
        "file_size": file_size
    }
    log_sent_video(update, context, video_info)

    await ask_to_confirm_sending_func(update, context)


async def download_video_locally(tg_file, user_id: int, kind: str = "video", bot_type: str = "manager") -> str:
    """Download video file to local storage and return the path"""
    try:
        # Create downloads directory based on bot type
        if bot_type == "applicant":
            downloads_dir = Path("applicant_video")
        else:
            downloads_dir = Path("manager_video")
        downloads_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename with appropriate extension
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if kind == "video_note":
            filename = f"{bot_type}_{user_id}_{timestamp}_note.mp4"
        else:
            filename = f"{bot_type}_{user_id}_{timestamp}.mp4"
        local_path = downloads_dir / filename

        # Download the file
        await tg_file.download_to_drive(custom_path=str(local_path))

        # Verify the file was created
        if local_path.exists():
            return str(local_path)
        else:
            return ""
    except Exception as e:
        return ""


async def handle_video_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_type: str = "manager") -> None:
    """Handle video confirmation for both manager and applicant bots"""
    query = update.callback_query
    await query.answer()

    action = query.data
    file_id = context.user_data.get("pending_file_id")
    
    # Log user's answer about confirming sending
    log_answered_confirm_sending(update, context, action)
    
    if action in ["confirm_yes", "privacy_confirm_yes"]:
        if not file_id:
            if query.message:
                await query.message.reply_text("Нет видео для сохранения. Пришли заново, пожалуйста.")
            else:
                await context.bot.send_message(chat_id=query.from_user.id, text="Нет видео для сохранения. Пришли заново, пожалуйста.")
            return

        # Download video to local storage
        tg_file = await context.bot.get_file(file_id)
        kind = context.user_data.get("pending_kind", "video")
        local_path = await download_video_locally(tg_file, query.from_user.id, kind, bot_type)
        
        if not local_path:
            await query.edit_message_text("Ошибка при скачивании видео. Пришли заново, пожалуйста.")
            return
        
        # Clear pending data
        context.user_data.pop("pending_file_id", None)
        context.user_data.pop("pending_kind", None)
        context.user_data.pop("pending_duration", None)

        if query.message:
            await query.message.reply_text(VIDEO_SAVED_TEXT)
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text=VIDEO_SAVED_TEXT)
    else:
        # Clear pending data
        context.user_data.pop("pending_file_id", None)
        context.user_data.pop("pending_kind", None)
        context.user_data.pop("pending_duration", None)
        
        if query.message:
            await query.message.reply_text("Хорошо, запиши новое видео и пришли его сюда, пожалуйста.")
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text="Хорошо, запиши новое видео и пришли его сюда, пожалуйста.")
