# bot.py
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

from story_data import story
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Хранилище состояния пользователей
# В реальном проекте лучше использовать базу данных
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    
    # Начинаем историю с начала
    user_states[user_id] = "start"
    
    # Отправляем первый узел истории
    await send_story_node(update, context, user_id)

async def send_story_node(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Отправляет узел истории пользователю"""
    current_node = user_states[user_id]
    node_data = story[current_node]
    
    # Формируем текст сообщения
    message_text = node_data["text"]
    
    # Формируем клавиатуру с вариантами ответов
    options = node_data["options"]
    if options:
        keyboard = [[option["text"]] for option in options.values()]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    else:
        # Если вариантов нет — история закончена
        reply_markup = ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
        message_text += "\n\nНажми /start чтобы начать заново."
    
    # Отправляем сообщение
    if update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    else:
        # Если это вызов из handle_choice (когда update не имеет message)
        await context.bot.send_message(chat_id=user_id, text=message_text, reply_markup=reply_markup)

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора пользователя"""
    user_id = update.effective_user.id
    user_choice = update.message.text
    
    # Проверяем, есть ли состояние у пользователя
    if user_id not in user_states:
        await update.message.reply_text("Нажми /start чтобы начать историю.")
        return
    
    current_node = user_states[user_id]
    node_data = story[current_node]
    options = node_data["options"]
    
    # Ищем выбранный вариант
    chosen_option = None
    for key, option in options.items():
        if option["text"] == user_choice:
            chosen_option = option
            break
    
    if chosen_option:
        # Обновляем состояние пользователя
        user_states[user_id] = chosen_option["next_node"]
        # Отправляем следующий узел истории
        await send_story_node(update, context, user_id)
    else:
        await update.message.reply_text("Пожалуйста, выбери один из предложенных вариантов.")

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()