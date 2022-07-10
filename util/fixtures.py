from textwrap import dedent

# This file contains constant values that are used throughout this REPL.

# Bot modes.
chat = "chat"
silence = "silence"

# The maximum amount of "memory" the bot will have for a given server's conversation.
max_history_length = 20

# GPT-3 configuration values depending on bot mode.
config = {
    chat: {
        "p1": "Human:",
        "p2": "AI:",
        "starter": "The following is a conversation with an AI assistant. The assistant's name is Geckobot. The assistant is witty, helpful, clever, and cynical.",
    },
}

# Description message when joining servers.
introduction = dedent(
    f"""
    It's nice to meet you, I'm a GPT-3 trained AI chatbot. I'll be your AI powered friend on this learning journey, I am a small demonstration of the recent developments in machine learning.
  
```Details of the project:
  You've all seen AI generated art but we chose to take the traditional route with our art. Our geckos have a rarity system that we'll reveal closer to the mint date. Our AI approach is focused greatly on the community and the roadmap of this project. The superior adaptation of geckos in nature will be the spirit of this project as we introduce new concepts and train our models to adapt.

1. We will be minting 2500 geckos on the Solana blockchain
2. The mint price is 2 SOL but is subject to  change should the value of Solana rise unexpectedly
3. There will never be more than 2500 geckos```

  I'll announce _the date of the mint_ when it's set (I promise)
    """
).strip()

# Help message
help_message = dedent(
    f"""
      
    :question: `/about`: Everything you need to know about me!
    :flashlight: `/status `: Allows you to switch my chat mode.

  *For devs:*
      :gear: `/engines `: displays all and any available Open AI engines. This is useful for debugging.
      :keyboard: `/complete <prompt>`: feeds in raw input. This can be helpful in case I act weird.
    """
).strip()

# Response when switching conversation modes
switch_replies = {
    chat: "*squeak* :lizard:",
    silence: "I think i'll go take a nap...zzzZZ",
}

# Default messaging history
initial_chat_exchange = ("Who are you?", "My name is Geckobot. I'm an AI bot made by The Gecko Project.")

# error message
generic_error_message = "Oops! Geckobot ran into an unknown error while handling your command."

# easter eggs
definitely_silent = {
    "gecko": "https://tenor.com/view/wink-gecko-smile-lizard-happy-gif-10796374",
    "solana": "https://tenor.com/view/solana-sol-crypto-cryptocurrency-blockchain-gif-19451701",
    "gm": "https://c.tenor.com/mqBOiPnIFKwAAAAC/music-good-times.gif",
}