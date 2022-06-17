from dotenv import load_dotenv
from http import HTTPStatus
import logging
import os
import requests
import time
import sys
import telegram as telegram


# Import exception
from exceptions import HTTPStatusError

# Import constants.
from settings import ENDPOINT, HOMEWORK_STATUSES, RETRY_TIME

# Load environment variable space.
load_dotenv()

# Variables from environment variable space
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Headers для API яндекс.практикум.
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


logging.basicConfig(
    filename='logs.log',
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
    encoding='UTF-8'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s -'
    '%(message)s - %(lineno)d'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Send review result to telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Удачная отправка сообщения в телеграм')
    except Exception as error:
        logger.error(
            f'Ошибка {error} при отправке сообщения "{message}" в телеграм'
        )


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(f'Ошибка получения ответа API: {error}')

    if response.status_code == HTTPStatus.OK:
        try:
            return response.json()
        except Exception as error:
            logger.error(f'Неудачная попытка преобразования ответа API '
                         f'из JSON, ошибка: {error}')
    else:
        logger.error(f'HTTPStatus: {response.status_code}')
        raise HTTPStatusError(f'HTTPStatus: {response.status_code}')


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        logger.error('Ответ API не является словарем')
        raise TypeError('Ответ API не является словарем')
    homeworks = response.get('homeworks')
    if homeworks is None:
        logger.error('Ключ "homeworks" в ответе API не найден')
        raise KeyError('Ключ "homeworks" в ответе API не найден')
    if not isinstance(homeworks, list):
        logger.error('Ключ "homeworks" в ответе API не выдает список')
        raise KeyError('Ключ "homeworks" в ответе API не выдает список')

    return homeworks


def parse_status(homework):
    """Извлекает из информации о домашней работы ее статус."""
    if 'homework_name' not in homework:
        logger.error('ключа "homework_name" нет в выбранной домашней работе')
        raise KeyError('ключа "homework_name" нет в выбранной домашней работе')
    homework_name = homework.get('homework_name')

    if 'status' not in homework:
        logger.error('ключа "status" нет в выбранной домашней работе')
        raise KeyError('ключа "status" нет в выбранной домашней работе')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        logger.error(
            'недокументированный статус домашней работы,'
            'обнаруженный в ответе API')
        raise KeyError('неизвестный статус домашки')

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Недоступна одна из переменных окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_message = ''

    while True:
        try:
            # Получили ответ API в понятном python формате (dict).
            response = get_api_answer(current_timestamp)

            # Получили список с домашками за выбранный промежуток времени.
            homework = check_response(response)

            if len(homework) > 0:
                # Извлекли статус домашки.
                message = parse_status(homework[0])

                send_message(bot, message)
                current_timestamp = response.get('current_date')
            else:
                logger.debug('Нет новых статусов домашки')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if old_message != message:
                send_message(bot, message)
                old_message = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
