"""
🌸 Parfume Center — Telegram Bot
Handles:
  • /start              — welcome + shop button
  • PRODUCTS_UPDATE:... — admin pushes product list → bot writes to GitHub
  • st:<uid>:<status>   — admin taps order status buttons
"""
import asyncio
import base64
import json
import logging

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
)

# ══════════════════════════════════════════════════
#  CONFIG  — fill these in
# ══════════════════════════════════════════════════
BOT_TOKEN  = "8045542724:AAGcakq1YxNSxdCB1aw0Lln1BPKymIHUWjA"
ADMIN_IDS  = [887340351]           # your Telegram user ID (integer)
SHOP_NAME  = "Parfume Center"
WEBAPP_URL = "https://botirjon05.github.io/parfume-shop/"

# GitHub — token stored ONLY here on the server, never in the browser
GH_TOKEN   = "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"   # github.com → Settings → Developer settings
GH_USER    = "botirjon05"               # your GitHub username
GH_REPO    = "parfume-shop"             # repository name
GH_FILE    = "products.json"            # file path in repo
# ══════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)

dp = Dispatcher()


def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            text="🛍 Do'konni ochish",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )]],
        resize_keyboard=True,
    )


# ── /start ────────────────────────────────────────
@dp.message(CommandStart())
async def on_start(message: Message):
    await message.answer(
        f"👋 <b>{SHOP_NAME}</b>ga xush kelibsiz!\n\n"
        "Quyidagi tugmani bosib atirlarimizni ko'ring va buyurtma bering 🌸",
        reply_markup=main_kb(),
    )


# ── PRODUCTS_UPDATE — admin saves product list ────
@dp.message(F.text.startswith("PRODUCTS_UPDATE:"))
async def on_products_update(message: Message, bot: Bot):
    """Mini App sends full product JSON. Bot writes it to GitHub."""
    if message.from_user.id not in ADMIN_IDS:
        return  # silently ignore non-admins

    # Delete the raw JSON message from chat so it stays clean
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

    raw = message.text[len("PRODUCTS_UPDATE:"):]
    try:
        products = json.loads(raw)
    except json.JSONDecodeError as e:
        await bot.send_message(message.chat.id, f"PRODUCTS_ERR:JSON xatosi: {e}")
        return

    try:
        await github_put(products)
        await bot.send_message(message.chat.id, "PRODUCTS_OK")
        logging.info(f"✅ products.json updated ({len(products)} items) by {message.from_user.id}")
    except Exception as e:
        logging.error(f"GitHub push failed: {e}")
        await bot.send_message(message.chat.id, f"PRODUCTS_ERR:{e}")


async def github_put(products: list):
    """Write products.json to GitHub via API."""
    url = f"https://api.github.com/repos/{GH_USER}/{GH_REPO}/contents/{GH_FILE}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    content_b64 = base64.b64encode(
        json.dumps(products, ensure_ascii=False, indent=2).encode()
    ).decode()

    async with aiohttp.ClientSession() as session:
        # Get current SHA (needed to update existing file)
        sha = None
        async with session.get(url, headers=headers) as r:
            if r.status == 200:
                data = await r.json()
                sha = data.get("sha")
            elif r.status != 404:
                text = await r.text()
                raise Exception(f"GET {r.status}: {text[:200]}")

        # PUT the new content
        body = {
            "message": "chore: update products via admin panel",
            "content": content_b64,
        }
        if sha:
            body["sha"] = sha

        async with session.put(url, headers=headers, json=body) as r:
            if r.status not in (200, 201):
                text = await r.text()
                raise Exception(f"PUT {r.status}: {text[:300]}")


# ── ORDER STATUS — admin taps inline buttons ──────
@dp.callback_query(F.data.startswith("st:"))
async def on_status(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return

    try:
        _, cid, status = callback.data.split(":")
        customer_id = int(cid)
    except ValueError:
        await callback.answer("Noto'g'ri ma'lumot")
        return

    msgs = {
        "confirmed": "✅ <b>Buyurtmangiz tasdiqlandi!</b>\n\nBuyurtmangiz tayyorlanmoqda va tez orada jo'natiladi 🌸",
        "shipped":   "🚚 <b>Buyurtmangiz yo'lga chiqdi!</b>\n\nTez orada manzilingizga yetkazib beriladi 📱",
        "completed": f"🎉 <b>Buyurtmangiz muvaffaqiyatli yetkazildi!</b>\n\n<b>{SHOP_NAME}</b>ni tanlaganingiz uchun rahmat 🌸",
        "cancelled": "❌ <b>Buyurtmangiz bekor qilindi.</b>\n\nSavollaringiz bo'lsa, biz bilan bog'laning.",
    }
    text = msgs.get(status, f"Status: {status}")

    try:
        await bot.send_message(customer_id, text)
        await callback.answer("Mijozga xabar yuborildi ✓")
        # Update admin message to show current status
        status_icons = {
            "confirmed": "✅ Tasdiqlandi",
            "shipped":   "🚚 Yetkazilmoqda",
            "completed": "🎉 Yetkazildi",
            "cancelled": "❌ Bekor qilindi",
        }
        try:
            orig = callback.message.text or ""
            import re
            orig = re.sub(r'\n\nStatus → .+', '', orig)
            await callback.message.edit_text(
                orig + f"\n\nStatus → <b>{status_icons.get(status, status)}</b>",
                reply_markup=callback.message.reply_markup,
            )
        except Exception:
            pass
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)


# ── MAIN ──────────────────────────────────────────
async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.info(f"🌸 {SHOP_NAME} bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())