from telegram.ext import Application
from telegram.request import HTTPXRequest
import asyncio
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def main():
    """Start the bot."""
    # Create the Application with custom request parameters
    application = Application.builder().token('7128344175:AAEWx_s4vGHYPCPqF0T6BKoYqVWa0vKRerY').request(
        HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
        )
    ).build()

    try:
        print("Starting bot...")
        await application.initialize()
        print("Bot initialized successfully!")
        me = await application.bot.get_me()
        print(f"Bot information: {me}")
        await application.stop()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(main()) 