"""
🌸 Parfume Center — Telegram Bot
Products are now managed via Supabase directly from the Mini App.
Bot only handles:
  • /start              — welcome + shop button
  • st:<uid>:<status>   — admin taps order status buttons → notifies customer
"""
import asyncio
import logging
import re


from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

# ══════════════════════════════════════════════════
BOT_TOKEN  = os.getenv("BOT_TOKEN")
ADMIN_IDS  = [887340351]
SHOP_NAME  = "Parfume Center"
WEBAPP_URL = "https://botirjon05.github.io/parfume-shop/"
# ══════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(message: Message):
    await message.answer(
        f"👋 <b>{SHOP_NAME}</b>ga xush kelibsiz!\n\n"
        f"Bu yerda siz o'zingizga mos noyob iforni topasiz!\n\n Kolleksiyamizni ko'rib chiqing va buyurtmangizni oson va tez rasmiylashtiring 🌸",
        reply_markup = ReplyKeyboardRemove(remove_keyboard = True)
    )


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
    labels = {"confirmed":"✅ Tasdiqlandi","shipped":"🚚 Yetkazilmoqda","completed":"🎉 Yetkazildi","cancelled":"❌ Bekor qilindi"}
    try:
        await bot.send_message(customer_id, msgs.get(status, f"Status: {status}"))
        await callback.answer("Mijozga xabar yuborildi ✓")
        try:
            orig = re.sub(r'\n\nStatus → .+', '', callback.message.text or '')
            await callback.message.edit_text(orig + f"\n\nStatus → <b>{labels.get(status, status)}</b>", reply_markup=callback.message.reply_markup)
        except Exception:
            pass
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)


async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.info(f"🌸 {SHOP_NAME} bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())