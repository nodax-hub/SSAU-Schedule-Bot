import datetime
from dataclasses import dataclass, field
from itertools import zip_longest

from prettytable import PrettyTable


@dataclass
class Pair:
    """Класс одной конкретной пары"""
    discipline_name: str
    teacher: str = None
    place: str = None
    pair_type: int = None
    
    PAIR_TYPES = {
        1: 'Лекция',
        2: 'Лабораторная',
        3: 'Практика',
        4: 'Другое',
        5: 'Экзамен',
        6: 'Консультация',
        8: 'Зачёт',
    }


@dataclass
class PairsSet:
    """Класс набора учебных пар в одно время"""
    number: int
    pairs_set: list[Pair] = field(default_factory=list, compare=False)
    
    TIMES = {
        1: (datetime.time(8, 0), datetime.time(9, 35)),
        2: (datetime.time(9, 45), datetime.time(11, 20)),
        3: (datetime.time(11, 30), datetime.time(13, 5)),
        4: (datetime.time(13, 30), datetime.time(15, 5)),
        5: (datetime.time(15, 15), datetime.time(16, 50)),
        6: (datetime.time(17, 0), datetime.time(18, 35)),
    }
    
    @classmethod
    def define_pair_number_by_time(cls, time: tuple[datetime.time, datetime.time]):
        return next((k for k, v in cls.TIMES.items() if v == time), None)
    
    def __str__(self):
        if len(self):
            return f"№{self.number} - {' | '.join(pair.discipline_name for pair in self.pairs_set)}"
        return ""
    
    def __len__(self):
        return len(self.pairs_set)
    
    def __iter__(self):
        return iter(self.pairs_set)


@dataclass
class Day:
    """Класс одного учебного дня"""
    date: datetime.date
    pairs: list[PairsSet] = field(default_factory=list)
    
    def __str__(self):
        table = PrettyTable()
        table.field_names = [str(self.date)]
        table.align = 'l'
        for pair in self.pairs:
            table.add_row([pair])
        return str(table)
    
    def strip_day(self):
        self.delete_empty_start_pairs()
        self.delete_empty_end_pairs()
    
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


@dataclass
class Week:
    """Класс одной учебной недели"""
    number_week: int
    days: list[Day]
    
    def __iter__(self):
        return iter(self.days)
    
    def __str__(self):
        table = PrettyTable()
        table.align = 'l'
        table.add_column('Время',
                         [f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
                          for start, end in PairsSet.TIMES.values()])
        for day in self.days:
            pairs = [PairsSet(i) for i in PairsSet.TIMES]
            
            for pair in day.pairs:
                pairs[pair.number - 1] = pair
                
            table.add_column(day.date.strftime("%d.%m.%Y"), pairs)
        
        return str(table)
