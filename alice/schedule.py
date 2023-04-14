import datetime

from prettytable import PrettyTable

# Кол-во дней в учебной недели
AMOUNT_DAYS = 6


class Pair:
    """Класс одной конкретной пары"""

    def __init__(self, discipline_name: str, teacher: str = None, place: str = None, pair_type: str = None):
        self.discipline_name = discipline_name
        self.teacher = teacher
        self.place = place
        self.pair_type = pair_type


class PairsSet:
    """Класс набора учебных пар в одно время"""

    def __init__(self, number: int, pairs_set: list[Pair] = None):
        self.number = number
        self.pairs_set = pairs_set or []

    def __str__(self):
        return f"№{self.number} - {' | '.join(pair.discipline_name for pair in self.pairs_set)}"

    def __len__(self):
        return len(self.pairs_set)

    def __iter__(self):
        return iter(self.pairs_set)


class Day:
    """Класс одного учебного дня"""

    def __init__(self, date: datetime.date, pairs: list[PairsSet] = None):
        self.date = date
        self.pairs = pairs or []

        # TODO: подумать над улучшением алгоритмов удаления крайних пустых пар
        self.delete_empty_start_pairs()
        self.delete_empty_end_pairs()

    def __str__(self):
        table = PrettyTable()
        table.field_names = [str(self.date)]
        table.align = 'l'
        for pair in self.pairs:
            table.add_row([pair])
        return str(table)

    def delete_empty_start_pairs(self):
        """Удаляет все пустые пары в начале дня, если конечно таковые имеются."""
        for pair in self.pairs[:]:
            if len(pair):
                break
            self.pairs.pop(0)

    def delete_empty_end_pairs(self):
        """Удаляет все пустые пары в конце, если конечно таковые имеются."""
        for pair in self.pairs[::-1]:
            if len(pair):
                break
            self.pairs.pop()


class Week:
    """Класс одной учебной недели"""
    number_week: int
    days: list[Day]

    def __init__(self, number_week, days):
        assert len(days) == AMOUNT_DAYS
        self.number_week = number_week
        self.days = days

    def __iter__(self):
        return iter(self.days)
