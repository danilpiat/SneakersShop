import asyncio
import json
import logging
import traceback
import re
import os
import json

from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup

# Настройка расширенного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_activity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sneakerculture_bot")


with open("bot_settings.json", "r", encoding="utf-8") as f:
    config = json.load(f)

API_TOKEN = config["API_TOKEN"]
WEBAPP_URL = config["WEBAPP_URL"]
ADMIN_CHAT_ID = config["ADMIN_CHAT_ID"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


class MarkdownV2Escaper:
    """
    A class to escape text for Telegram MarkdownV2 formatting.
    It ensures that only characters outside MarkdownV2 syntax are escaped.
    """

    def __init__(self):
        # Define special characters that need to be escaped in MarkdownV2
        self.special_chars = r'_*\[\]()~`>#+-=|{}.!'

        # Compile regex patterns for MarkdownV2 elements
        self.markdown_patterns = [
            r'\*[^*]+\*',  # Bold
            r'_[^_]+_',  # Italic
            r'__[^_]+__',  # Underline
            r'~[^~]+~',  # Strikethrough
            r'\|\|[^|]+\|\|',  # Spoiler
            r'\[([^\]]+)\]\(([^)]+)\)',  # Inline URL
            r'`[^`]+`',  # Inline code
            r'(?:[^`]*?)```',  # Code blocks
            r'```python\n[\s\S]*?\n```'  # Python code blocks
        ]
        # Combine all patterns into a single regex
        self.combined_pattern = re.compile('|'.join(self.markdown_patterns))

    def escape(self, text: str) -> str:
        """
        Escapes special characters in the text that are not part of MarkdownV2 syntax.

        Args:
            text (str): The input string with MarkdownV2 formatting.

        Returns:
            str: The escaped string safe for Telegram API.
        """
        if not text:
            return text

        # Find all MarkdownV2 syntax matches
        matches = list(self.combined_pattern.finditer(text))

        # Initialize variables
        escaped_text = []
        last_end = 0

        for match in matches:
            start, end = match.start(), match.end()
            # Escape non-Markdown text before the current match
            if last_end < start:
                non_markdown_part = text[last_end:start]
                escaped_non_markdown = self._escape_non_markdown(non_markdown_part)
                escaped_text.append(escaped_non_markdown)
            # Append the Markdown syntax without escaping
            escaped_text.append(match.group())
            last_end = end

        # Escape any remaining non-Markdown text after the last match
        if last_end < len(text):
            remaining_text = text[last_end:]
            escaped_remaining = self._escape_non_markdown(remaining_text)
            escaped_text.append(escaped_remaining)

        return ''.join(escaped_text)

    def _escape_non_markdown(self, text: str) -> str:
        """
        Escapes special characters in non-Markdown text.

        Args:
            text (str): Text outside of Markdown syntax.

        Returns:
            str: Escaped text.
        """
        escaped = ''
        for char in text:
            if char in self.special_chars:
                escaped += '\\' + char
            else:
                escaped += char
        return escaped

@dp.message(CommandStart())
async def start(message: types.Message):
    """Обработка команды /start"""
    logger.info(f"Start command from user_id={message.from_user.id}, username={message.from_user.username}")

    try:
        kb = [
            [types.KeyboardButton(text="🚀 Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))],
            [types.KeyboardButton(text="ℹ️ Помощь")],
        ]
        keyboard = ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )

        await message.answer(
            "Добро пожаловать. Выберите действие из встроенной клавиатуры:",
            reply_markup=keyboard
        )
        logger.debug("Start command processed successfully")

    except Exception as e:
        logger.error(f"Error in start command: {e}\n{traceback.format_exc()}")


@dp.message(F.text == "ℹ️ Помощь")
async def info(message: types.Message):
    """Обработка кнопки помощи"""
    logger.info(f"Help requested by user_id={message.from_user.id}")

    try:
        await message.answer(
            "Это Telegram-бот магазина Sneaker Culture. "
            "Нажмите кнопку '🚀 Открыть магазин' для запуска веб-приложения."
        )
        logger.debug("Help message sent")

    except Exception as e:
        logger.error(f"Error sending help message: {e}\n{traceback.format_exc()}")


@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    """Обработчик данных из WebApp с расширенным логированием"""
    # Логируем получение данных
    logger.info(
        f"Received WebApp data from user_id={message.from_user.id}, "
        f"username={message.from_user.username}"
    )
    logger.debug(f"Raw WebApp data: {message.web_app_data.data}")

    try:
        # Парсим полученные данные
        web_data = json.loads(message.web_app_data.data)
        logger.info("Successfully parsed WebApp data")
        logger.debug(f"Parsed data: {json.dumps(web_data, indent=2, ensure_ascii=False)}")

        # Извлекаем данные заказа
        items = web_data.get("items", [])
        total_amount = web_data.get("totalAmount", 0)
        timestamp = web_data.get("timestamp", 0)

        # Логируем детали заказа
        logger.info(f"Order contains {len(items)} items, total: {total_amount} руб.")

        # Инициализируем данные пользователя
        user_data = {
            'id': message.from_user.id,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name or '',
            'username': message.from_user.username or 'нет'
        }
        logger.debug(f"User data: {user_data}")

        # Формируем полное имя пользователя
        full_name = f"{user_data['first_name']} {user_data['last_name']}".strip()

        # Форматируем дату заказа
        order_date = datetime.fromtimestamp(timestamp / 1000).strftime("%d.%m.%Y %H:%M")

        # Формируем сообщение-чек для администратора
        admin_message = (
            f"🛒 *НОВЫЙ ЗАКАЗ* {timestamp}\n\n"
            f"👤 *Клиент:* [{full_name}]\n"
            f"🔗 @{user_data['username']}\n"
            f"🆔 ID: `{user_data['id']}`\n"
            f"📅 *Дата:* {order_date}\n\n"
            "📋 *Состав заказа:*\n"
        )

        # Добавляем товары в сообщение
        for item in items:
            admin_message += (
                f"\n• {item['title']}\n"
                f"  Размер: {item['size']}\n"
                f"  Цвет: {item['color']}\n"
                f"  Цена: {float(item['price']):.2f} руб × {item['quantity']} шт\n"
            )

        # Добавляем итоговую сумму
        admin_message += (
            f"\n💵 *Итого:* {float(total_amount):.2f} руб\n"
            f"🚚 *Тип:* {'Предзаказ' if items[0].get('isPreOrder', False) else 'В наличии'}"
        )

        # Логируем сообщение для администратора
        logger.debug(f"Admin message before escape:\n{admin_message}")

        # Экранирование для MarkdownV2
        escaper = MarkdownV2Escaper()
        escaped_admin_message = escaper.escape(admin_message)

        logger.debug(f"Admin message after escape:\n{escaped_admin_message}")

        # Отправляем сообщение администратору
        admin_msg = await message.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=escaped_admin_message,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )
        logger.info(f"Admin message sent to chat {ADMIN_CHAT_ID}, message_id={admin_msg.message_id}")

        # Формируем сообщение для пользователя
        user_message = (
            "✅ *Спасибо за заказ*\n\n"
            f"{full_name}, ваш заказ успешно оформлен\n"
            "Наш менеджер свяжется с вами в ближайшее время для уточнения деталей\n\n"
            f"*Номер заказа:* {timestamp}\n"
            f"*Сумма заказа:* {float(total_amount):.2f} руб\n"
        )
        for item in items:
            user_message += (
                f"\n• {item['title']}\n"
                f"  Размер: {item['size']}\n"
                f"  Цвет: {item['color']}\n"
                f"  Цена: {float(item['price']):.2f} руб × {item['quantity']} шт\n"
            )

        logger.debug(f"User message before escape:\n{user_message}")

        # Экранирование для MarkdownV2
        escaped_user_message = escaper.escape(user_message)

        logger.debug(f"User message after escape:\n{escaped_user_message}")

        # Отправляем подтверждение пользователю
        user_msg = await message.answer(
            text=escaped_user_message,
            parse_mode="MarkdownV2"
        )
        logger.info(f"Confirmation sent to user {user_data['id']}, message_id={user_msg.message_id}")

        # Логируем успешную обработку
        logger.info(f"Order processed successfully for user_id={user_data['id']}")

    except json.JSONDecodeError as e:
        error_msg = "Ошибка декодирования JSON данных"
        logger.error(f"{error_msg}: {e}\nData: {message.web_app_data.data}\n{traceback.format_exc()}")
        await message.answer("❌ Ошибка обработки данных заказа, пожалуйста, попробуйте еще раз")

    except Exception as e:
        error_msg = "Неизвестная ошибка при обработке заказа"
        logger.error(f"{error_msg}: {e}\n{traceback.format_exc()}")

        # Отправляем сообщение об ошибке
        await message.answer(
            "❌ Произошла ошибка при обработке вашего заказа, "
            "пожалуйста, попробуйте еще раз или свяжитесь с поддержкой"
        )


async def main() -> None:
    """Запуск бота с логированием"""
    logger.info("===== Starting bot =====")
    logger.info(f"Bot token: {API_TOKEN[:5]}...{API_TOKEN[-5:]}")
    logger.info(f"WebApp URL: {WEBAPP_URL}")
    logger.info(f"Admin chat ID: {ADMIN_CHAT_ID}")

    try:
        await dp.start_polling(bot)
        logger.info("Bot polling started")
    except Exception as e:
        logger.critical(f"Fatal error in bot: {e}\n{traceback.format_exc()}")
    finally:
        logger.info("===== Bot stopped =====")


if __name__ == "__main__":
    # Создаем папку для логов, если ее нет
    os.makedirs("bot_logs", exist_ok=True)

    # Настраиваем ротацию логов
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(
        "bot_logs/bot.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)

    # Запускаем бота
    asyncio.run(main())