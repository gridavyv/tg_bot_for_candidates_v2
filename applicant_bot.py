import asyncio
from pathlib import Path
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from video_handler import handle_video_confirmation, handle_video
from user_data_handler import collect_user_silently
from action_tracker import (
    log_start, log_got_video, log_asked_about_watched_video, log_answered_about_watched_video,
    log_asked_to_shoot_video, log_answered_to_shoot_video, log_got_instructions,
    log_sent_video, log_asked_to_confirm_sending, log_answered_confirm_sending,
    log_asked_to_confirm_privacy, log_answered_confirm_privacy,
    log_asked_why_hesitant_or_reject, log_answered_why_hesitant_or_reject,
    log_start_triggered_again
)


INTRO_TEXT = """👋 Привет!
Уже загружаю приветствие от нанимающего менеджера.\nЭто займет несколько секунд."""
QUESTION_TEXT = """🎥 Хочешь записать свое видео в ответ? 
Я перешлю его напрямую нанимающему менеджеру в обход HR. 
Это ускорит назначение интервью."""
CONFIRM_TEXT = "Использовать это видео для отправки менеджеру или хочешь записать другое?"
MAX_DURATION_SECS = 90

INSTRUCTIONS_TO_SHOOT_VIDEO_TEXT = """📹Запиши видео прямо здесь в чате или загрузи готовое.
Перед отправкой менеджеру я спрошу разрешения, поэтому можно делать сколько угодно дублей)

👉 Не знаешь что сказать вот примерный план:
- Поздоровайся.
- Скажи, почему тебе интересна эта компания или вакансия.
- Коротко объясни, почему ты лучший кандидат.

Видео должно быть коротким (максимум 60 секунд), простым и «продающим».
И главное — не забудь улыбнуться 🙂"""

PRIVACY_TEXT = "Нажимая кнопку, вы даёте согласие на обработку персональных данных. Ссылка на политику конфиденциальности: https://hrvibe.ru/page80523236.html"

