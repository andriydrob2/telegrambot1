import os
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, Dispatcher, CommandHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes
)

# Завантажити змінні середовища
load_dotenv()
TOKEN = os.getenv("7784019887:AAED0R6gwR3bNdQ8aYy1NFcoGi1VBaZKlEk")
SELLER_ID = int(os.getenv("1227954847", "0"))

CHOOSING_CATEGORY, CHOOSING_PRODUCT, CONFIRMING_CART = range(3)
products = {
    "Картриджи": {"Vaporesso XROS 0.6 Ом, 2 мл": 150},
    "Рідини": {
        "Lucky 15 ml 5% WILD BERRIES": 160,
        "Lucky 15 ml 5% BERRY LEMONADE": 160,
        "Chaser 10ml 5% WATERMELON": 140,
        "Chaser 10ml 5% BLUE RASPBERRY": 140,
        "Chaser 15ml 5% CHERRIES": 170,
        "Chaser 15ml 5% BLACKBERRY": 170,
        "Chaser 30ml 5% WILD STRAWBERRY KIWI": 300
    }
}
user_carts = {}

app = Flask(__name__)
bot = Bot(TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Shop 🛒", callback_data="shop")]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ласкаво просимо! Натисніть кнопку Shop, щоб переглянути товари.", reply_markup=markup)
    return CHOOSING_CATEGORY

async def shop_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in products]
    await query.edit_message_text("Оберіть категорію:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_PRODUCT

async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split("_", 1)[1]
    keyboard = [[InlineKeyboardButton(f"{name} - {price} грн", callback_data=f"add_{name}")]
                for name, price in products[category].items()]
    keyboard.append([InlineKeyboardButton("Переглянути кошик", callback_data="view_cart")])
    await query.edit_message_text(f"Товари в категорії *{category}*:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CHOOSING_PRODUCT

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    product = query.data.split("_", 1)[1]
    cart = user_carts.setdefault(user_id, {})
    cart[product] = cart.get(product, 0) + 1
    await query.answer(f"Додано: {product}")
    return CHOOSING_PRODUCT

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cart = user_carts.get(user_id, {})
    if not cart:
        await query.edit_message_text("Ваш кошик порожній.")
        return CHOOSING_PRODUCT

    total = 0
    text = "Ваш кошик:\n"
    for product, qty in cart.items():
        price = next((p[product] for p in products.values() if product in p), 0)
        text += f"{product} — {qty} × {price} грн = {qty * price} грн\n"
        total += qty * price

    text += f"\nЗагальна сума: {total} грн\nНатисніть Підтвердити замовлення або Продовжити покупки."

    keyboard = [
        [InlineKeyboardButton("Підтвердити замовлення", callback_data="confirm_order")],
        [InlineKeyboardButton("Продовжити покупки", callback_data="continue_shopping")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMING_CART

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cart = user_carts.get(user_id, {})
    if not cart:
        await query.edit_message_text("Ваш кошик порожній.")
        return CHOOSING_CATEGORY

    total = 0
    order_text = f"Нове замовлення від @{query.from_user.username or query.from_user.first_name} (ID: {user_id}):\n\n"
    for product, qty in cart.items():
        price = next((p[product] for p in products.values() if product in p), 0)
        order_text += f"{product} — {qty} × {price} грн = {qty * price} грн\n"
        total += qty * price
    order_text += f"\nЗагальна сума: {total} грн"

    await context.bot.send_message(chat_id=SELLER_ID, text=order_text)
    user_carts[user_id] = {}
    await query.edit_message_text("Дякуємо за замовлення! Продавець отримав його.")
    return ConversationHandler.END

async def continue_shopping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in products]
    await query.edit_message_text("Оберіть категорію:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_PRODUCT

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

@app.route("/")
def index():
    return "Бот працює через Webhook \U0001f7e2"

if __name__ == '__main__':
    from telegram.ext import ApplicationBuilder
    application = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_CATEGORY: [CallbackQueryHandler(shop_button, pattern="^shop$")],
            CHOOSING_PRODUCT: [
                CallbackQueryHandler(category_chosen, pattern="^category_"),
                CallbackQueryHandler(add_to_cart, pattern="^add_"),
                CallbackQueryHandler(view_cart, pattern="^view_cart$")
            ],
            CONFIRMING_CART: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(continue_shopping, pattern="^continue_shopping$")
            ]
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
