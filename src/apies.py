from abc import ABC, abstractmethod

import requests


class AbstractAPI(ABC):
    """Абстрактный класс для работы с API вакансий"""

    @abstractmethod
    def get_employers(self) -> list[dict]:
        """Абстрактный метод получения компаний-работодателей"""
        pass

    @abstractmethod
    def get_employer_vacancies(self, employer_id: int) -> list[dict]:
        """Абстрактный метод получения вакансий"""
        pass


class HeadHunterAPI(AbstractAPI):
    """Класс для работы с API платформы hh.ru"""

    def __init__(self):
        """Инициализация с приватными атрибутами"""
        self.__base_url = "https://api.hh.ru/"
        self.employers = [
            {"id": 3529, "name": "Сбер", "alternate_url": "https://hh.ru/employer/3529"},
            {"id": 907345, "name": "Альфа-Банк", "alternate_url": "https://hh.ru/employer/907345"},
            {"id": 78638, "name": "Тинькофф", "alternate_url": "https://hh.ru/employer/78638"},
            {"id": 2748, "name": "Ростелеком", "alternate_url": "https://hh.ru/employer/2748"},
            {"id": 3776, "name": "МТС", "alternate_url": "https://hh.ru/employer/3776"},
            {"id": 4934, "name": "Билайн", "alternate_url": "https://hh.ru/employer/4934"},
            {"id": 1740, "name": "Яндекс", "alternate_url": "https://hh.ru/employer/1740"},
            {"id": 41862, "name": "VK", "alternate_url": "https://hh.ru/employer/41862"},
            {"id": 2180, "name": "Ozon", "alternate_url": "https://hh.ru/employer/2180"},
            {"id": 87021, "name": "Wildberries", "alternate_url": "https://hh.ru/employer/87021"},
        ]

    def get_employers(self) -> list[dict]:
        """Метод для получения списка работодателей"""
        return self.employers

    def get_employer_vacancies(self, employer_id: int) -> list[dict]:
        """Публичный метод получения списка вакансий по ID работодателя с валидацией данных"""
        url = f"{self.__base_url}vacancies"
        params = {"employer_id": employer_id, "per_page": 100, "area": 113}  # Россия

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "items" not in data:
                print(f"Неожиданный формат ответа API для employer_id {employer_id}")
                return []

            vacancies = data["items"]
            return vacancies if isinstance(vacancies, list) else []

        except requests.RequestException as e:
            print(f"Ошибка при запросе вакансий для employer_id {employer_id}: {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка при обработке вакансий: {e}")
            return []
