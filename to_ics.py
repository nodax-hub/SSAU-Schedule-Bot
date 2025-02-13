import datetime
from copy import deepcopy
from dataclasses import dataclass

from parser import SSAUParser
from schedule import PairsSet, Week


@dataclass
class Event:
    """Класс для представления события в календаре iCal."""
    title: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    location: str = None
    description: str = None
    
    def to_ics(self) -> str:
        """Преобразует событие в формат iCal."""
        return f"""BEGIN:VEVENT
SUMMARY:{self.title}
DTSTART:{self.start_time.strftime('%Y%m%dT%H%M%S')}
DTEND:{self.end_time.strftime('%Y%m%dT%H%M%S')}
LOCATION:{self.location or ''}
DESCRIPTION:{self.description or ''}
STATUS:CONFIRMED
TRANSP:OPAQUE
BEGIN:VALARM
TRIGGER:-PT10M
ACTION:DISPLAY
END:VALARM
END:VEVENT
"""


def generate_ics_from_week(weeks: list[Week]) -> str:
    """Генерирует iCalendar строку на основе объекта Week."""
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Python//NONSGML v1.0//EN\n"
    
    for week in weeks:
        for day in week.days:
            for pairs_set in day.pairs:
                start_time, end_time = PairsSet.TIMES[pairs_set.number]
                
                for pair in pairs_set:
                    # Преобразуем время в datetime с учетом даты
                    event_start = datetime.datetime.combine(day.date, start_time)
                    event_end = datetime.datetime.combine(day.date, end_time)
                    
                    # Формируем описание и название события
                    title = pair.discipline_name
                    location = pair.place if pair.place else None
                    description = f"Преподаватель: {pair.teacher}" if pair.teacher else None
                    
                    # Создаем событие и добавляем его в ics content
                    ics_content += Event(title=title,
                                         start_time=event_start,
                                         end_time=event_end,
                                         location=location,
                                         description=description).to_ics()
    
    ics_content += "END:VCALENDAR"
    return ics_content


def create_ics_file(filename: str, weeks: list[Week]):
    """Создает .ics файл на основе объекта Week."""
    ics_content = generate_ics_from_week(weeks)
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
    group_id = int(input('Укажите ID вашей группы: '))
    subgroup = input('Укажите вашу подгруппу (опционально): ')
    print('Укажите интересующий вас диапазон.')
    start_number_week = input('Начиная с недели под номером: ') or SSAUParser.get_number_week()
    end_number_week = input('До (включительно) недели под номером: ')
    
    weeks = []
    for i in range(int(start_number_week), int(end_number_week) + 1):
        week = SSAUParser.get_week(group_id, i)
        if subgroup:
            week = filter_by_subgroup(week, int(subgroup))
        weeks.append(week)
    
    create_ics_file(f"{group_id}_{start_number_week}_{end_number_week}.ics", weeks)


if __name__ == '__main__':
    main()
