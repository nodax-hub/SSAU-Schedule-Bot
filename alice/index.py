import datetime

from requests import HTTPError, ConnectionError
from fuzzywuzzy import process
from parser import get_day
from schedule import Day


def say_day(day: Day) -> str:
    response = f"Расписание на {day.date.strftime('%d.%m.%Y')}.\nИ так слушайте:\n"
    if len(day.pairs):
        if day.pairs[0].number != 1:
            response += f"Вам к паре номер {day.pairs[0].number}\n"
        for pair in day.pairs:
            response += f"{pair}.\n"
    else:
        response += "По моим данным в этот день нет пар."
    return response


def schedule_on_day(phrase: str, group_id: int) -> str:
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
            return 'Извините, я не знаю что ответить.'

    try:
        return say_day(get_day(group_id, date_of_interest))
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
