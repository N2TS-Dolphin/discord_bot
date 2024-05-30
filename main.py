import os

import discord
import yt_dlp

from discord.ext import commands
from dotenv import load_dotenv

# Lấy Token từ .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('GUILD_ID')

# Cài đặt prefix cho bot
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

songinfo = []


# Khởi tạo
@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    
    print(
        f'{bot.user} has connected to Discord!\n'
        f'Guild: {guild.name} (id: {guild.id})'
    )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content == 'ping':
        await message.channel.send('pong')
    if message.content == 'hello':
        await message.channel.send(f'Hello {message.author}')

    await bot.process_commands(message)

# Each member join my server
@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )

# Bot join voice channel
@bot.command(pass_context = True)
async def join(ctx):
    if (ctx.author.voice):
        voice_channel = ctx.message.author.voice.channel
        await voice_channel.connect()
    else:
        await ctx.send("Bạn chưa tham gia bất kỳ kênh thoại nào")

# Bot leave voice channel
@bot.command(pass_context = True)
async def leave(ctx):
    if(ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Tôi đã rời khỏi kênh thoại")
    else:
        await ctx.send("Tôi không trong bất kỳ kênh thoại nào")

# Bot play a song in voice channel
@bot.command(pass_context=True)
async def play(ctx, url):
    # Kiểm tra URL hợp lệ
    if not url.startswith("https://"):
        await ctx.send("URL không hợp lệ.")
        return

    # Đặt tên tệp cố định
    fixed_filename = "fixed_audio.webm"
    fixed_file_path = os.path.join(os.getcwd(), fixed_filename)
    try: 
        os.remove(fixed_file_path)
    except:
        pass

    # Tải video   
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": fixed_file_path,
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info or not info.get("formats"):
                await ctx.send("Tải thông tin video thất bại")
                return
            
            # Download the video
            ydl.download([url])
            
            # Phát nhạc
            voice_channel = ctx.message.author.voice.channel
            if voice_channel is None:
                await ctx.send("Bạn cần tham gia một kênh thoại trước.")
                return

            voice_client = await voice_channel.connect()
            source = discord.FFmpegPCMAudio(fixed_file_path)
            player = voice_client.play(source)

    except Exception as e:
        await ctx.send(f"Lỗi xảy ra: {e}")

@bot.command(pass_context = True)
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_playing():
        voice_client.pause()
    else:
        await ctx.send("Không có bài hát nào đang phát trong kênh thoại này")

@bot.command(pass_context = True)
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_paused():
        voice_client.resume()
    else:
        await ctx.send("Không có bài hát nào đang tạm dừng")

@bot.command(pass_context = True)
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice_client.stop()

bot.run(TOKEN)