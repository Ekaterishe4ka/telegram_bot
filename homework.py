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
        raise exceptions.SendMessageFailure(
            'При отправке сообщения произошла ошибка')
    else:
        logger.info('Сообщение отправлено успешно')


def get_api_answer(current_timestamp):
    """Функция запроса к API Яндекс.Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise exceptions.UnableAccessAPI(f'Ошибка доступа {error}. '
                              f'Проверить API: {ENDPOINT}, '
                              f'Токен авторизации: {HEADERS}, '
                              f'Запрос с момента времени: {params}')
    else:
        if response.status_code != HTTPStatus.OK:
            raise exceptions.InvalidHttpStatus(
                f'Ошибка ответа сервера. Проверить API: {ENDPOINT}, '
                f'Токен авторизации: {HEADERS}, '
                f'Запрос с момента времени: {params},'
                f'Статус страницы не 200 и равен: {response.status_code}')
        response_content = response.json()
        return response_content


def check_response(response):
    """Функция проверки корректности ответа API Яндекс.Практикум."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не словарь')
    if 'homeworks' not in response:
        raise KeyError('Ключ "homeworks" в ответе API Яндекс.Практикум отсутствует')
    homeworks = response['homeworks']
    if not homeworks:
        raise KeyError('Отсутствует статус homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Неверный тип данных у homeworks')
    if 'current_date' not in response:
        raise KeyError(
            'Ключ current_date в ответе API Яндекс.Практикум отсутствует')
    return homeworks


def parse_status(homework):
    """Функция, проверяющая статус домашнего задания."""
    if not isinstance(homework, dict):
        raise KeyError('Ошибка типа данных: homework - не словарь')
    if 'homework_name' not in homework:
        raise KeyError('В ответе API нет ключа homework_name')
    if 'status' not in homework:
        raise KeyError('В ответе API нет ключа homework_status')
    homework_name = homework['homework_name']
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        raise exceptions.UnknownHomeworkStatus(
            'f Cтатуса {homework_status} нет в словаре')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция проверки доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    logger.info('Вы запустили Бота')
    # проверка обязательных переменных окружения
    if not check_tokens():
        logger.critical('Обязательные переменные окружения отсутствуют.')
        return None
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
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
            current_timestamp = int(time.time())
        except exceptions.SendMessageFailure as error:
            logger.error(f'Боту не удалось отправить сообщение: {error}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
