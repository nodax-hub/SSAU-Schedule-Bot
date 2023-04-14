"""
Выполняет парсинг расписания на неделю для указанной группы
Также есть функция для парсинга начала семетра определённой группы
"""

import logging
import math
import re
from functools import lru_cache

import requests
from bs4 import BeautifulSoup

from schedule import *

URL = 'https://ssau.ru/rasp'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/106.0.0.0 YaBrowser/22.11.2.807 '
                  'Yowser/2.5 Safari/537.36'
}


def reshape(roll, length):
    """
    Создаёт из одномерного массива двумерный, объединяя в строку по {param} элементов.
    :param roll: исходный список.
    :param length: По сколько элементов объединять.
    :return: Новый список с объединёнными массивами
    """
    return [roll[(cur_pos := i * length):cur_pos + length] for i in range(math.ceil(len(roll) / length))]


@lru_cache
def parse_week(group_id: int, selected_week: int) -> Week:
    """Вернёт расписание для указанной группы на указанную неделю"""
    response = requests.get(f"{URL}?groupId={group_id}&selectedWeek={selected_week}", headers=HEADERS)
    soup = BeautifulSoup(response.text, 'lxml')

    days_dates: list[datetime.date] = []

    pairs: list[PairsSet] = []
    # добавляем пары или дату пробегая одну за другой ячейки таблицы (данная таблица читается построчно)
    for item in soup.find_all("div", class_="schedule__item"):
        # Случай когда рассматриваемая ячейка является заголовком (header)
        if "schedule__head" in item["class"]:

            if date := item.find("div", class_="caption-text schedule__head-date"):
                day, month, year = map(int, date.text.strip().split('.'))
                days_dates.append(datetime.date(year, month, day))
            continue

        # Сразу считаем номер текущей пары
        number_pair = len(pairs) // AMOUNT_DAYS + 1

        # Случай когда рассматриваемая ячейка является парой (содержит имя лекции)
        if lessons := item.find_all("div", class_="schedule__lesson"):
            # Найдём множество пар в это время
            tmp_set_pairs = list()
            for pair in lessons:
                # Перебор всех типов пар [1, 4]
                discipline_name = '?'
                pair_type = 1
                while pair_type <= 4:
                    if discipline_name := pair.find("div",
                                                    class_=f"body-text schedule__discipline lesson-color "
                                                           f"lesson-color-type-{pair_type}"):
                        discipline_name = discipline_name.text.strip()
                        break
                    pair_type += 1
                else:
                    logging.debug('[!] Необработанный тип лекции')

                place = getattr(pair.find("div", class_="caption-text schedule__place"), 'text', '').strip()
                teacher = getattr(pair.find("div", class_="schedule__teacher"), 'text', '').strip()

                tmp_set_pairs.append(Pair(discipline_name, teacher, place, str(pair_type)))

            pairs.append(PairsSet(number_pair, tmp_set_pairs))
        # В противном случае если ячейка пуста считаем пару окном
        elif item.text == "":
            pairs.append(PairsSet(number_pair))

        # Пропускаем если ячейка не подходит не под один из вариантов
        else:
            logging.debug('[!] Необработанная непустая ячейка')

    days = []
    for date, *pairs in zip(days_dates, *reshape(pairs, AMOUNT_DAYS)):
        days.append(Day(date, pairs))
    return Week(selected_week, days)


@lru_cache
def parse_start_semester(group_id: int) -> datetime.date:
    """Функция для получения даты начала семестра для указанной группы"""
    response = requests.get(f"{URL}?groupId={group_id}", headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    info = soup.find('div', class_='body-text info-block__semester')
    day, month, year = map(int, re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', info.text).group(0).split('.'))
    return datetime.date(year, month, day)


def get_cur_week(cur_date: datetime.date = datetime.date.today(), start_semester: datetime.date = None):
    """Функция для определения текущей недели"""
    if start_semester is None:
        # Определяем какой сейчас должен быть семестр по текущему месяцу
        start_semester = datetime.date(cur_date.year, 9, 1) \
            if 9 <= cur_date.month <= 12 else \
            datetime.date(cur_date.year, 2, 6)

    date_first_learn_week = start_semester - datetime.timedelta(days=start_semester.weekday())
    return ((cur_date - date_first_learn_week) // 7).days + 1


def get_day(group_id: int, date: datetime.date) -> Day:
    if date.weekday() == 6:
        return Day(date)
    week = parse_week(group_id, get_cur_week(cur_date=date))
    return week.days[date.weekday()]


def today(group_id: int) -> Day:
    return get_day(group_id, datetime.date.today())


def tomorrow(group_id: int) -> Day:
    return get_day(group_id, datetime.date.today() + datetime.timedelta(days=1))
