import calendar
import datetime
import re

from fuzzywuzzy import process
from requests import HTTPError, ConnectionError

from parser import SSAUParser
from schedule import Day


def say_day(day: Day) -> str:
    response = f"Расписание на {day.date.strftime('%d.%m.%Y')}.\nИ так слушайте:\n"
    if len(day.pairs):
        if day.pairs[0].number != 1:
            response += f"Вам к паре номер {day.pairs[0].number}.\n"
        if len(day.pairs[0].pairs_set) == 1:
            response += f"Место: {day.pairs[0].pairs_set[0].place}.\n"
        for pair in day.pairs:
            response += f"{pair}.\n"
    else:
        response += "По моим данным в этот день нет пар."
    return response


def define_date_by_phrase(phrase):
    week_days = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    date_of_interest = datetime.date.today()
    if 'сегодня' in phrase:
        pass
    elif 'завтра' in phrase:
        date_of_interest += datetime.timedelta(days=1)
    else:
        day, percent = process.extractOne(phrase, week_days)
        if percent >= 70:
            date_of_interest += datetime.timedelta(days=week_days.index(day) - date_of_interest.weekday())
        else:
            raise ValueError
    return date_of_interest


def parse_date_from_phrase(phrase: str) -> datetime:
    today = datetime.datetime.today()

    # Карта простых фраз на дни
    days_map = {
        "сегодня": 0,
        "завтра": 1,
        "послезавтра": 2,
        "вчера": -1
    }

    # Обрабатываем "сегодня", "завтра" и т.д.
    for word, delta in days_map.items():
        if word in phrase:
            return today + datetime.timedelta(days=delta)

    # Обрабатываем дни недели
    weekdays_map = {
        "понедельник": 0,
        "вторник": 1,
        "среда": 2,
        "четверг": 3,
        "пятница": 4,
        "суббота": 5,
        "воскресенье": 6
    }

    # Проверяем, говорится ли о следующей неделе
    if "следующий" in phrase or "следующая" in phrase:
        next_week = True
    else:
        next_week = False

    for day_name, weekday in weekdays_map.items():
        if day_name in phrase:
            current_weekday = today.weekday()
            delta_days = (weekday - current_weekday) % 7
            if next_week or delta_days == 0:
                delta_days += 7
            return today + datetime.timedelta(days=delta_days)

    # Обрабатываем числовые даты типа "на 20 число" или "на 30 апреля"
    day_match = re.search(
        r'(\d{1,2})\s*(число|января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)',
        phrase)

    if day_match:
        day = int(day_match.group(1))
        month = today.month

        # Определяем месяц по тексту
        month_map = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5,
            "июня": 6, "июля": 7, "августа": 8, "сентября": 9, "октября": 10,
            "ноября": 11, "декабря": 12
        }
        for month_name, month_num in month_map.items():
            if month_name in phrase:
                month = month_num
                break

        # Проверяем, что если месяц прошел в этом году, используем следующий год
        year = today.year
        if month < today.month or (month == today.month and day < today.day):
            year += 1

        # Возвращаем дату
        return datetime.datetime(year, month, day)

    # Обрабатываем фразы типа "через 3 дня" или "3 дня назад"
    relative_days_match = re.search(r'через\s*(\d+)\s*(день|дня|дней)', phrase)
    if relative_days_match:
        days = int(relative_days_match.group(1))
        return today + datetime.timedelta(days=days)

    relative_days_ago_match = re.search(r'(\d+)\s*(день|дня|дней)\s*назад', phrase)
    if relative_days_ago_match:
        days = int(relative_days_ago_match.group(1))
        return today - datetime.timedelta(days=days)

    # Обрабатываем фразы "через X недель" или "X недель назад"
    relative_weeks_match = re.search(r'через\s*(\d+)\s*(неделю|недели|недель)', phrase)
    if relative_weeks_match:
        weeks = int(relative_weeks_match.group(1))
        return today + datetime.timedelta(weeks=weeks)

    relative_weeks_ago_match = re.search(r'(\d+)\s*(неделю|недели|недель)\s*назад', phrase)
    if relative_weeks_ago_match:
        weeks = int(relative_weeks_ago_match.group(1))
        return today - datetime.timedelta(weeks=weeks)

    # Обрабатываем фразы "через X месяцев" или "X месяцев назад"
    relative_months_match = re.search(r'через\s*(\d+)\s*(месяц|месяца|месяцев)', phrase)
    if relative_months_match:
        months = int(relative_months_match.group(1))
        year = today.year + (today.month + months - 1) // 12
        month = (today.month + months - 1) % 12 + 1
        day = min(today.day, calendar.monthrange(year, month)[1])  # Корректируем день для конца месяца
        return datetime.datetime(year, month, day)

    relative_months_ago_match = re.search(r'(\d+)\s*(месяц|месяца|месяцев)\s*назад', phrase)
    if relative_months_ago_match:
        months = int(relative_months_ago_match.group(1))
        year = today.year - (months // 12)
        month = (today.month - months) % 12 or 12
        if today.month - months <= 0:
            year -= 1
        day = min(today.day, calendar.monthrange(year, month)[1])  # Корректируем день для конца месяца
        return datetime.datetime(year, month, day)

    # Обрабатываем фразы "через X лет" или "X лет назад"
    relative_years_match = re.search(r'через\s*(\d+)\s*(год|года|лет)', phrase)
    if relative_years_match:
        years = int(relative_years_match.group(1))
        return datetime.datetime(today.year + years, today.month, today.day)

    relative_years_ago_match = re.search(r'(\d+)\s*(год|года|лет)\s*назад', phrase)
    if relative_years_ago_match:
        years = int(relative_years_ago_match.group(1))
        return datetime.datetime(today.year - years, today.month, today.day)

    # Если ничего не подошло, выбрасываем исключение
    raise ValueError("Невозможно определить дату из фразы.")


def schedule_on_day(phrase: str, group_id: int) -> str:
    try:
        date_of_interest = parse_date_from_phrase(phrase)
        return say_day(SSAUParser.get_day(group_id, date_of_interest))

    except ValueError:
        return 'Не могу определить дату из вашего сообщения. Пожалуйста, укажите день или диапазон дат.'

    except HTTPError as e:
        return f'Извините сайт не отвечает, проверьте указанный вами id группы, попробуйте позже или, ' \
               f'если проблема не исчезнет, свяжитесь с разработчиком. \n{e}'
    except ConnectionError as e:
        return f'Не удаётся установить соединение с сайтом. Попробуйте позже или свяжитесь с разработчиком. \n{e}'


def handler(event: dict, context) -> dict:
    # TODO: Добавить логику сохранения id группы в хранилище приложения
    user_state_update = {}
    end_session = 'false'
    phrase = event['request']['original_utterance'].lower()

    if event['session']['new'] and len(phrase) == 0:
        text = 'Привет. Для того чтобы узнать своё расписание просто спроси меня: "расписание на сегодня". ' \
               'Если возникнут вопросы скажите помощь.'

    elif 'помощь' in phrase:
        text = 'Для того чтобы я могла сказать ваше расписание, мне необходимо получить от вас id группы. ' \
               'Затем вы можете попросить меня сказать расписание на сегодня или на завтра.'

    elif 'спасибо' in phrase:
        text = 'Всегда рада помочь.'
        end_session = 'true'

    elif phrase.isdigit():
        user_state_update['group_id'] = int(phrase)
        text = 'Вы успешно сменили id своей группы.'

    elif 'group_id' not in event['state']['user']:
        text = 'Напиши мне id своей группы.'

    else:
        group_id = event['state']['user']['group_id']
        text = schedule_on_day(phrase, group_id)

    return {
        'version': event['version'],
        'session': event['session'],
        'response': {
            'text': text,
            'end_session': end_session
        },
        'user_state_update': user_state_update,
    }
