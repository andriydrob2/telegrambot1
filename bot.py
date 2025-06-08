from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# ID продавця (твій Telegram ID)
SELLER_ID = 1227954847  # заміни на свій реальний ID

# Стани розмови
CHOOSING_CATEGORY, CHOOSING_PRODUCT, CONFIRMING_CART = range(3)

# Категорії товарів та товари (приклад)
products = {
    "Картриджи": {
        "Vaporesso XROS 0.6 Ом, 2 мл": 150,
    },
    "Рідини": {
        "Lucky 15 ml 5% WILD BERRIES": 160,
        "Lucky 15 ml 5% BERRY LEMONADE": 160,
        "Chaser 10ml 5% WATERMELON": 140,
        "Chaser 10ml 5% BLUE RASPBERRY": 140,
        "Chaser 15ml 5% CHERRIES": 170,
        "Chaser 15ml 5% BLACKBERRY": 170,
        "Chaser 30ml 5% WILD STRAWBERRY KIWI": 300,
    }
}

# Кошик: user_id -> {product_name: quantity}
user_carts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Shop 🛒", callback_data="shop")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ласкаво просимо! Натисніть кнопку Shop, щоб переглянути товари.", reply_markup=reply_markup)
    return CHOOSING_CATEGORY

async def shop_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Відобразити категорії
    keyboard = []
    for category in products.keys():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"category_{category}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text="Оберіть категорію:", reply_markup=reply_markup)
    return CHOOSING_PRODUCT

async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split("_", 1)[1]

    # Показати товари цієї категорії з кнопками "Додати"
    keyboard = []
    for product_name, price in products[category].items():
        keyboard.append([InlineKeyboardButton(f"{product_name} - {price} грн", callback_data=f"add_{product_name}")])
    keyboard.append([InlineKeyboardButton("Переглянути кошик", callback_data="view_cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=f"Товари в категорії *{category}*:", reply_markup=reply_markup, parse_mode="Markdown")
    return CHOOSING_PRODUCT

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    product_name = query.data.split("_", 1)[1]

    # Додати в кошик
    cart = user_carts.setdefault(user_id, {})
    cart[product_name] = cart.get(product_name, 0) + 1

    await query.answer(text=f"Додано до кошика: {product_name}")
    return CHOOSING_PRODUCT

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cart = user_carts.get(user_id, {})

    if not cart:
        await query.edit_message_text(text="Ваш кошик порожній.")
        return CHOOSING_PRODUCT

    # Показати вміст кошика
    text = "Ваш кошик:\n"
    total = 0
    for product, qty in cart.items():
        # Знайти ціну товару
        price = None
        for cat_products in products.values():
            if product in cat_products:
                price = cat_products[product]
                break
        if price is None:
            price = 0
        text += f"{product} — {qty} шт. × {price} грн = {qty * price} грн\n"
        total += qty * price
    text += f"\nЗагальна сума: {total} грн\n"
    text += "\nНатисніть Підтвердити замовлення або Продовжити покупки."

    keyboard = [
        [InlineKeyboardButton("Підтвердити замовлення", callback_data="confirm_order")],
        [InlineKeyboardButton("Продовжити покупки", callback_data="continue_shopping")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return CONFIRMING_CART

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cart = user_carts.get(user_id, {})

    if not cart:
        await query.edit_message_text("Ваш кошик порожній.")
        return CHOOSING_CATEGORY

    # Створити текст замовлення
    text = f"Нове замовлення від @{query.from_user.username or query.from_user.first_name} (ID: {user_id}):\n\n"
    total = 0
    for product, qty in cart.items():
        price = None
        for cat_products in products.values():
            if product in cat_products:
                price = cat_products[product]
                break
        if price is None:
            price = 0
        text += f"{product} — {qty} шт. × {price} грн = {qty * price} грн\n"
        total += qty * price
    text += f"\nЗагальна сума: {total} грн"

    # Надіслати продавцю
    await context.bot.send_message(chat_id=SELLER_ID, text=text)

    # Очистити кошик користувача
    user_carts[user_id] = {}

    await query.edit_message_text("Дякуємо за замовлення! Продавець вже отримав ваше замовлення.")
    return ConversationHandler.END

async def continue_shopping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Повернутися до вибору категорій
    keyboard = []
    for category in products.keys():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"category_{category}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text="Оберіть категорію:", reply_markup=reply_markup)
    return CHOOSING_PRODUCT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token("7784019887:AAED0R6gwR3bNdQ8aYy1NFcoGi1VBaZKlEk").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_CATEGORY: [CallbackQueryHandler(shop_button, pattern="^shop$")],
            CHOOSING_PRODUCT: [
                CallbackQueryHandler(category_chosen, pattern="^category_"),
                CallbackQueryHandler(add_to_cart, pattern="^add_"),
                CallbackQueryHandler(view_cart, pattern="^view_cart$"),
            ],
            CONFIRMING_CART: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(continue_shopping, pattern="^continue_shopping$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()
