#Implementation of Bot connection to discord 

import os

import discord 
from discord.ext import commands

client = commands.Bot(command_prefix = '!')

@client.event
async def on_ready():
        print("Bot Is Ready")

@client.command()
async def hello(ctx):
        await ctx.send('Hello!') 


client.run('')