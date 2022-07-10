import logging
from collections import defaultdict
from textwrap import dedent

import openai
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
from openai.error import OpenAIError

from util import db, fixtures, gpt, locks


logger = logging.getLogger(__name__)

class Geckobot(commands.Bot):
    """The base class for Geckobot.
    
    Geckobot includes handlers for messaging and standard Discord events along with slash commands
    """
    def __init__(self, token=None, *args, **kwargs):
        super(Geckobot, self).__init__(command_prefix="/", *args, **kwargs)
        self.history = defaultdict(list)
        self.lock = locks.Lock()
        self._init_slash_commands()
   
    async def on_ready(self):
        logger.info("We have logged in as %s", self.user)
        db.set_last_init()

    async def on_guild_join(self, guild):
        """Handler for when the bot joins a Discord server."""
        logger.info("Joined guild: %d", guild.id)
        db.increment_guild_count()
        for channel in guild.text_channels:
            if channel.name == "general":
                await channel.send(fixtures.introduction)

    async def on_message(self, message):
        """Handler for when the bot receives a message."""
        if message.author == self.user:
            return

        guild_id = message.guild.id
        # If there's no OpenAI API key, don't enable chat features.
        if openai.api_key is None:
            db.switch_mode(guild_id, fixtures.silence)
        mode = db.get_mode(guild_id)

        # Geckobot won't say anything when silenced...or will he?
        if mode == fixtures.silence:
            for token, gif in fixtures.definitely_silent.items():
                if token in message.content:
                    await message.channel.send(gif)
                    return
            logger.debug("Bot is in silence mode. Skipping interaction in guild %d", guild_id)
            return

        if not self.lock.claim_lock(guild_id):
            logger.info("Guild %d currently holds a lock; ignoring new messages...", guild_id)
            return

        # Generate the parameters for GPT-3 completion.
        prompt = self._build_prompt(guild_id, message.content)
        config = fixtures.config[mode]
        try:
            response = gpt.complete(prompt, [config["p1"], config["p2"]])
            # Post-process the bot response before sending.
            if mode == fixtures.chat:
                self._update_history(guild_id, message.content, response)
            await message.channel.send(response)
        except OpenAIError as e:
            await message.channel.send(str(e))

        self.lock.release_lock(guild_id)

    def _update_history(self, guild_id: int, opener: str, response: str):
        """This updates the AI chat history in the server. If there is degraded performance, the recommended length is 10, but it's up to the user.
        """
        self.history[guild_id].append((opener, response))
        if len(self.history[guild_id]) > fixtures.max_history_length:
            self.history[guild_id].pop(0)

    def _build_prompt(self, guild_id: int, msg: str) -> str:
        """Builds a prompt template to feed to GPT-3.
        """
        mode = db.get_mode(guild_id)
        config = fixtures.config[mode]
        p1 = config["p1"]
        p2 = config["p2"]

        # Fetches chat history from memory.
        history = []
        if mode == fixtures.chat:
            if guild_id not in self.history:
                opener, response = fixtures.initial_chat_exchange
                self._update_history(guild_id, opener, response)
            history = self.history[guild_id]

        # Constructs the final prompt.
        prompt = "" if "starter" not in config else config["starter"] + "\n"
        for (opener, response) in history:
            prompt = prompt + dedent(
                f"""
                {p1} {opener}
                {p2} {response}
                """
            ).rstrip()
        return prompt + dedent(
            f"""
            {p1} {msg}
            {p2}
            """
        ).rstrip()

    def _init_slash_commands(self):
        """Initializes all slash commands for this bot."""
        cmd = SlashCommand(self, sync_commands=True)
       
        @cmd.slash(
            name="help",
            description="Help and details",
        )
        async def _help(ctx):
            """Displays the help message"""
            await ctx.send(fixtures.help_message)

        @cmd.slash(
            name="about",
            description="Shows general information",
        )
        async def _about(ctx):
            """Displays general info"""
            await ctx.send(fixtures.introduction)

        @cmd.slash(
            name="status",
            description="Current status",
        )
        async def _status(ctx):
            """Displays the bot's chat mode"""
            latency = round(self.latency * 1000, 3)
            timestamp = db.get_last_init()
            mode = db.get_mode(ctx.guild.id)
            statuses = [
                f"- I received your ping in {latency} ms.",
                f"- My current build was initialized on {timestamp} UTC.",
                f"- Right now I'm in `{mode}` mode.",
            ]
            if openai.api_key is not None:
                statuses.append("- I have an OpenAI API key. ✅")
            else:
                statuses.append("- I am missing an OpenAI API key. ❌")
            await ctx.send("\n".join(statuses))

        @cmd.slash(
            name="switch",
            description="Change the bot interaction mode.",
            options=[
                create_option(
                    name="mode",
                    description="How you'd like the bot to act.",
                    option_type=3,
                    required=True,
                    choices=[
                        create_choice(
                            name="Conversation Mode",
                            value=fixtures.chat,
                        ),
                        create_choice(
                            name="Silence the bot for now",
                            value=fixtures.silence,
                        ),
                    ],
                ),
            ],
        )
        async def _switch(ctx, mode: str):
            """Changes the bot's chatmode to the user's choice."""
            db.switch_mode(ctx.guild.id, mode)
            await ctx.send(fixtures.switch_replies[mode])
    
        @cmd.slash(
            name="engines",
            description="List available GPT-3 engines.",
        )
        async def _engines(ctx):
            """Lists all of the available GPT-3 engines.
            """
            await ctx.defer()
            try:
                engines = gpt.engines()
                msg = "The following GPT-3 engines are available:\n"
                msg += "\n".join(map(lambda engine: f"- `{engine}`", engines))
                await ctx.send(msg)
            except OpenAIError as e:
                await ctx.send(str(e))
    
        @cmd.slash(
            name="complete",
            description="Send raw input into GPT-3",
            options=[
                create_option(
                    name="prompt",
                    description="A raw prompt to feed into GPT-3. Must wrap in quotes.",
                    option_type=3,
                    required=True,
                ),
            ],
        )
        async def _complete(ctx, prompt: str):
            """Feeds raw input into GPT-3
            """
            await ctx.defer()
            try:
                res = gpt.complete(prompt, max_tokens=50)
                await ctx.send(f"**{prompt[1:-1]}** {res}")
            except OpenAIError as e:
                await ctx.send(str(e))
  