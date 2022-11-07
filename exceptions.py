class InvalidHttpStatus(Exception):
    """Статут ответа от API Яндекс.Практикума отличный от 200."""

    pass


class UnknownHomeworkStatus(Exception):
    """Неизвестный статус домашнего задания."""

    pass
