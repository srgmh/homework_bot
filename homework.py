from dotenv import load_dotenv
import logging
import os
import requests
import time
from telegram import Bot


load_dotenv()

# Variables from environment variable space
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    filename='logs.log',
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s',
    encoding='UTF-8'
)


def send_message(bot, message):
    """Отправляет сообщение о результатах ревью."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Функция делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    В случае успешного запроса должна вернуть ответ API,
    преобразовав его из формата JSON к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise Exception('API возвращает код не со статусом 200')
    return response.json()


def check_response(response):
    """Функция проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    Если ответ API соответствует ожиданиям, то функция должна вернуть список
    домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'.
    """
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')
    if response is None:
        raise TypeError('Ответ API: None')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise KeyError('Ключ "homeworks" в ответе API не выдает список')
    if homeworks is None:
        raise KeyError('Ключ "homeworks" в ответе API не найден')
    x = homeworks[0]
    return x


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работы.
    статус этой работы. В качестве параметра функция
    получает только один элемент из списка домашних работ.
    В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_STATUSES.
    """
    if 'homework_name' not in homework:
        raise KeyError('ключа "homework_name" нет в данной домашней работе')
    homework_name = homework.get('homework_name')

    if 'status' not in homework:
        logging.error('отсутствие ожидаемых ключей в ответе API')
        raise KeyError('ключа "status" нет в данной домашней работе')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        logging.error(
            'недокументированный статус домашней работы,'
            'обнаруженный в ответе API')
        raise KeyError('неизвестный статус домашки')

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствие обязательных переменных окружения.')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            try:
                # Получаем ответ от API Яндекс Практикума.
                response = get_api_answer(current_timestamp)
                logging.info('ответ API получен успешно')
            except Exception as error:
                logging.error(f'Сбой в отправке сообщения: {error}')

            # Проверяем ответ API на корректность.
            homework = check_response(response)

            # На основании ответа API получаем сообщение со статусом работы.
            message = parse_status(homework)

            try:
                # Бот отправляет пользователю сообщение
                # в телеграм со статусом работы.
                bot.send_message(TELEGRAM_CHAT_ID, message)
                logging.info('Удачная отправка сообщения')
            except Exception as error:
                logging.error(f'Сбой в отправке сообщения: {error}')

            current_timestamp = response.get('current_date')

            # Ждем некоторое время и отправляем новый запрос
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            bot.send_message(TELEGRAM_CHAT_ID, message)
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