def _validate_video_directory(directory_name: str, max_videos: int = 1) -> Path:
    """Validate video directory and return the video file path with comprehensive checks"""
    # Check if directory exists
    video_dir = Path(directory_name)
    if not video_dir.exists():
        raise FileNotFoundError(f"Directory '{directory_name}' not found")
    
    # Find all video files
    video_extensions = ['*.mp4', '*.mov', '*.avi', '*.mkv', '*.webm']
    video_files = []
    for ext in video_extensions:
        video_files.extend(video_dir.glob(ext))
    
    # Check number of videos
    if len(video_files) != 1:
        raise FileNotFoundError(f"No video files or more than 1 found in '{directory_name}' directory")
    
    # Get the video file
    video_path = video_files[0]
    
    # Check file size (Telegram limit is 50MB for videos)
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 50:
        raise ValueError(f"Video '{video_path.name}' is too large: {file_size_mb:.1f}MB. Maximum allowed: 50MB")
    
    return video_path


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler - sends intro text and manager video"""
    # Collect user data silently
    await collect_user_silently(update, context)
    
    # Check if this is a repeat start (user already has data in context)
    if context.user_data.get("collected_user"):
        log_start_triggered_again(update, context)
    else:
        log_start(update, context)
    
    await update.message.reply_text(INTRO_TEXT)
    await asyncio.sleep(1)
    # Get manager video path (with validation)
    try:
        manager_video_path = _validate_video_directory("manager_video", max_videos=1)  
        try:
            # Send video from local file
            with open(manager_video_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=update.message.from_user.id, 
                    video=video_file, 
                    caption="Держи!"
                )
            
            # Log that user got video
            log_got_video(update, context)
            
            # Wait a bit after sending video
            await asyncio.sleep(2)
        except Exception as e:
            error_msg = f"Упс. Не могу отправить видео от менеджера. Ошибка: {str(e)}. Уже пошли чинить."
            # Handle both message and callback query contexts
            if update.message:
                await context.bot.send_message(
                    chat_id=update.message.from_user.id, 
                    text=error_msg
                )
            elif update.callback_query and update.callback_query.message:
                await context.bot.send_message(
                    chat_id=update.callback_query.from_user.id, 
                    text=error_msg
                )
            else:
                # Fallback: send message to user directly
                user_id = update.effective_user.id if update.effective_user else None
                if user_id:
                    await context.bot.send_message(chat_id=user_id, text=error_msg)
    except (FileNotFoundError, ValueError) as e:
        error_msg = f"Ошибка видео от менеджера: {str(e)}"
        # Handle both message and callback query contexts
        if update.message:
            await context.bot.send_message(
                chat_id=update.message.from_user.id, 
                text=error_msg
            )
        elif update.callback_query and update.callback_query.message:
            await context.bot.send_message(
                chat_id=update.callback_query.from_user.id, 
                text=error_msg
            )
        else:
            # Fallback: send message to user directly
            user_id = update.effective_user.id if update.effective_user else None
            if user_id:
                await context.bot.send_message(chat_id=user_id, text=error_msg)
    await asyncio.sleep(3)
    await ask_about_watched_video(update, context)


async def ask_about_watched_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user if they liked the video with 3 options"""
    # Log that we're asking about watched video
    log_asked_about_watched_video(update, context)
    
    keyboard = [
        [InlineKeyboardButton(text="Да", callback_data="video_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="video_no")],
        [InlineKeyboardButton(text="Не вижу видео", callback_data="video_not_seen")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both message and callback query contexts
    if update.message:
        await update.message.reply_text("Тебе понравилось видео?", reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text("Тебе понравилось видео?", reply_markup=reply_markup)
    else:
        # Fallback: send message to user directly
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            await context.bot.send_message(chat_id=user_id, text="Тебе понравилось видео?", reply_markup=reply_markup)


async def ask_to_shoot_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user if they want to record a video"""
    # Log that we're asking to shoot video
    log_asked_to_shoot_video(update, context)
    
    keyboard = [
        [InlineKeyboardButton(text="Кончено, Да", callback_data="yes")],
        [InlineKeyboardButton(text="Возможно, надо подумать", callback_data="maybe")],
        [InlineKeyboardButton(text="Нет, не хочу", callback_data="no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both message and callback query contexts
    if update.message:
        await update.message.reply_text(QUESTION_TEXT, reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(QUESTION_TEXT, reply_markup=reply_markup)
    else:
        # Fallback: send message to user directly
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            await context.bot.send_message(chat_id=user_id, text=QUESTION_TEXT, reply_markup=reply_markup)


async def instructions_to_shoot_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show instructions for shooting video"""
    # Log that user got instructions
    log_got_instructions(update, context)
    
    # Handle both message and callback query contexts
    if update.message:
        await update.message.reply_text(INSTRUCTIONS_TO_SHOOT_VIDEO_TEXT)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(INSTRUCTIONS_TO_SHOOT_VIDEO_TEXT)
    else:
        # Fallback: send message to user directly
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            await context.bot.send_message(chat_id=user_id, text=INSTRUCTIONS_TO_SHOOT_VIDEO_TEXT)


async def ask_to_confirm_sending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user to confirm sending the video"""
    # Log that we're asking to confirm sending
    log_asked_to_confirm_sending(update, context)
    
    keyboard = [
        [InlineKeyboardButton(text="Да", callback_data="confirm_yes_privacy")],
        [InlineKeyboardButton(text="Нет", callback_data="confirm_no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both message and callback query contexts
    if update.message:
        await update.message.reply_text(CONFIRM_TEXT, reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(CONFIRM_TEXT, reply_markup=reply_markup)
    else:
        # Fallback: send message to user directly
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            await context.bot.send_message(chat_id=user_id, text=CONFIRM_TEXT, reply_markup=reply_markup)


async def privacy_policy_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show privacy policy and ask for confirmation"""
    # Log that we're asking to confirm privacy
    log_asked_to_confirm_privacy(update, context)
    
    keyboard = [
        [InlineKeyboardButton(text="Отправить", callback_data="privacy_confirm_yes")],
        [InlineKeyboardButton(text="Не отправлять", callback_data="privacy_confirm_no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both message and callback query contexts
    if update.message:
        await update.message.reply_text(PRIVACY_TEXT, reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(PRIVACY_TEXT, reply_markup=reply_markup)
    else:
        # Fallback: send message to user directly
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            await context.bot.send_message(chat_id=user_id, text=PRIVACY_TEXT, reply_markup=reply_markup)


async def feedback_privacy_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle privacy policy confirmation responses"""
    query = update.callback_query
    await query.answer()
    
    # Log user's answer about privacy confirmation
    answer = "yes" if query.data == "privacy_confirm_yes" else "no"
    log_answered_confirm_privacy(update, context, answer)
    
    if query.data == "privacy_confirm_yes":
        # User agreed to privacy policy, proceed with video download
        await handle_video_confirmation(update, context, bot_type="applicant")
    elif query.data == "privacy_confirm_no":
        # User declined privacy policy, ask why they're hesitant
        await ask_why_hesitant_or_reject_to_shoot_video(update, context)


async def feedback_to_confirm_sending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video confirmation using shared video handler"""
    await handle_video_confirmation(update, context, bot_type="applicant")


async def feedback_about_watched_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video feedback responses"""
    query = update.callback_query
    await query.answer()
    
    # Log user's answer about watched video
    answer_map = {
        "video_yes": "yes",
        "video_no": "no", 
        "video_not_seen": "not_seen"
    }
    log_answered_about_watched_video(update, context, answer_map.get(query.data, query.data))
    
    # Remove inline keyboard if present
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    if query.data == "video_yes":
        # User liked the video
        if query.message:
            await query.message.reply_text("Отлично!⚡")
            await asyncio.sleep(1)
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text="Отлично!⚡")
            await asyncio.sleep(1)
    elif query.data == "video_no":
        # User didn't like the video
        if query.message:
            await query.message.reply_text("Понятно. Спасибо за честность!😊")
            await asyncio.sleep(1)
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text="Понятно. Спасибо за честность!😊")
            await asyncio.sleep(1)
    elif query.data == "video_not_seen":
        # User didn't see the video
        if query.message:
            await query.message.reply_text("Извиняюсь за технические проблемы. Пошел ремонтироваться 😊")
            await asyncio.sleep(1)
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text="Извиняюсь за технические проблемы. Пошел ремонтироваться 😊")
            await asyncio.sleep(1)
    
    # All users proceed to ask_to_shoot_video regardless of their answer
    await ask_to_shoot_video(update, context)


async def ask_why_hesitant_or_reject_to_shoot_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask why user is hesitant or rejects recording video"""
    # Log that we're asking why hesitant or reject
    log_asked_why_hesitant_or_reject(update, context)
    
    keyboard = [
        [InlineKeyboardButton(text="Не хочу устраиваться в эту компанию", callback_data="reason_no_company")],
        [InlineKeyboardButton(text="Неловко записывать видео", callback_data="reason_no_awkward")],
        [InlineKeyboardButton(text="Не знаю как или что записать", callback_data="reason_no_dont_know")],
        [InlineKeyboardButton(text="Переживаю за персональные данные", callback_data="reason_no_privacy")],
        [InlineKeyboardButton(text="Другое", callback_data="reason_no_other")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both message and callback query contexts
    if update.message:
        await update.message.reply_text("Пожалуйста, расскажи почему.😊", reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text("Пожалуйста, расскажи почему.😊", reply_markup=reply_markup)
    else:
        # Fallback: send message to user directly
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            await context.bot.send_message(chat_id=user_id, text="Пожалуйста, расскажи почему.", reply_markup=reply_markup)


async def feedback_why_hesitant_or_reject_to_shoot_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle hesitation or rejection reason responses"""
    query = update.callback_query
    await query.answer()
    
    # Log user's reason for being hesitant or rejecting
    reason_map = {
        "reason_no_company": "no_company",
        "reason_no_awkward": "awkward", 
        "reason_no_dont_know": "dont_know",
        "reason_no_privacy": "privacy",
        "reason_no_other": "other"
    }
    log_answered_why_hesitant_or_reject(update, context, reason_map.get(query.data, query.data))
    
    # Remove inline keyboard if present
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    # No matter what the reason is, just say "Спасибо!"
    if query.message:
        await query.message.reply_text("Спасибо за обратную связь!\nМы это учтем.\nХорошего дня! 😊")
    else:
        await context.bot.send_message(chat_id=query.from_user.id, text="Спасибо за обратную связь!\nМы это учтем.\nХорошего дня! 😊")


async def feedback_to_shoot_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # Log user's answer about shooting video
    log_answered_to_shoot_video(update, context, query.data)
    
    # Remove inline keyboard if present
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    if query.data == "yes":
        # User wants to shoot video, show instructions
        await instructions_to_shoot_video(update, context)
    elif query.data == "maybe" or query.data == "no":
        # User is hesitant or rejecting, ask why
        await ask_why_hesitant_or_reject_to_shoot_video(update, context)


def create_applicant_application(token: str) -> Application:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(feedback_about_watched_video, pattern="^(video_yes|video_no|video_not_seen)$"))
    application.add_handler(CallbackQueryHandler(feedback_to_shoot_video, pattern="^(yes|maybe|no)$"))
    application.add_handler(CallbackQueryHandler(feedback_why_hesitant_or_reject_to_shoot_video, pattern="^(reason_no_company|reason_no_awkward|reason_no_dont_know|reason_no_privacy|reason_no_other)$"))
    application.add_handler(MessageHandler(filters.ALL & (filters.VIDEO | filters.VIDEO_NOTE | filters.Document.VIDEO), lambda update, context: handle_video(update, context, ask_to_confirm_sending)))
    application.add_handler(CallbackQueryHandler(privacy_policy_confirmation, pattern="^confirm_yes_privacy$"))
    application.add_handler(CallbackQueryHandler(feedback_to_confirm_sending, pattern="^confirm_no$"))
    application.add_handler(CallbackQueryHandler(feedback_privacy_confirmation, pattern="^(privacy_confirm_yes|privacy_confirm_no)$"))
    return application


