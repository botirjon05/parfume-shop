"""
🌸 Parfume Center — Telegram Mini App Bot
Launches the WebApp and handles orders from it
"""

import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import CommandStart

from config import BOT_TOKEN, ADMIN_IDS, SHOP_NAME, WEBAPP_URL, CURRENCY_SYMBOL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

dp = Dispatcher()


def shop_keyboard():
    """Main keyboard with the Mini App button."""
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="🛍 Open Shop",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]],
        resize_keyboard=True
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Welcome to <b>{SHOP_NAME}</b>!\n\n"
        f"Tap the button below to browse our exclusive perfume collection, "
        f"add items to your cart, and place an order — all inside Telegram. 🌸",
        reply_markup=shop_keyboard()
    )


@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message, bot: Bot):
    """Receives order data sent from the Mini App via tg.sendData()"""
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        logger.error("Failed to parse WebApp data")
        return

    if data.get("type") != "order":
        return

    order = data["order"]
    user = message.from_user

    # Confirm to customer
    items_text = "\n".join(
        f"  • {i['name']} × {i['qty']} = {CURRENCY_SYMBOL}{i['price'] * i['qty']:.2f}"
        for i in order["items"]
    )
    await message.answer(
        f"🎉 <b>Order Received!</b>\n\n"
        f"{items_text}\n\n"
        f"💰 <b>Total: {CURRENCY_SYMBOL}{order['total']:.2f}</b>\n"
        f"📱 Phone: {order['phone']}\n"
        f"🏠 Address: {order['address']}\n"
        f"{f'📝 Note: {order[\"note\"]}' if order.get('note') else ''}\n\n"
        f"We'll confirm your order shortly! ✨",
        reply_markup=shop_keyboard()
    )

    # Notify admins
    admin_text = (
        f"🔔 <b>New Order!</b>\n\n"
        f"👤 {user.full_name} (@{user.username or 'N/A'}) — ID: {user.id}\n"
        f"📱 {order['phone']}\n"
        f"🏠 {order['address']}\n"
        f"{f'📝 {order[\"note\"]}' if order.get('note') else ''}\n\n"
        f"{items_text}\n\n"
        f"💰 <b>Total: {CURRENCY_SYMBOL}{order['total']:.2f}</b>"
    )
    status_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Confirm",  callback_data=f"status:{user.id}:confirmed"),
        InlineKeyboardButton(text="🚚 Shipped",  callback_data=f"status:{user.id}:shipped"),
    ],[
        InlineKeyboardButton(text="🎉 Delivered", callback_data=f"status:{user.id}:completed"),
        InlineKeyboardButton(text="❌ Cancel",    callback_data=f"status:{user.id}:cancelled"),
    ]])

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=status_kb)
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")


from aiogram.types import CallbackQuery

@dp.callback_query(F.data.startswith("status:"))
async def update_status(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Unauthorized")
        return

    _, customer_id, status = callback.data.split(":")
    labels = {
        "confirmed": "✅ Your order has been <b>confirmed</b>! We're preparing it.",
        "shipped":   "🚚 Your order is <b>on its way</b>!",
        "completed": "🎉 Your order has been <b>delivered</b>! Thank you for shopping with us 🌸",
        "cancelled": "❌ Your order has been <b>cancelled</b>. Please contact us for help."
    }
    try:
        await bot.send_message(int(customer_id), labels[status])
        await callback.answer(f"Customer notified: {status}")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(f"✅ Status updated to: <b>{status}</b>")
    except Exception as e:
        await callback.answer(f"Error: {e}")


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logger.info(f"🌸 {SHOP_NAME} Mini App Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
