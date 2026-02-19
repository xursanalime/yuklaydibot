import asyncio
import os
from yt_dlp import YoutubeDL
from shazamio import Shazam


async def download_media(url, mode="video", quality="720"):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    async def get_yt_info(url):
        loop = asyncio.get_event_loop()

        def sync_info():
            with YoutubeDL({"quiet": True}) as ydl:
                return ydl.extract_info(url, download=False)

        return await loop.run_in_executor(None, sync_info)

    loop = asyncio.get_event_loop()

    # 🔥 YOUTUBE
    if "youtube.com" in url or "youtu.be" in url:

        if mode == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        else:
            ydl_opts = {
                # iPhone compatible
                "format": f"best[ext=mp4][height<={quality}]/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "merge_output_format": "mp4",
            }

    # 🔥 BOSHQA PLATFORMALAR
    else:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
        }

    def sync_download():
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit(".", 1)[0]
            return filename + (".mp3" if mode == "audio" else ".mp4")

    return await loop.run_in_executor(None, sync_download)


# 🔍 YOUTUBE QIDIRUV
async def search_yt(query):
    loop = asyncio.get_event_loop()

    def sync_search():
        with YoutubeDL(
            {"format": "bestaudio", "noplaylist": True, "quiet": True}
        ) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            return info["entries"]

    return await loop.run_in_executor(None, sync_search)


# 🎵 SHAZAM YANGILANGAN VERSIYA
async def identify_music(path):
    sh = Shazam()
    # recognize_song o'rniga recognize ishlatamiz
    out = await sh.recognize(path)

    if out and "track" in out:
        t = out["track"]
        return {
            "title": t["title"],
            "artist": t["subtitle"],
        }
    return None
# 🔎 YOUTUBE INFO (format tanlash uchun)
async def get_yt_info(url):
    loop = asyncio.get_event_loop()

    def sync_info():
        with YoutubeDL({"quiet": True}) as ydl:
            return ydl.extract_info(url, download=False)

    return await loop.run_in_executor(None, sync_info)
