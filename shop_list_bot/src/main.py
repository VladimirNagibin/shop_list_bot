"""Main entry point for the shop list bot application."""

import asyncio
import signal
import sys

from core.logger import logger
from core.settings import settings


async def main() -> None:
    """Main async entry point for the shop list bot."""
    logger.info("Starting shop list bot...")

    # Create an event for graceful shutdown
    shutdown_event = asyncio.Event()

    # Setup signal handlers for graceful shutdown
    def signal_handler() -> None:
        """Handle shutdown signals."""
        logger.info("Received shutdown signal")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # TODO: Initialize bot and start polling
        logger.info(f"Bot token loaded: {settings.BOT_TOKEN[:10]}...")
        logger.info("Bot is running. Press Ctrl+C to stop.")

        # Wait for shutdown event instead of using while loop
        await shutdown_event.wait()
        logger.info("Shutting down gracefully...")

    except asyncio.CancelledError:
        logger.info("Task was cancelled")
        raise
    except (OSError, RuntimeError) as e:
        logger.exception(f"Runtime or OS error occurred: {e}")
        raise
    finally:
        # Cleanup code can go here
        logger.info("Cleanup completed")


def run() -> None:
    """Run the bot application."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except (SystemExit, asyncio.CancelledError):
        # Эти исключения уже обрабатываются или являются частью нормального завершения
        raise
    except (RuntimeError, OSError, ValueError) as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    except Exception as e:
        # Оставляем как fallback для действительно неожиданных ошибок
        logger.exception(f"Unexpected fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
