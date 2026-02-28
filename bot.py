"""
🌸 Parfume Center — Telegram Mini App Bot

Architecture:
  Orders are sent directly from the Mini App (index.html) to the
  Telegram Bot API via fetch(). This bot only needs to:
  1. Show the /start welcome + Open Shop button
  2. Handle admin status callbacks (Confirm / Shipped / Delivered)

No HTTP server needed. Works for unlimited orders per session.
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

from config import BOT_TOKEN, ADMIN_IDS, SHOP_NAME, WEBAPP_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

dp = Dispatcher()


def shop_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛍 Open Shop", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Welcome to <b>{SHOP_NAME}</b>!\n\n"
        f"Tap the button below to browse our exclusive perfume collection "
        f"and place an order — all inside Telegram. 🌸",
        reply_markup=shop_keyboard(),
    )


@dp.callback_query(F.data.startswith("status:"))
async def update_order_status(callback: CallbackQuery, bot: Bot):
    """Admin taps Confirm / Shipped / Delivered / Cancel on an order notification."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    try:
        _, customer_id_str, status = callback.data.split(":")
        customer_id = int(customer_id_str)
    except ValueError:
        await callback.answer("Bad callback data")
        return

    status_messages = {
        "confirmed": "✅ Your order has been <b>confirmed</b>! We're preparing it.",
        "shipped":   "🚚 Your order is <b>on its way</b>!",
        "completed": f"🎉 Your order has been <b>delivered</b>! Thank you for shopping at {SHOP_NAME} 🌸",
        "cancelled": "❌ Your order has been <b>cancelled</b>. Please contact us if you have questions.",
    }

    customer_text = status_messages.get(status, f"Order status updated: {status}")

    try:
        await bot.send_message(customer_id, customer_text)
        await callback.answer(f"✅ Customer notified: {status}")
        # Remove buttons so the same order can't be double-actioned
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(f"Status set to <b>{status}</b>")
    except Exception as e:
        logger.error(f"Failed to notify customer {customer_id}: {e}")
        await callback.answer(f"Error: {e}", show_alert=True)


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logger.info(f"🌸 {SHOP_NAME} bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
