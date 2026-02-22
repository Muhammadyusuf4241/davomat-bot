import os
from io import BytesIO

import pandas as pd
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -5135030233  # Xabar yuboriladigan guruh


def get_absent_students(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    absent = []
    for _, row in df.iterrows():
        familiya = str(row.get("Familiya", "")).strip()
        ism = str(row.get("Ism", "")).strip()
        kelgan = row.get("Kelgan vaqti", None)

        if not familiya or familiya.lower() == "nan":
            continue

        ism = ism.rstrip("К").strip()
        full_name = f"{familiya} {ism}".strip()

        if pd.isna(kelgan) or str(kelgan).strip() in ("", "NaN", "nan"):
            absent.append(full_name)

    return absent


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return

    filename = (doc.file_name or "").lower()
    if not filename.endswith((".xlsx", ".xls")):
        await update.message.reply_text(
            "Iltimos .xlsx yoki .xls formatida fayl yuboring.")
        return

    # Faylni yuklab olish (yangi usul)
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()

    try:
        absent = get_absent_students(bytes(data))
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")
        return

    if not absent:
        msg = "✅ Barcha o'quvchilar kelgan!"
    else:
        lines = [f"📋 Kelmagan o'quvchilar ({len(absent)} ta):\n"]
        for i, name in enumerate(absent, 1):
            lines.append(f"{i}. {name}")
        msg = "\n".join(lines)

    # Guruhga yuborish
    await context.bot.send_message(chat_id=GROUP_ID, text=msg)

    # Faylni yuborganga tasdiqlash
    await update.message.reply_text("✅ Natija guruhga yuborildi!")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN o'rnatilmagan!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("✅ Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
