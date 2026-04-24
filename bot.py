import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from skyscanner_search import search_cheapest_market

# =============================================
# AYARLAR — BURAYA KENDİ BİLGİLERİNİ GİR
# =============================================
TELEGRAM_TOKEN = "8713331820:AAG53oUz7TE-CXRs060TC2yV41HHhsFCbrQ"
SKYSCANNER_API_KEY = "uc643373167396223405725428773537"
# =============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

YARDIM_METNI = """
✈️ *Skyscanner Çok Market Fiyat Botu*

Tüm ülke marketlerinde en ucuz fiyatı bulur.

📌 *Komutlar:*

*Tek yön uçuş:*
`/tek IST LHR 2025-08-15`

*Gidiş-dönüş uçuş:*
`/gd IST LHR 2025-08-15 2025-08-22`

📌 *Format:*
• IATA kodları büyük harf (IST, LHR, CDG...)
• Tarih: YYYY-AA-GG formatında

💡 *Örnek:*
`/tek IST AMS 2025-09-01`
`/gd IST BCN 2025-07-20 2025-07-27`
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(YARDIM_METNI, parse_mode="Markdown")

async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(YARDIM_METNI, parse_mode="Markdown")

async def tek_yon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tek yön uçuş arama: /tek IST LHR 2025-08-15"""
    args = context.args
    if len(args) != 3:
        await update.message.reply_text(
            "❌ Hatalı format!\n\nDoğru kullanım:\n`/tek KALKIŞ VARIŞ TARİH`\n\nÖrnek: `/tek IST LHR 2025-08-15`",
            parse_mode="Markdown"
        )
        return

    origin, destination, date = args[0].upper(), args[1].upper(), args[2]

    msg = await update.message.reply_text(
        f"🔍 *{origin} → {destination}* ({date})\n"
        f"Tüm marketler taranıyor... Bu işlem 1-2 dakika sürebilir ⏳",
        parse_mode="Markdown"
    )

    try:
        result = await search_cheapest_market(
            api_key=SKYSCANNER_API_KEY,
            origin=origin,
            destination=destination,
            depart_date=date,
            return_date=None
        )
        await msg.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Hata: {e}")
        await msg.edit_text(f"❌ Bir hata oluştu: {str(e)}")

async def gidis_donus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gidiş-dönüş arama: /gd IST LHR 2025-08-15 2025-08-22"""
    args = context.args
    if len(args) != 4:
        await update.message.reply_text(
            "❌ Hatalı format!\n\nDoğru kullanım:\n`/gd KALKIŞ VARIŞ GİDİŞ_TARİH DÖNÜŞ_TARİH`\n\nÖrnek: `/gd IST LHR 2025-08-15 2025-08-22`",
            parse_mode="Markdown"
        )
        return

    origin, destination, depart_date, return_date = (
        args[0].upper(), args[1].upper(), args[2], args[3]
    )

    msg = await update.message.reply_text(
        f"🔍 *{origin} → {destination}* | Gidiş: {depart_date} | Dönüş: {return_date}\n"
        f"Tüm marketler taranıyor... Bu işlem 1-2 dakika sürebilir ⏳",
        parse_mode="Markdown"
    )

    try:
        result = await search_cheapest_market(
            api_key=SKYSCANNER_API_KEY,
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date
        )
        await msg.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Hata: {e}")
        await msg.edit_text(f"❌ Bir hata oluştu: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yardim", yardim))
    app.add_handler(CommandHandler("tek", tek_yon))
    app.add_handler(CommandHandler("gd", gidis_donus))

    logger.info("Bot başlatıldı!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
