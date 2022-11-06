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
        logging.info('Cообщение в Telegram было отправлено')
    except Exception as error:
        logging.error('Cбой при отправке сообщения в Telegram')


def get_api_answer(current_timestamp):
    """Функция запроса к API Яндекс.Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params
    )
    response_content = response.json()
    if response.status_code == HTTPStatus.OK:
        return response_content
    else:
        raise exceptions.InvalidHttpStatus(
            'Ошибка при обращении к API Яндекс.Практикума: ',
            f'Код ответа: {response_content.get("code")}',
            f'Сообщение сервера: {response_content.get("message")}'
        )


def check_response(response):
    """Функция проверки корректности ответа API Яндекс.Практикум."""
    try:
        timestamp = response['current_date']
    except KeyError:
        logging.error(
            'Ключ current_date в ответе API Яндекс.Практикум отсутствует'
        )
    try:
        homeworks = response['homeworks']
    except KeyError:
        logging.error(
            'Ключ homeworks в ответе API Яндекс.Практикум отсутствует'
        )
    if isinstance(timestamp, int) and isinstance(homeworks, list):
        return homeworks
    else:
        raise Exception


def parse_status(homework):
    """Функция, проверяющая статус домашнего задания."""
    homework_name = homework['homework_name']
    homework_status = homework.get('status')
    if homework_status is None:
        raise exceptions.KeyHomeworkStatusIsInaccessible
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES.get(homework_status)
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        raise exceptions.UnknownHomeworkStatus


def check_tokens():
    """Функция проверки доступности переменных окружения"""
    tokens = {
        'practicum_token': PRACTICUM_TOKEN,
        'telegram_token': TELEGRAM_TOKEN,
        'telegram_chat_id': TELEGRAM_CHAT_ID,
    }
    for key, value in tokens.items():
        if value is None:
            logging.error(f'{key} отсутствует')
            return False
    return True


def main():
    """Основная логика работы бота."""
    logger.info('Вы запустили Бота')
    # проверка обязательных переменных окружения
    if not check_tokens():
        logger.critical('Обязательные переменные окружения отсутствуют.')
        return None
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())
    # Проверка статуса домашней работы с определенной переодичностью
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            logging.info(f'Получили список работ {homeworks}')
            if len(homeworks) > 0:
                message = parse_status(homeworks[0])
                send_message(bot, message)
                logging.info('Заданий нет')
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
