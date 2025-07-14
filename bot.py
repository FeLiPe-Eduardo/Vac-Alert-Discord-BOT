from dotenv import load_dotenv
load_dotenv()

import discord
from discord.ext import commands, tasks
import sqlite3
import requests
import os
import asyncio

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
CHECK_INTERVAL = 12 * 60 * 60  # 12 horas

intents = discord.Intents.default()
intents.message_content = True  # Necessário para capturar comandos com conteúdo
bot = commands.Bot(command_prefix="/", intents=intents)

os.makedirs("db", exist_ok=True)
conn = sqlite3.connect("db/steam_vac.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitored_accounts (
        user_id INTEGER,
        steam_id TEXT,
        PRIMARY KEY (user_id, steam_id)
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id INTEGER PRIMARY KEY,
        channel_id INTEGER
    )
""")
conn.commit()

def check_vac_status(steam_id):
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={STEAM_API_KEY}&steamids={steam_id}"
    response = requests.get(url).json()
    if "players" in response and response["players"]:
        return response["players"][0]["VACBanned"]
    return None

@bot.command()
async def adicionar(ctx, steam_id: str):
    cursor.execute("INSERT OR IGNORE INTO monitored_accounts (user_id, steam_id) VALUES (?, ?)", (ctx.author.id, steam_id))
    conn.commit()
    await ctx.send(f"Steam ID {steam_id} adicionado para monitoramento.")

@bot.command()
async def remover(ctx, steam_id: str):
    cursor.execute("DELETE FROM monitored_accounts WHERE user_id = ? AND steam_id = ?", (ctx.author.id, steam_id))
    conn.commit()
    await ctx.send(f"Steam ID {steam_id} removido do monitoramento.")

@bot.command()
async def listar(ctx):
    cursor.execute("SELECT steam_id FROM monitored_accounts WHERE user_id = ?", (ctx.author.id,))
    accounts = cursor.fetchall()
    if accounts:
        await ctx.send("IDs monitorados:\n" + "\n".join([a[0] for a in accounts]))
    else:
        await ctx.send("Você não tem nenhuma conta monitorada.")

@bot.command()
async def verificar(ctx):
    cursor.execute("SELECT steam_id FROM monitored_accounts WHERE user_id = ?", (ctx.author.id,))
    accounts = cursor.fetchall()
    if not accounts:
        await ctx.send("Você não tem nenhuma conta monitorada.")
        return
    msg = "Status VAC:\n"
    for account in accounts:
        vac_status = check_vac_status(account[0])
        msg += f"Steam ID {account[0]}: {'BANIDO' if vac_status else 'LIMPO'}\n"
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def definircanal(ctx):
    guild_id = ctx.guild.id
    canal_id = ctx.channel.id
    cursor.execute("REPLACE INTO guild_settings (guild_id, channel_id) VALUES (?, ?)", (guild_id, canal_id))
    conn.commit()
    await ctx.send(f"Canal de notificações automáticas definido para: {ctx.channel.mention}")

@tasks.loop(seconds=CHECK_INTERVAL)
async def verificar_automaticamente():
    cursor.execute("SELECT DISTINCT steam_id FROM monitored_accounts")
    accounts = cursor.fetchall()
    if not accounts:
        return
    cursor.execute("SELECT guild_id, channel_id FROM guild_settings")
    guilds = cursor.fetchall()
    for guild_id, canal_id in guilds:
        channel = bot.get_channel(int(canal_id))
        if not channel:
            continue
        msg = "Status VAC Atualizado:\n"
        for account in accounts:
            vac_status = check_vac_status(account[0])
            msg += f"Steam ID {account[0]}: {'BANIDO' if vac_status else 'LIMPO'}\n"
        try:
            await channel.send(msg)
        except:
            continue

@bot.event
async def on_ready():
    verificar_automaticamente.start()
    print(f"{bot.user.name} está online!")

bot.run(TOKEN)
