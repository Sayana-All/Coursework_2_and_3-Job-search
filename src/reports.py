import csv
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


class AbstractSaver(ABC):
    """Абстрактный класс для работы с входящими данными"""

    @abstractmethod
    def add_vacancy(self, vacancy):
        pass

    @abstractmethod
    def get_vacancies(self, criteria: dict):
        pass

    @abstractmethod
    def delete_vacancy(self, vacancy):
        pass


class JSONSaver(AbstractSaver):
    """Класс для сохранения вакансий в JSON-файл"""

    def __init__(self, filename: str = "vacancies.json"):
        """Конструктор для создания объектов класса JSONSaver"""
        self.__filename = DATA_DIR / filename
        os.makedirs(DATA_DIR, exist_ok=True)

    def add_vacancy(self, vacancy) -> None:
        """Метод для добавления вакансии в файл"""
        data = self._load_data()
        vacancy_dict = vacancy.to_dict()

        # Проверка на дубликаты по URL
        if not any(v.get("url") == vacancy_dict.get("url") for v in data):
            data.append(vacancy_dict)
            self._save_data(data)

    def get_vacancies(self, criteria: dict = None) -> list[dict]:
        """Метод для получения вакансии по заданным критериям"""
        data = self._load_data()
        if not criteria:
            return data
        return [v for v in data if all(v.get(k) == v for k, v in criteria.items())]

    def delete_vacancy(self, vacancy) -> None:
        """Метод для удаления вакансии из файла"""
        data = self._load_data()
        data = [v for v in data if v["url"] != vacancy.url]
        self._save_data(data)

    def _load_data(self) -> list:
        """Метод загрузки данных из файла"""
        try:
            with open(self.__filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Ошибка загрузки данных. Файл не обнаружен.")
            return []

    def _save_data(self, data: list) -> None:
        """Метод сохранения данных в файл"""
        with open(self.__filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def clear_file(self) -> None:
        """Метод для удаления файла с вакансиями"""
        if os.path.exists(self.__filename):
            os.remove(self.__filename)
            print(f"Файл '{self.__filename}' успешно удалён.")
        else:
            print("Файл не найден.")


class CSVSaver(AbstractSaver):
    """Класс для сохранения вакансий в CSV-файл"""

    def __init__(self, filename: str = "vacancies.csv"):
        """Конструктор для создания объектов класса CSVSaver"""
        self.__filename = DATA_DIR / filename
        os.makedirs(DATA_DIR, exist_ok=True)

    def add_vacancy(self, vacancy) -> None:
        """Метод для добавления вакансии в CSV-файл"""
        data = self.get_vacancies()
        vacancy_dict = vacancy.to_dict()

        # Проверка на дубликаты по URL
        if not any(v.get("url") == vacancy_dict.get("url") for v in data):
            file_exists = os.path.exists(self.__filename)
            with open(self.__filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=vacancy_dict.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(vacancy_dict)

    def get_vacancies(self, criteria: dict = None) -> list[dict]:
        """Метод для получения данных из CSV-файла"""
        if not os.path.exists(self.__filename):
            return []

        with open(self.__filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = list(reader)

        if not criteria:
            return data
        return [row for row in data if all(row.get(k) == v for k, v in criteria.items())]

    def delete_vacancy(self, vacancy) -> None:
        """Метод для удаления вакансии из CSV-файла"""
        if not os.path.exists(self.__filename):
            return
        with open(self.__filename, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        with open(self.__filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            writer.writerows(row for row in rows if row["url"] != vacancy.url)

    def clear_file(self) -> None:
        """Метод удаления CSV-файла"""
        if os.path.exists(self.__filename):
            os.remove(self.__filename)
            print(f"Файл '{self.__filename}' успешно удалён.")
        else:
            print("Файл не найден.")
