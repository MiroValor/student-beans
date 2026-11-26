from datetime import datetime

import discord
from discord.ext import commands

import icloud
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
    if isinstance(error, commands.NotOwner):
        await ctx.author.send("⛔ Only the bot's owner can use that command.")
    elif isinstance(error, commands.CheckFailure):
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
        # Providers are shared instances, so restore the default after this run.
        default_headless = provider.headless
        if use_headed:
            provider.headless = False
        try:
            codes = await provider.fetch_codes(email, password)
        except Exception as e:
            codes = f"❌ Error: {e}"
        finally:
            provider.headless = default_headless
        await ctx.author.send(f"**{provider.name.title()} codes:**\n{codes}")


@bot.command(name="hme")
@is_dm()
@commands.is_owner()
async def hide_my_email(ctx, *, label: str = None):
    """Create a new iCloud+ Hide My Email address. Usage: !hme [label]"""
    label = (label or f"Discord bot {datetime.now():%Y-%m-%d %H:%M}").strip()[:100]
    await ctx.author.send("🔄 Creating a Hide My Email address...")
    try:
        email = await icloud.create_hide_my_email(label)
    except icloud.ICloudError as e:
        await ctx.author.send(f"❌ {e}")
        return
    except Exception as e:
        print(f"Hide My Email error: {e!r}")
        await ctx.author.send(f"❌ Something went wrong creating the address: {e}")
        return
    await ctx.author.send(f"✅ New Hide My Email (label: **{label}**):\n`{email}`")


@bot.command(name="icloudlogin")
@is_dm()
@commands.is_owner()
async def icloud_login(ctx):
    """Save an iCloud session. Attach icloud_session.json from icloud_login.py."""
    if not ctx.message.attachments:
        await ctx.author.send(
            "📎 Attach the `icloud_session.json` file made by `python icloud_login.py` "
            "to the same message as `!icloudlogin`."
        )
        return
    attachment = ctx.message.attachments[0]
    if attachment.size > 1_000_000:
        await ctx.author.send("❌ That file is too big to be a session file.")
        return
    try:
        icloud.save_session(await attachment.read())
    except icloud.ICloudError as e:
        await ctx.author.send(f"❌ {e}")
        return
    await ctx.author.send(
        "✅ iCloud sign-in saved. Try `!hme` now.\n"
        "Delete your message with the file (and the file on your Mac) — it gives access to your iCloud account."
    )


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
    embed.add_field(
        name="!hme [label]",
        value="Create a new iCloud+ Hide My Email address (owner only)",
        inline=False,
    )
    embed.add_field(
        name="!icloudlogin + file",
        value="Save the iCloud sign-in from icloud_login.py (owner only)",
        inline=False,
    )
    await ctx.author.send(embed=embed)


bot.run(DISCORD_TOKEN)
