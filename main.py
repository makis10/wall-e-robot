#!/usr/bin/env python3
"""
WallPi - A Wall-E inspired robot powered by Claude AI
Main entry point
"""

import sys
import signal
import logging
from src.robot import WallPiRobot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("wallpi.log")
    ]
)
logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Shutting down WallPi... Goodbye! 👋")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("🤖 WallPi starting up...")
    logger.info("Say 'Hey Walli' to wake me up!")

    robot = WallPiRobot()
    robot.run()


if __name__ == "__main__":
    main()