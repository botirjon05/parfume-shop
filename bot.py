"""
🌸 Parfume Center — Telegram Bot
Handles /start and admin order status callbacks.
Orders are sent directly from the Mini App to Telegram API.
"""

import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

# ── CONFIG ────────────────────────────────────────────────────────
BOT_TOKEN = "8045542724:AAGcakq1YxNSxdCB1aw0Lln1BPKymIHUWjA"  # from @BotFather
ADMIN_IDS = [887340351]  # your Telegram user ID (integer)
SHOP_NAME = "Parfume Center"
WEBAPP_URL = "https://botirjon05.github.io/parfume-shop/"
# ─────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(message: Message):
    await message.answer(
        f"👋 <b>{SHOP_NAME}ga xush kelibsiz!</b>\n\n"
        "Bu yerda siz o‘zingizga mos noyob iforni topasiz.\n"
        "Kolleksiyamizni ko‘rib chiqing va buyurtmangizni oson va tez rasmiylashtiring 🌸",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
    )


@dp.callback_query(F.data.startswith("st:"))
async def on_status(callback: CallbackQuery, bot: Bot):
    """
    Admin taps Confirm / Shipped / Delivered / Cancel.
    callback_data format: st:<customer_id>:<status>
    where status is one of: confirmed, shipped, completed, cancelled
    """
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Ruxsat yo‘q", show_alert=True)
        return

    try:
        _, cid, status = callback.data.split(":")
        customer_id = int(cid)
    except ValueError:
        await callback.answer("Noto‘g‘ri ma’lumot", show_alert=True)
        return

    # User-facing messages (Uzbek)
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

    # Admin-visible label for status
    label_map = {
        "confirmed": "✅ Tasdiqlandi",
        "shipped": "🚚 Yetkazilmoqda",
        "completed": "🎉 Yetkazildi",
        "cancelled": "❌ Bekor qilindi",
    }
    label = label_map.get(status, status)

    text = msgs.get(status, f"📌 Buyurtma holati: <b>{label}</b>")

    try:
        # 1) Notify customer
        await bot.send_message(customer_id, text)

        # 2) Update admin message text (keep buttons so you can change status again)
        try:
            base = callback.message.html_text or callback.message.text or ""
            # Remove previous "Holati" block if present (so it doesn't stack)
            base = re.sub(r"\n\n📌 <b>Holati:</b>.*$", "", base, flags=re.S)

            new_text = base + f"\n\n📌 <b>Holati:</b> {label}"
            await callback.message.edit_text(
                new_text,
                reply_markup=callback.message.reply_markup,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Could not edit admin message: {e}")

        await callback.answer("✅ Mijozga xabar yuborildi")
    except Exception as e:
        logger.error(f"Failed to notify customer {customer_id}: {e}")
        await callback.answer(f"Xatolik: {e}", show_alert=True)


async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logger.info(f"🌸 {SHOP_NAME} starting…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
