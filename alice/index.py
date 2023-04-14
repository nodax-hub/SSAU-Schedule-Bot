from parser import today, tomorrow
from schedule import Day


def say_day(day: Day) -> str:
    response = f"Расписание на {day.date.strftime('%d.%m.%Y')}.\nИ так слушайте:\n"
    if len(day.pairs):
        for pair in day.pairs:
            response += f"{pair}.\n"
    else:
        response += "В этот день нет пар."
    return response


def handler(event: dict, context) -> dict:
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

    elif 'сегодня' in phrase:
        text = say_day(today(event['state']['user']['group_id']))

    elif 'завтра' in phrase:
        text = say_day(tomorrow(event['state']['user']['group_id']))

    else:
        text = 'Извините, я не знаю что ответить.'

    return {
        'version': event['version'],
        'session': event['session'],
        'response': {
            'text': text,
            'end_session': end_session
        },
        'user_state_update': user_state_update,
    }
