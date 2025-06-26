from abc import ABC, abstractmethod
import requests


class AbstractAPI(ABC):
    """Абстрактный класс для работы с API вакансий"""

    @abstractmethod
    def get_vacancies(self, query: str):
        pass


class HeadHunterAPI(AbstractAPI):
    """Класс для работы с API-сервисом сайта hh.ru"""

    def __init__(self):
        """Конструктор для создания объектов класса HeadHunterAPI"""
        self.base_url = "https://api.hh.ru/vacancies"

    def get_vacancies(self, query: str) -> list[dict]:
        """Метод для получения списка вакансий по запросу пользователя"""
        params = {
            "text": query,
            "area": 113,  # 113 — Россия
            "per_page": 100
        }
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json().get("items", [])
