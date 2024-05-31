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

class Song:
    def __init__(self, url, title, file_path):
        self.url = url
        self.title = title
        self.file_path = file_path

song_queue = []
index = 0

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
    fixed_filename = f"audio_{len(song_queue)}.webm"
    fixed_file_path = os.path.join(os.getcwd(), fixed_filename)
    
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
                await ctx.send("Failed to extract video information.")
                return

            # Download the video
            ydl.download([url])
            song = Song(url, info['title'], fixed_file_path)
            song_queue.append(song)
            await ctx.send(f"Đã thêm vào hàng đợi: {info['title']}")

            # Phát nhạc nếu hàng đợi chỉ có 1 bài hát (không có bài nào đang phát)
            if len(song_queue) == 1:
                voice_client = ctx.voice_client
                if voice_client is None or not voice_client.is_playing():
                    await play_next_song(ctx)

    except Exception as e:
        await ctx.send(f"Lỗi xảy ra: {e}")

async def play_next_song(ctx):
    global index
    global song_queue

    if len(song_queue) == 0:
        return

    voice_channel = ctx.author.voice.channel
    if voice_channel is None:
        await ctx.send("Bạn cần tham gia một kênh thoại trước.")
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await voice_channel.connect()
    
    if index < len(song_queue):
        current_song = song_queue[index]
        audio_source = discord.FFmpegPCMAudio(current_song.file_path)
        await ctx.send(index)
        await ctx.send(len(song_queue))

        def after_playing(error):
            global index
            if error:
                print(f"Error occurred: {error}")
            else:
                try:
                    os.remove(current_song.file_path)
                except Exception as e:
                    print(f"Failed to delete file: {e}")
                index = index + 1
                if index < len(song_queue):
                    bot.loop.create_task(play_next_song(ctx))
                else:
                    index = 0
                    song_queue.clear()
                    if len(song_queue) > 0:
                        play_next_song(ctx)

        voice_client.play(audio_source, after=after_playing)
        

@bot.command(pass_context=True)
async def skip(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Đã bỏ qua bài hát hiện tại.")

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
