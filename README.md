# Telegram_bot
## Описание:
Проект сервиса telegram_bot, работающий с API сервиса Практикум.Домашка.

Бот умеет:
- опрашивать API сервиса Практикум.Домашка с выбранной периодичностью и проверять статус отправленной на ревью домашней работы
- при обновлении статуса анализировать ответ API и отправлять Вам соответствующее уведомление в Telegram
- логировать свою работу и сообщать Вам о важных проблемах сообщением в Telegram 

## Системные требования
- Python 3.7+
- Works on Linux, Windows, macOS

## Используемые технологии:
- Python 3.7+
- Pytest
- Telegram Bot API
- Requests

## Запуск проекта:
Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Ekaterishe4ka/telegram_bot.git
cd telegram_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Создать файл виртуального окружения .env в корневой директории проекта:

```
touch .env
```

В нём указать свои ключи для токен API сервиса Практикум.Домашка и Telegram:

```
- PRAKTIKUM_TOKEN =
- TELEGRAM_TOKEN =
- TELEGRAM_CHAT_ID =
```

Запустить проект на локальной машине:

```
python homework.py
```
