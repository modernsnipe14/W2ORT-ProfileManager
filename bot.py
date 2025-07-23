import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# ---------- CONFIG ----------
TOKEN = "YOUR BOT TOKEN HERE"
DEFAULT_FIELDS = ["Callsign", "Email", "Digital ID", "HoIP #"]

# ---------- DATABASE ----------
conn = sqlite3.connect('profiles.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS fields (
    guild_id INTEGER,
    name TEXT,
    UNIQUE(guild_id, name)
)''')
c.execute('''CREATE TABLE IF NOT EXISTS profiles (
    guild_id INTEGER,
    user_id INTEGER,
    field TEXT,
    value TEXT,
    UNIQUE(guild_id, user_id, field)
)''')
conn.commit()

# ---------- BOT ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()  # Global sync
        print(f"Synced {len(synced)} global commands")
    except Exception as e:
        print(e)

# Auto-add default fields when bot joins a server
@bot.event
async def on_guild_join(guild):
    for field in DEFAULT_FIELDS:
        try:
            c.execute("INSERT INTO fields (guild_id, name) VALUES (?, ?)", (guild.id, field))
        except sqlite3.IntegrityError:
            pass
    conn.commit()


# ---------- SLASH COMMANDS ----------
@bot.tree.command(name="profile_view", description="View your profile or another user's profile")
async def profile_view(interaction: discord.Interaction, user: discord.User = None):
    if user is None:
        user = interaction.user
    c.execute("SELECT field, value FROM profiles WHERE guild_id = ? AND user_id = ?", (interaction.guild.id, user.id))
    rows = c.fetchall()
    if not rows:
        await interaction.response.send_message(f"{user.display_name} has no profile set yet.", ephemeral=False)
        return

    embed = discord.Embed(title=f"{user.display_name}'s Profile", color=discord.Color.blue())
    for field, value in rows:
        embed.add_field(name=field, value=value if value else "Not set", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="profile_edit", description="Edit any user's profile interactively")
async def profile_edit(interaction: discord.Interaction, user: discord.User):
    # Fetch fields for this guild
    c.execute("SELECT name FROM fields WHERE guild_id = ?", (interaction.guild.id,))
    fields = [row[0] for row in c.fetchall()]

    if not fields:
        await interaction.response.send_message("⚠ No fields are set up yet.", ephemeral=True)
        return

    class FieldSelect(discord.ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=field) for field in fields]
            super().__init__(placeholder="Select a field to edit", options=options)

        async def callback(self, interaction_dropdown: discord.Interaction):
            selected_field = self.values[0]

            class EditModal(discord.ui.Modal, title=f"Edit {selected_field} for {user.display_name}"):
                value_input = discord.ui.TextInput(label="New Value", style=discord.TextStyle.short)

                async def on_submit(self, modal_interaction: discord.Interaction):
                    new_value = self.value_input.value
                    c.execute("""
                        INSERT INTO profiles (guild_id, user_id, field, value)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(guild_id, user_id, field) DO UPDATE SET value = excluded.value
                    """, (interaction.guild.id, user.id, selected_field, new_value))
                    conn.commit()
                    await modal_interaction.response.send_message(
                        f"✅ Updated `{selected_field}` for {user.display_name} to `{new_value}`", ephemeral=False
                    )

            await interaction_dropdown.response.send_modal(EditModal())

    view = discord.ui.View()
    view.add_item(FieldSelect())
    await interaction.response.send_message(f"Editing profile for {user.display_name}:", view=view, ephemeral=True)


# ---------- ADMIN COMMANDS ----------
@bot.tree.command(name="profile_addfield", description="Add a new profile field (Admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def profile_addfield(interaction: discord.Interaction, field_name: str):
    try:
        c.execute("INSERT INTO fields (guild_id, name) VALUES (?, ?)", (interaction.guild.id, field_name))
        conn.commit()
        await interaction.response.send_message(f"✅ Field `{field_name}` added.", ephemeral=True)
    except sqlite3.IntegrityError:
        await interaction.response.send_message("⚠ Field already exists.", ephemeral=True)


@bot.tree.command(name="profile_removefield", description="Remove a profile field (Admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def profile_removefield(interaction: discord.Interaction, field_name: str):
    c.execute("DELETE FROM fields WHERE guild_id = ? AND name = ?", (interaction.guild.id, field_name))
    c.execute("DELETE FROM profiles WHERE guild_id = ? AND field = ?", (interaction.guild.id, field_name))
    conn.commit()
    await interaction.response.send_message(f"❌ Field `{field_name}` removed.", ephemeral=True)


bot.run(TOKEN)
