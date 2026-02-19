import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import API_TOKEN
from downloader import download_media, search_yt, identify_music
from database import db

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
store = {}


# =========================
# START
# =========================
@dp.message(CommandStart())
async def start(m: types.Message):
    db.add_user(m.from_user.id, m.from_user.username)
    await m.answer("👋 **Salom! Men Jack!**\n\n🔍 Musiqa nomini yozing yoki video link yuboring.")


# =========================
# LINK KELGANDA (Video + Shazam tugmasi)
# =========================
@dp.message(F.text.startswith("http"))
async def handle_link(m: types.Message):
    user_id = m.from_user.id
    url = m.text.strip()
    store[user_id] = url

    # 🔥 Agar YouTube bo‘lsa
    if "youtube.com" in url or "youtu.be" in url:
        from downloader import get_yt_info
        info = await get_yt_info(url)

        kb = InlineKeyboardBuilder()
        kb.row(
            types.InlineKeyboardButton(text="🎬 1080p", callback_data="yt_1080"),
            types.InlineKeyboardButton(text="🎬 720p", callback_data="yt_720"),
        )
        kb.row(
            types.InlineKeyboardButton(text="🎬 480p", callback_data="yt_480"),
            types.InlineKeyboardButton(text="🎵 MP3", callback_data="yt_mp3"),
        )

        await m.answer_photo(
            info["thumbnail"],
            caption=f"🎬 {info['title']}\n⏱ {info.get('duration_string','')}\n\n📥 Formatni tanlang:",
            reply_markup=kb.as_markup()
        )
        return

    # 🔥 Boshqa platformalar — to‘g‘ridan yuklaydi
    wait = await m.answer("🚀 Yuklanmoqda...")
    try:
        path = await download_media(url, mode="video")
        await m.answer_video(types.FSInputFile(path))
        if os.path.exists(path): os.remove(path)
    except:
        await m.answer("❌ Yuklashda xato.")
    finally:
        await wait.delete()



# =========================
# SHAZAM TUGMASI (Video ostidagi)
# =========================
@dp.callback_query(F.data == "do_shazam")
async def shazam_callback(call: types.CallbackQuery):
    url = store.get(call.from_user.id)
    if not url:
        return await call.answer("❌ Ma'lumot topilmadi", show_alert=True)

    await call.answer("🔍 Musiqa aniqlanmoqda...")
    try:
        # Shazam uchun audioni yuklash
        path = await download_media(url, mode="audio")
        result = await identify_music(path)
        if os.path.exists(path): os.remove(path)

        if result:
            query = f"{result['artist']} - {result['title']}"
            await call.message.reply(f"🔍 **Shazam natijasi:**\n\n🎵 {query}")
            # Topilgan musiqa bo'yicha qidiruv natijalarini chiqarish
            await send_search_results(call.message, query)
        else:
            await call.message.answer("😔 Musiqa topilmadi.")
    except:
        await call.message.answer("❌ Shazam xizmatida xatolik.")


# =========================
# QIDIRUV NATIJALARI (1-10 TUGMALAR)
# =========================
async def send_search_results(message, query):
    wait = await message.answer("🔎 Qidirilmoqda...")
    try:
        results = await search_yt(query)
        store[f"s_{message.chat.id}"] = results

        kb = InlineKeyboardBuilder()
        text = "🔍 **Topilgan natijalar:**\n\n"

        # 10 ta natijani chiqarish
        for i, res in enumerate(results[:10], 1):
            text += f"{i}. {res['title'][:45]}... [{res.get('duration_string', '')}]\n"
            kb.add(types.InlineKeyboardButton(text=str(i), callback_data=f"pick_{i - 1}"))

        kb.adjust(5)  # 1-5 va 6-10 qilib teradi
        kb.row(types.InlineKeyboardButton(text="❌ Yopish", callback_data="close"))

        await message.answer(text, reply_markup=kb.as_markup())
    except:
        await message.answer("❌ Qidiruvda xato.")
    finally:
        await wait.delete()


# =========================
# RO'YXATDAN TANLASH (XABAR O'CHMAYDI)
# =========================
@dp.callback_query(F.data.startswith("pick_"))
async def pick_music(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    results = store.get(f"s_{call.message.chat.id}")

    if not results:
        return await call.answer("❌ Ro'yxat eskirgan", show_alert=True)

    await call.answer(f"🎧 Yuklanmoqda...")
    try:
        path = await download_media(results[idx]['webpage_url'], mode="audio")
        await call.message.answer_audio(types.FSInputFile(path))

        # call.message.delete() YO'Q - ro'yxat turadi, boshqasini tanlash mumkin
        if os.path.exists(path): os.remove(path)
    except:
        await call.message.answer("❌ Yuklashda xato.")


# =========================
# QIDIRUV (Oddiy tekst)
# =========================
@dp.message(F.text)
async def handle_text(m: types.Message):
    await send_search_results(m, m.text)


# =========================
# BOSHQALAR
# =========================
@dp.callback_query(F.data == "get_mp3")
async def get_mp3_callback(call: types.CallbackQuery):
    url = store.get(call.from_user.id)
    await call.answer("🎵 MP3 tayyorlanmoqda...")
    path = await download_media(url, mode="audio")
    await call.message.answer_audio(types.FSInputFile(path))
    if os.path.exists(path): os.remove(path)


@dp.callback_query(F.data == "close")
async def close_callback(call: types.CallbackQuery):
    await call.message.delete()


@dp.callback_query(F.data.startswith("yt_"))
async def yt_download(call: types.CallbackQuery):
    url = store.get(call.from_user.id)
    if not url:
        return await call.answer("❌ Link topilmadi", show_alert=True)

    quality = call.data.split("_")[1]

    await call.answer("🚀 Yuklanmoqda...")

    try:
        if quality == "mp3":
            path = await download_media(url, mode="audio")
            await call.message.answer_audio(types.FSInputFile(path))
        else:
            path = await download_media(url, mode="video", quality=quality)
            await call.message.answer_video(types.FSInputFile(path))

        if os.path.exists(path): os.remove(path)

    except:
        await call.message.answer("❌ Yuklashda xato.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())