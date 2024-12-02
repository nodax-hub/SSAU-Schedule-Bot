import datetime
from copy import deepcopy
from dataclasses import dataclass

from parser import SSAUParser
from schedule import PairsSet, Week, Day, Pair


@dataclass
class Event:
    """Класс для представления события в календаре iCal."""
    title: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    location: str = None
    description: str = None
    summary: str = None

    def to_ics(self) -> str:
        """Преобразует событие в формат iCal."""
        return f"""BEGIN:VEVENT
SUMMARY:{self.title}
DTSTART:{self.start_time.strftime('%Y%m%dT%H%M%S')}
DTEND:{self.end_time.strftime('%Y%m%dT%H%M%S')}
LOCATION:{self.location or 'Не указано'}
DESCRIPTION:{self.description or 'Нет описания'}
STATUS:CONFIRMED
TRANSP:OPAQUE
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Напоминание о {self.title}
ACTION:DISPLAY
END:VALARM
END:VEVENT
"""


def generate_ics_from_week(week: Week) -> str:
    """Генерирует iCalendar строку на основе объекта Week."""
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Python//NONSGML v1.0//EN\n"

    for day in week.days:
        for pairs_set in day.pairs:
            start_time, end_time = PairsSet.TIMES[pairs_set.number]

            for pair in pairs_set:
                # Преобразуем время в datetime с учетом даты
                event_start = datetime.datetime.combine(day.date, start_time)
                event_end = datetime.datetime.combine(day.date, end_time)

                # Формируем описание и название события
                title = pair.discipline_name
                location = pair.place or "Не указано"
                description = f"Преподаватель: {pair.teacher}" if pair.teacher else "Преподаватель не указан"

                # Создаем событие и добавляем его в ics content
                ics_content += Event(title=title, start_time=event_start, end_time=event_end,
                                     location=location, description=description).to_ics()

    ics_content += "END:VCALENDAR"
    return ics_content


def create_ics_file(filename: str, week: Week):
    """Создает .ics файл на основе объекта Week."""
    ics_content = generate_ics_from_week(week)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(ics_content)
    print(f"Файл {filename} успешно создан!")


def filter_by_subgroup(week: Week, subgroup: int) -> Week:
    filtered_week = deepcopy(week)
    for day in filtered_week.days:
        for pairs_set in day.pairs:
            for pair in pairs_set:
                if pair.subgroups and subgroup not in pair.subgroups:
                    pairs_set.pairs_set.remove(pair)

    return filtered_week


def main():
    group_id = int(input('ID группы:'))
    subgroup = int(input('Подгруппа:'))
    number_week = int(input('До номера недели:'))

    for i in range(SSAUParser.get_number_week(), number_week + 1):
        week = SSAUParser.get_week(group_id, i)
        create_ics_file(f"{group_id}_{i}.ics",
                        filter_by_subgroup(week, subgroup))


if __name__ == '__main__':
    main()
