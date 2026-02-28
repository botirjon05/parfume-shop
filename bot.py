"""
🌸 Parfume Center — Telegram Bot
Handles /start and admin order status callbacks.
Orders themselves are sent directly from the Mini App
to Telegram's API — no server needed.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
)

# ── CONFIG ────────────────────────────────────────────────────────
BOT_TOKEN = "8045542724:AAGcakq1YxNSxdCB1aw0Lln1BPKymIHUWjA"   # from @BotFather
ADMIN_IDS = [887340351]             # your Telegram user ID (integer)
SHOP_NAME = "Parfume Center"
WEBAPP_URL = "https://botirjon05.github.io/parfume-shop/"
# ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)

dp = Dispatcher()


def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            text="🛍 Open Shop",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]],
        resize_keyboard=True,
    )


@dp.message(CommandStart())
async def on_start(message: Message):
    await message.answer(
        f"👋 Welcome to <b>{SHOP_NAME}</b>!\n\n"
        "Tap the button below to browse our collection "
        "and place an order — all inside Telegram. 🌸",
        reply_markup=main_kb(),
    )


@dp.callback_query(F.data.startswith("st:"))
async def on_status(callback: CallbackQuery, bot: Bot):
    """Admin taps Confirm / Shipped / Delivered / Cancel."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Not authorised", show_alert=True)
        return

    try:
        _, cid, status = callback.data.split(":")
        customer_id = int(cid)
    except ValueError:
        await callback.answer("Bad data")
        return

    msgs = {
        "confirmed": "✅ Your order has been <b>confirmed</b>! We're preparing it.",
        "shipped":   "🚚 Your order is <b>on its way</b>!",
        "completed": f"🎉 Delivered! Thank you for shopping at <b>{SHOP_NAME}</b> 🌸",
        "cancelled": "❌ Your order was <b>cancelled</b>. Please contact us for help.",
    }
    text = msgs.get(status, f"Order status: {status}")

    try:
        await bot.send_message(customer_id, text)
        await callback.answer(f"Customer notified ✓")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(f"Status → <b>{status}</b>")
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)


async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.info(f"🌸 {SHOP_NAME} starting…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
