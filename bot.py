import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import json
import time

from utils import is_valid_url, load_text_from_file, escape_markdown


# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


HEADERS = {'Content-Type': 'application/json', 'X-Model-Discovery-Oauth-Token': f'{balancer_token}'}


def send_to_yagpt(text):
    DATA = {
        "Params":{"NumHypos":1,"Seed":42},
        "messages":[{
            "role":"user",
            "content": text,
        }]
    }
    for i in range(3):
        try:
            r = requests.post(url=f'{model_url}', headers=HEADERS, data=json.dumps(DATA))
            if r.status_code == 200:
                return r.json()['Responses'][0]['Response'], True
            else:
                logger.error(f"Ошибка YaGPT API: {r.status_code} - {r.text}")
                return None, False
        except Exception as e:
            logger.error(f"Неудалось сделать запрос к YaGPT API: {e}")

        time.sleep(1)
    
    return None, False

def ask_api(url):
    """Отправляет GET-запрос с OAuth-авторизацией и возвращает JSON-ответ"""
    headers = {"Authorization": f'{oauth_token}'}
    print(url)
    for i in range(3):
        try:
            response = requests.get(url, headers=headers)
            print(response.status_code)
            if response.status_code == 200:
                return response.json(), True
            elif response.status_code >= 400 and response.status_code < 500:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return 'Не удалось сгенерировать запрос к API AppMetrica. Пожалуйста, уточните параметры запроса, такие как счетчик, метрики, даты, группировки и другие, чтобы я мог сформировать корректный запрос.', False
            elif response.status_code >= 500:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return 'API error, ask Ilyas', False
            else:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return 'API error, ask Ilyas', False
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к API: {e}")

        time.sleep(1)
    
    return 'API error, ask Ilyas', False

def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Привет, {user.mention_markdown_v2()}\! Я бот\-ассистент сервиса AppMetrica, на базе YandexGPT\(*NDA*\)\. Ты можешь задать мне любой вопрос про данные на любом счетчике, а я постараюсь ответить\. \
        \
\- Пожалуйста учти, что я не умею хранить контекст, поэтому для меня каждое новое сообщение \- новый запрос\. \
\- Если возникнут какие\-то баги, то отправь пожалуйста переписку Ильясу\. \
\- А если, я неправильно ответил на вопрос, попробуй четко сформулировать запрос с указанием APIKey, нужных тебе дат, метрик и группировок\.',
    )

def handle_message(update: Update, context: CallbackContext) -> None:
    """Обрабатывает текстовые сообщения от пользователя."""
    user = update.effective_user
    user_message = update.message.text
    
    # Отправляем сообщение пользователю, что бот печатает
    update.message.reply_chat_action(action='typing')

    # Получаем URL от YaGPT
    gpt_url, _ = send_to_yagpt(load_text_from_file('docs.txt') +
                               load_text_from_file('prompt1.txt') + user_message)
    # Проверяем, получили ли и что получили URL
    if not _:
        update.message.reply_text("Произошла ошибка при подключении к API YaGPT. Пожалуйста, попробуйте позже.")
        return
    elif not is_valid_url(gpt_url):
        update.message.reply_text(gpt_url)
        return

    # Получаем данные
    json_data, _ = ask_api(gpt_url)

    # Проверяем, что данные дошли
    if not _:
        update.message.reply_text(json_data)
        return

    data = {}
    data['query'] = json_data['query']
    data['data'] = json_data['data']
    data['totals'] = json_data['totals']
    data['min'] = json_data['min']
    data['max'] = json_data['max']
    # Получаем готовое сообщение от YaGPT
    bot_response, _ = send_to_yagpt(load_text_from_file('prompt2.txt') + user_message +
                                load_text_from_file('prompt3.txt') + str(data))
    # Проверяем получили ли
    if not _:
        update.message.reply_text("Произошла ошибка при подключении к API YaGPT. Пожалуйста, попробуйте позже.")
        return

    try:
        update.message.reply_markdown_v2(escape_markdown(bot_response))
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        update.message.reply_text("Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.")

def error_handler(update: Update, context: CallbackContext) -> None:
    """Логирует ошибки."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    updater = Updater(f'{bot_token}')
    
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
