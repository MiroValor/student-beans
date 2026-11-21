import discord
from discord.ext import commands
from config import DISCORD_TOKEN
from storage import CredentialStore
from providers import get_provider, list_providers

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
store = CredentialStore()


def is_dm():
    async def predicate(ctx):
        return isinstance(ctx.channel, discord.DMChannel)

    return commands.check(predicate)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.author.send("⚠️ Please use bot commands in a direct message for security.")
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
    else:
        print(f"Command error: {error}")


@bot.command(name="add")
@is_dm()
async def add_credential(ctx, service: str, email: str, password: str):
    """Save login credentials for a service. Usage: !add unidays email password"""
    provider = get_provider(service)
    if not provider:
        await ctx.author.send(
            f"❌ Unknown service `{service}`. Supported: {', '.join(list_providers())}"
        )
        return
    try:
        store.save_credential(ctx.author.id, service, email, password)
        await ctx.author.send(f"✅ Saved credentials for **{service}**.")
    except Exception as e:
        await ctx.author.send(f"❌ Failed to save credentials: {e}")


@bot.command(name="codes")
@is_dm()
async def get_codes(ctx, headed: str = None):
    """Fetch discount codes from all saved accounts.
    Usage: !codes          (headless browser)
           !codes headed   (visible browser — use to discover selectors / solve CAPTCHA)
    """
    creds = store.get_credentials(ctx.author.id)
    if not creds:
        await ctx.author.send(
            "📭 No credentials saved. Use `!add <service> <email> <password>` to add an account."
        )
        return

    use_headed = (headed or "").lower() in ("headed", "headless=false", "visible")
    await ctx.author.send(
        f"🔄 Fetching codes... (headed browser: {use_headed}) — this may take a moment."
    )
    for service, (email, password) in creds.items():
        provider = get_provider(service)
        # Recreate provider with the right headless setting so we can toggle per-run
        from providers import get_provider as _gp

        provider = _gp(service)
        provider.headless = not use_headed
        try:
            codes = await provider.fetch_codes(email, password)
        except Exception as e:
            codes = f"❌ Error: {e}"
        await ctx.author.send(f"**{provider.name.title()} codes:**\n{codes}")


@bot.command(name="remove")
@is_dm()
async def remove_credential(ctx, service: str):
    """Remove saved credentials for a service. Usage: !remove unidays"""
    if store.remove_credential(ctx.author.id, service):
        await ctx.author.send(f"🗑️ Removed credentials for **{service}**.")
    else:
        await ctx.author.send(f"❌ No credentials found for **{service}**.")


@bot.command(name="list")
@is_dm()
async def list_services(ctx):
    """List supported services."""
    await ctx.author.send(f"Supported services: {', '.join(list_providers())}")


@bot.command(name="help")
@is_dm()
async def help_cmd(ctx):
    """Show help."""
    embed = discord.Embed(
        title="Student Discount Bot",
        description="All commands must be sent in a direct message to the bot.",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="!add <service> <email> <password>",
        value="Save login credentials for a service",
        inline=False,
    )
    embed.add_field(
        name="!codes", value="Fetch discount codes from saved accounts", inline=False
    )
    embed.add_field(
        name="!remove <service>", value="Remove saved credentials", inline=False
    )
    embed.add_field(name="!list", value="List supported services", inline=False)
    await ctx.author.send(embed=embed)


bot.run(DISCORD_TOKEN)
