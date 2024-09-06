"""
Выполняет парсинг расписания на неделю для указанной группы
Также есть функция для парсинга начала семестра определённой группы
"""
import datetime
import re
from functools import lru_cache

import requests
from bs4 import BeautifulSoup

from schedule import PairsSet, Week, Day, Pair


class SSAUParser:
    _URL = 'https://ssau.ru/rasp'

    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/106.0.0.0 YaBrowser/22.11.2.807 '
                      'Yowser/2.5 Safari/537.36'
    }

    @classmethod
    def _get_soup(cls, group_id: int, selected_week: int = None) -> BeautifulSoup:

        url = f"{cls._URL}?groupId={group_id}"

        if selected_week:
            url += f"&selectedWeek={selected_week}"

        response = requests.get(url, headers=cls._HEADERS)
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f'Server returned {response.status_code} status code.')
        soup = BeautifulSoup(response.text, 'lxml')
        return soup

    @staticmethod
    def _parse_times(soup: BeautifulSoup) -> list[tuple[datetime.time, datetime.time]]:
        def create_time_from_item(item) -> datetime.time:
            """Принимает ячейку времени с текстом в формате ` 8:00 ` преобразует в класс datetime.time"""
            text = item.text.strip()
            hour, minute = text.split(':')
            return datetime.time.fromisoformat(f"{hour.zfill(2)}:{minute.zfill(2)}:00")

        times = []
        for schedule_time in soup.find_all("div", class_="schedule__time"):
            start_time_item, end_time_item = schedule_time.find_all("div", class_="schedule__time-item")
            times.append((create_time_from_item(start_time_item), create_time_from_item(end_time_item)))

        return times

    @staticmethod
    def _parse_dates(soup: BeautifulSoup) -> list[datetime.date]:
        dates = []

        for schedule_date in soup.find_all("div", class_="schedule__item schedule__head"):
            if date_element := schedule_date.find("div", class_="caption-text schedule__head-date"):
                day, month, year = map(int, date_element.text.strip().split('.'))
                dates.append(datetime.date(year, month, day))

        return dates

    @staticmethod
    def _get_pair_type(pair: BeautifulSoup):
        for pair_type in Pair.PAIR_TYPES:
            class_pair_type = f"schedule__lesson-type-color lesson-type-{pair_type}__color"
            if pair.find("div", class_=class_pair_type):
                return pair_type

    @classmethod
    def _get_discipline_name(cls, pair) -> str:
        return getattr(pair.find("div", class_="body-text schedule__discipline"), 'text', '').strip()

    @classmethod
    def _get_place(cls, pair) -> str:
        return getattr(pair.find("div", class_="caption-text schedule__place"), 'text', '').strip()

    @classmethod
    def _get_teacher(cls, pair) -> str:
        return getattr(pair.find("div", class_="schedule__teacher"), 'text', '').strip()

    @classmethod
    def _parse_pairs_set(cls, soup_item: BeautifulSoup, time: tuple[datetime.time, datetime.time]) -> PairsSet:
        pairs_set = []
        for pair in soup_item.find_all("div", class_="schedule__lesson"):

            pair_type = cls._get_pair_type(pair)
            discipline_name = cls._get_discipline_name(pair)
            place = cls._get_place(pair)
            teacher = cls._get_teacher(pair)

            pairs_set.append(Pair(discipline_name, teacher, place, pair_type))

        return PairsSet(PairsSet.define_pair_number_by_time(time), pairs_set)

    @classmethod
    def _create_week(cls, soup: BeautifulSoup, number_week: int) -> Week:
        days = [Day(date) for date in cls._parse_dates(soup)]

        amount_header_items = 7
        item_iter = iter(soup.find_all("div", class_="schedule__item")[amount_header_items:])

        for time in cls._parse_times(soup):
            for day in days:
                day.pairs.append(cls._parse_pairs_set(next(item_iter), time))

        for day in days:
            day.strip_day()

        return Week(number_week, days)

    @staticmethod
    def _parse_start_semester(soup: BeautifulSoup) -> datetime.date:
        """Функция для получения даты начала семестра для указанной группы"""
        info = soup.find('div', class_='body-text info-block__semester')
        day, month, year = map(int, re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', info.text).group(0).split('.'))
        return datetime.date(year, month, day)

    @staticmethod
    def _get_date_start_semester(cur_date: datetime.date) -> datetime.date:
        """
        Если текущий месяц лежит в диапазоне [сентябрь; январь],
        то это первая половина учебного года и начало семестра будет 1 сентября.
        Будем считать, что вторая половина учебного года начинается в первый понедельник февраля.
        """

        if 9 <= cur_date.month <= 12:
            return datetime.date(cur_date.year, 9, 1)

        if cur_date.month == 1:
            return datetime.date(cur_date.year - 1, 9, 1)

        # Находим первое февраля для заданного года
        start_date = datetime.date(cur_date.year, 2, 1)
        day_of_week = start_date.weekday()

        # Если 1 февраля не является понедельником, находим следующий понедельник
        if day_of_week != 0:
            start_date += datetime.timedelta(days=(7 - day_of_week))

        return start_date

    @classmethod
    def _get_date_first_monday(cls, date):
        # вернёт дату первого понедельника в данном месяце

        # Начинаем с первого числа месяца
        date = datetime.date(date.year, date.month, 1)

        # Проверяем, является ли первое число месяца понедельником
        if date.weekday() == 0:
            return date

        # Если нет, находим дату первого понедельника
        days_to_monday = (7 - date.weekday()) % 7
        first_monday_date = date + datetime.timedelta(days=days_to_monday)

        return first_monday_date

    @classmethod
    def get_number_week(cls, date: datetime.date, start_semester: datetime.date = None) -> int:
        """Функция для определения номера текущей недели"""
        if start_semester is None:
            start_semester = cls._get_date_start_semester(date)

        date_first_learn_week = cls._get_date_first_monday(start_semester)
        return ((date - date_first_learn_week) // 7).days + 1

    @classmethod
    @lru_cache
    def get_week(cls, group_id: int, number_week: int) -> Week:
        """Вернёт расписание для указанной группы на указанную неделю"""
        soup = cls._get_soup(group_id, number_week)
        return cls._create_week(soup, number_week)

    @classmethod
    def get_day(cls, group_id: int, date: datetime.date) -> Day:
        if date.weekday() == 6:
            return Day(date)

        week = cls.get_week(group_id, cls.get_number_week(date))
        return week.days[date.weekday()]
