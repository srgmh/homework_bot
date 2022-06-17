# Constants.

# Время повторного запроса, sec.
RETRY_TIME = 600

# Эндпоинт API.
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

# Словарь для расшифровки статусов домашней работы.
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
