import logging
from logging import StreamHandler

import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправки сообщения в чат телеграмма."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Начало отправки сообщения в Telegram')
    except telegram.error.TelegramError:
        raise exceptions.MyException('При отправке сообщения произошла ошибка')
    else:
        logger.info('Сообщение отправлено успешно')


def get_api_answer(current_timestamp):
    """Функция запроса к API Яндекс.Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params
    )
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise SystemError(f'Ошибка при запросе к API: {error}')
    else:
        if response.status_code != HTTPStatus.OK:
            raise exceptions.InvalidHttpStatus('Статус страницы не равен 200')
        response_content = response.json()
        return response_content


def check_response(response):
    """Функция проверки корректности ответа API Яндекс.Практикум."""
    homeworks = response['homeworks']
    if not homeworks:
        raise LookupError('Отсутсвует статус homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Неверный тип входящих данных')
    if 'homeworks' not in response.keys():
        raise KeyError(
            'Ключ "homeworks" в ответе API Яндекс.Практикум отсутствует')
    if 'current_date' not in response.keys():
        raise KeyError(
            'Ключ current_date в ответе API Яндекс.Практикум отсутствует')
    return homeworks


def parse_status(homework):
    """Функция, проверяющая статус домашнего задания."""
    if not isinstance(homework, dict):
        raise KeyError('Ошибка типа данных в homework')
    homework_name = homework['homework_name']
    if homework_name is None:
        raise KeyError('В ответе API нет ключа homework_name')
    homework_status = homework.get('status')
    if homework_status is None:
        raise KeyError('В ответе API нет ключа homework_status')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        raise exceptions.UnknownHomeworkStatus('Такого статуса нет в словаре')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция проверки доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    logger.info('Вы запустили Бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    # проверка обязательных переменных окружения
    if not check_tokens():
        logger.critical('Обязательные переменные окружения отсутствуют.')
        sys.exit()
    last_message = ''
    # Проверка статуса домашней работы с определенной переодичностью
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            logger.info(f'Получили список работ {homeworks}')
            if len(homeworks) > 0:
                message = parse_status(homeworks[0])
                if last_message != message:
                    last_message = message
                    send_message(bot, last_message)
                    logger.info('Изменений нет')
            current_timestamp = int(time.time())
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        else:
            logger.error('Сбой, ошибка не найдена')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
