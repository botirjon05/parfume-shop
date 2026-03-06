"""
🌸 Parfume Center — Telegram Bot
Secure version:
- /start
- receives WebApp orders via message.web_app_data
- sends admin/customer messages
- handles admin status callbacks
"""

import asyncio
import json
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

# ── CONFIG ────────────────────────────────────────────────────────
BOT_TOKEN = "8045542724:AAGcakq1YxNSxdCB1aw0Lln1BPKymIHUWjA"
ADMIN_IDS = [887340351]
SHOP_NAME = "Parfume Center"
WEBAPP_URL = "https://botirjon05.github.io/parfume-shop/"
# ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger(__name__)

dp = Dispatcher()


def status_keyboard(customer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"st:{customer_id}:confirmed"),
            InlineKeyboardButton(text="🚚 Yetkazilmoqda", callback_data=f"st:{customer_id}:shipped"),
        ],
        [
            InlineKeyboardButton(text="🎉 Yetkazildi", callback_data=f"st:{customer_id}:completed"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"st:{customer_id}:cancelled"),
        ]
    ])


@dp.message(CommandStart())
async def on_start(message: Message):
    await message.answer(
        f"👋 <b>{SHOP_NAME}ga xush kelibsiz!</b>\n\n"
        "Bu yerda siz o‘zingizga mos noyob iforni topasiz.\n"
        "Kolleksiyamizni ko‘rib chiqing va buyurtmangizni oson va tez rasmiylashtiring 🌸",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
    )


@dp.message(F.web_app_data)
async def on_webapp_order(message: Message, bot: Bot):
    try:
        raw = message.web_app_data.data
        data = json.loads(raw)

        if data.get("type") != "order":
            return

        order = data.get("order", {})
        customer_id = message.from_user.id

        name = order.get("name", "")
        phone = order.get("phone", "")
        addr = order.get("addr", "")
        note = order.get("note", "")
        items = order.get("items", [])
        total = float(order.get("total", 0))
        order_id = int(order.get("id", 0))
        order_num = str(order_id)[-6:] if order_id else "------"

        lines = "\n".join(
            f"  • {item.get('emoji', '🧴')} {item.get('name', 'Mahsulot')} ×{item.get('qty', 1)}  ${float(item.get('price', 0)) * int(item.get('qty', 1)):.2f}"
            for item in items
        )

        note_line = f"\n📝 <i>{note}</i>" if note else ""

        # 1. Customer confirmation
        await bot.send_message(
            customer_id,
            f"✅ <b>#{order_num} Buyurtma qabul qilindi!</b>\n\n"
            f"{lines}\n\n"
            f"💰 Jami: <b>${total:.2f}</b>\n"
            f"📱 Telefon raqami: {phone}\n"
            f"🏠 Manzil: {addr}{note_line}\n\n"
            f"Buyurtmangizni tez orada tasdiqlaymiz 🌸"
        )

        # 2. Admin notification
        admin_text = (
            f"🔔 <b>Yangi Buyurtma #{order_num}</b>\n\n"
            f"👤 <a href='tg://user?id={customer_id}'>{name or 'Mijoz'}</a> · ID: <code>{customer_id}</code>\n"
            f"📱 Telefon raqami: {phone}\n"
            f"🏠 Manzil: {addr}{note_line}\n\n"
            f"{lines}\n\n"
            f"💰 <b>Jami: ${total:.2f}</b>\n\n"
            f"📌 <b>Holati:</b> ⏳ Jarayonda"
        )

        for admin_id in ADMIN_IDS:
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=status_keyboard(customer_id)
            )

    except Exception as e:
        logger.exception(f"WebApp order error: {e}")
        await message.answer("❌ Buyurtmani qabul qilishda xatolik yuz berdi.")


@dp.callback_query(F.data.startswith("st:"))
async def on_status(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Ruxsat yo‘q", show_alert=True)
        return

    try:
        _, cid, status = callback.data.split(":")
        customer_id = int(cid)
    except ValueError:
        await callback.answer("Noto‘g‘ri ma’lumot", show_alert=True)
        return

    msgs = {
        "confirmed": (
            "✅ <b>Buyurtmangiz tasdiqlandi!</b>\n\n"
            "Buyurtmangiz tayyorlanmoqda va tez orada jo‘natiladi 🌸\n"
            "Sabringiz uchun rahmat!"
        ),
        "shipped": (
            "🚚 <b>Buyurtmangiz yo‘lga chiqdi!</b>\n\n"
            "Tez orada manzilingizga yetkazib beriladi.\n"
            "Iltimos, telefoningiz faol bo‘lsin 📱"
        ),
        "completed": (
            f"🎉 <b>Buyurtmangiz muvaffaqiyatli yetkazildi!</b>\n\n"
            f"<b>{SHOP_NAME}</b>ni tanlaganingiz uchun rahmat 🌸\n"
            "Yana sizni kutib qolamiz!"
        ),
        "cancelled": (
            "❌ <b>Buyurtmangiz bekor qilindi.</b>\n\n"
            "Savollaringiz bo‘lsa, bemalol biz bilan bog‘laning."
        ),
    }

    label_map = {
        "confirmed": "✅ Tasdiqlandi",
        "shipped": "🚚 Yetkazilmoqda",
        "completed": "🎉 Yetkazildi",
        "cancelled": "❌ Bekor qilindi",
    }

    try:
        await bot.send_message(customer_id, msgs.get(status, status))

        base = callback.message.html_text or callback.message.text or ""
        base = re.sub(r"\n\n📌 <b>Holati:</b>.*$", "", base, flags=re.S)
        new_text = base + f"\n\n📌 <b>Holati:</b> {label_map.get(status, status)}"

        await callback.message.edit_text(
            new_text,
            reply_markup=status_keyboard(customer_id),
            disable_web_page_preview=True
        )

        await callback.answer("✅ Mijozga xabar yuborildi")

    except Exception as e:
        logger.exception(f"Status update error: {e}")
        await callback.answer(f"Xatolik: {e}", show_alert=True)


async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.info(f"🌸 {SHOP_NAME} starting…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
