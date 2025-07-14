import os
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Passport photo size in inches and DPI
PASSPORT_WIDTH_INCH = 3.5
PASSPORT_HEIGHT_INCH = 4.5
DPI = 300

# Convert inches to pixels
PASSPORT_WIDTH_PX = int(PASSPORT_WIDTH_INCH * DPI)
PASSPORT_HEIGHT_PX = int(PASSPORT_HEIGHT_INCH * DPI)

# Store users' photos temporarily
user_data_store = {}

TOKEN = os.getenv("TOKEN")  # Get bot token from environment variable


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Send me a passport-size photo, and then send me an even number (2,4,6,8). "
        "I'll make a collage for you!"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"{user_id}_photo.jpg"
    await photo_file.download_to_drive(photo_path)
    user_data_store[user_id] = {"photo_path": photo_path}

    await update.message.reply_text(
        "Got your photo! Now send me an even number (2,4,6,8) to make a collage."
    )


async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("Please send a valid number.")
        return

    num_copies = int(text)
    if num_copies not in [2, 4, 6, 8]:
        await update.message.reply_text("Please send an even number: 2, 4, 6, or 8.")
        return

    if user_id not in user_data_store or "photo_path" not in user_data_store[user_id]:
        await update.message.reply_text("Please send a photo first.")
        return

    photo_path = user_data_store[user_id]["photo_path"]
    image = Image.open(photo_path)
    resized = image.resize((PASSPORT_WIDTH_PX, PASSPORT_HEIGHT_PX))

    # Calculate grid (2 rows, cols = num_copies / 2)
    cols = num_copies // 2
    rows = 2

    collage_width = PASSPORT_WIDTH_PX * cols
    collage_height = PASSPORT_HEIGHT_PX * rows
    collage = Image.new("RGB", (collage_width, collage_height), "white")

    for i in range(num_copies):
        x = (i % cols) * PASSPORT_WIDTH_PX
        y = (i // cols) * PASSPORT_HEIGHT_PX
        collage.paste(resized, (x, y))

    collage_path = f"{user_id}_collage.jpg"
    collage.save(collage_path, dpi=(DPI, DPI))

    await update.message.reply_photo(photo=open(collage_path, "rb"))

    # Clean up files
    os.remove(photo_path)
    os.remove(collage_path)
    user_data_store.pop(user_id, None)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
