import logging
import os
import sys
from textwrap import dedent

import openai

from bot import Geckobot
from util import fixtures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("Welcome! You are running Geckobot, the AI Discord bot!")

    # Fetch the Discord bot token.
    token = os.getenv("TOKEN")
    if token is None:
        logger.error("Missing bot token!")
        print(
            dedent(
                f"""
                Please provide a discord bot token from the discord dev portal."""
            )
        )
        sys.exit(1)

    # Load the OpenAI API key.
    # Unlike the bot token, the OpenAI API key is a soft dependency.
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if openai.api_key is None:
        logger.warning("Missing OpenAI API key!")
        print("Geckobot did not receive an OpenAI API key.")

    # Instantiate and run the bot.
    bot = Geckobot(token)
    bot.run(token)
  
if __name__ == "__main__":
    main()
