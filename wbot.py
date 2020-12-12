import discord
import asyncio
import logging
import cv2
from discord.ext import commands, tasks
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tinydb import TinyDB, Query

db = TinyDB("wbdb.json")
channel_query = Query()

bot = commands.Bot(command_prefix="!")
bot.remove_command("help")


async def get_sec(time_str):
    h, m, s = time_str.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


@bot.command()
async def pingme(ctx):
    res = db.search(channel_query.user == ctx.author.id)
    if len(res) == 0:
        db.insert({"user": ctx.author.id, "user_channel": ctx.channel.id})
        await ctx.channel.send("<@" + str(ctx.author.id) + "> k")
    else:
        await ctx.channel.send("no")


@bot.command()
async def dontping(ctx):
    res = db.search(channel_query.user == ctx.author.id)
    if len(res) > 0:
        for item in db:
            if "channel" in item:
                channel = bot.get_channel(item["channel"])
                continue
            db.remove(channel_query.user == ctx.author.id)
            await ctx.channel.send("<@" + str(ctx.author.id) + "> k, no more pinging")
    else:
        await ctx.channel.send("no")


@bot.command()
async def posthere(ctx):
    if ctx.author.id == 114881658045464581:
        res = db.search(channel_query.channel == ctx.channel.id)
        if len(res) == 0:
            db.insert({"channel": ctx.message.channel.id})
        else:
            await ctx.channel.send("This channel already registered.")


@bot.command()
async def sauce(ctx):
    await ctx.channel.send("https://github.com/bucksgen/AK-World-Boss-Pinger")


@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="AK WB Pinger",
        description="This bot will ping you 5 minute before world boss spawn. Use !pingme command to make the bot ping you and !dontping to stop. Developed by <@114881658045464581>",
        color=0x9D2CA7,
    )
    await ctx.channel.send(embed=embed)


async def on_ready():
    await bot.change_presence(activity=discord.Game(name="!help"))


@tasks.loop(seconds=5)
async def scan_spreadsheet():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    SAMPLE_SPREADSHEET_ID = "tUL0-Nn3Jx7e6uX3k4_yifQ"
    SAMPLE_RANGE_NAME = "C10"

    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])
    seconds = await get_sec(values[0][0])
    print(seconds)
    if seconds < 310 or (seconds > 72000 and seconds < 72310):
        text = ""
        channel = 0
        res = len(db)
        if res > 0:
            for item in db:
                if "channel" in item:
                    channel = bot.get_channel(item["channel"])
                    continue
                text = text + "<@" + str(item["user"]) + "> "
            await channel.send(text + "WB in 5 min")
        print("waited")
        await asyncio.sleep(5400)


@scan_spreadsheet.before_loop
async def scan_spreadsheet_before():
    await bot.wait_until_ready()
    game = discord.Game("!help !sauce")
    await bot.change_presence(status=discord.Status.idle, activity=game)


scan_spreadsheet.start()
bot.run("YOUR BOT TOKEN HERE")
