from  nextcord.ext import commands,tasks
from nextcord import FFmpegPCMAudio, FFmpegAudio, FFmpegOpusAudio
from get_youtube import give_link,download_vid,find_music_name,remove_all_files, delete_selected_file
import asyncio
import nextcord
from time import sleep
import os
from dotenv import load_dotenv

#This is the main file

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
intents = nextcord.Intents.all() #allowing all intents
intents.members = True

# os.environ["PATH"] += os.pathsep + r"C:\Users\Olivier\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-essentials_build/bin" 
bot = commands.Bot(command_prefix = "!",help_command=None,intents = intents) #Creating our bot
queue = []
is_playing = False
voice_client = None


@bot.command(name="play")
async def play(ctx, *, url):
    global is_playing, voice_client

    # 1. Download the video
    title = download_vid(url)  # e.g., returns "song.mp3"
    song_path = os.path.join("music", title)
    queue.append((ctx.guild.id, song_path))

    await ctx.send(f"✅ Added to queue: `{title}`")

    # 2. If already playing, return — the queue will handle it
    if is_playing:
        return

    # 3. Connect if not already connected
    if ctx.author.voice:
        if not ctx.voice_client:
            voice_client = await ctx.author.voice.channel.connect()
        else:
            voice_client = ctx.voice_client
    else:
        await ctx.send("❌ You must be in a voice channel.")
        return

    # 4. Start the queue loop
    await play_next(ctx)


async def play_next(ctx):
    global is_playing, voice_client

    while queue:
        is_playing = True
        guild_id, song = queue[0]

        try:
            audio = FFmpegPCMAudio(song)
            voice_client.play(audio)
            await ctx.send(f"🎵 Now playing: `{os.path.basename(song)}` song 1 of {len(queue)}")

            while voice_client.is_playing() or voice_client.is_paused():
                await asyncio.sleep(1)

        except Exception as e:
            await ctx.send(f"❌ Playback error: {e}")

        queue.pop(0)

    # Cleanup
    is_playing = False
    await voice_client.disconnect()
    remove_all_files("music")
    voice_client = None

@bot.command()
async def clear(ctx):
    global queue

    if queue:
        queue.clear()
        await ctx.send("🧹 Cleared the queue. The current song will continue playing.")
    else:
        await ctx.send("ℹ️ The queue is already empty.")

@bot.command()
async def skip(ctx):
    global voice_client, is_playing

    vc = ctx.voice_client

    if vc and vc.is_playing():
        vc.stop()  # This triggers the `after` callback or lets play_next() continue
        await ctx.send("⏭️ Skipping current track...")
    else:
        await ctx.send("❌ Nothing is playing right now.")


@bot.event
async def on_ready():  
    try: # If bot can connect to the discord

        print('Discord bot succesfully connected')
        print(f"{bot.user} is Ready")
    except:
        print("[!] Couldn't connect, an Error occured")


@bot.command()
async def pause(ctx):
    global queue, is_playing, voice_client

    vc = ctx.voice_client

    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("⏸️ Paused playback. I'll disconnect in 1 minute if not resumed.")

        # Start a 60s timeout
        waited = 0
        timeout = 60
        while waited < timeout:
            if vc.is_playing():  # resumed
                return
            await asyncio.sleep(5)
            waited += 5

        # Timeout reached: clear and disconnect
        if not vc.is_playing():
            queue.clear()
            is_playing = False
            await vc.disconnect()
            await ctx.send("👋 Disconnected due to inactivity while paused.")
            voice_client = None
            remove_all_files("music")

    else:
        await ctx.send("❌ Nothing is currently playing.")


@bot.command()
async def resume(ctx):
    vc = ctx.voice_client

    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("▶️ Resumed playback.")
    else:
        await ctx.send("❌ Nothing is paused.")


@bot.command()
async def leave(ctx): 
    if ctx.voice_client: #if you are in vc 
        await ctx.guild.voice_client.disconnect() #disconnecting from the vc
        await ctx.send("Lefted the voice channel") #sending confirmation on channel
        sleep(1)
        remove_all_files("music") #deleting the all the files in the folder that  we downloaded to not waste space on your pc

    else:
        await ctx.send("[-] An Error occured: You have to be in a voice channel to run this command") #if you are not in vc

@bot.command()
async def join(context):
    if context.author.voice:
        channel = context.message.author.voice.channel
        try:

             await channel.connect() #connecting to channel
        except:
            await context.send("[-] An error occured: Couldn't connect to the channel") #if there is an error

    else:
        await context.send("[-] An Error occured: You have to be in a voice channel to run this command") #if you are not in vc


@bot.command(name="test")
async def testplay(ctx):
    if ctx.author.voice:
        vc = await ctx.author.voice.channel.connect()
        audio_file = os.path.join("music", "Curicó.mp3")  # Use a known-good MP3 or WAV file
        vc.play(FFmpegPCMAudio(audio_file))
        await ctx.send("Playing test audio.")

        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
    else:
        await ctx.send("You're not in a voice channel.")


bot.run(TOKEN)