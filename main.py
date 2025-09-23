import asyncio
import os
from pathlib import Path

from applicant_bot import create_applicant_application


def ensure_directories() -> None:
    """Ensure required directories exist"""
    Path("applicant_video").mkdir(exist_ok=True)
    Path("manager_video").mkdir(exist_ok=True)


async def run_applicant_bot() -> None:
    """Run the applicant bot"""
    applicant_token = os.getenv("TELEGRAM_APPLICANT_BOT_TOKEN_v2")
    if not applicant_token:
        raise RuntimeError("TELEGRAM_APPLICANT_BOT_TOKEN_v2 not found in environment variables")
    application = create_applicant_application(applicant_token)
    # Initialize and start the application
    await application.initialize()
    await application.start()
    try:
        # Start polling
        await application.updater.start_polling()
        await asyncio.Event().wait()
    finally:
        await application.stop()
        await application.shutdown()


def main():
    """Main entry point"""
    print("Telegram Bot for Candidates is running")
    # Ensure required directories exist
    ensure_directories()
    # Run the applicant bot (validation happens inside the bot)
    asyncio.run(run_applicant_bot())


if __name__ == "__main__":
    main()
