from abc import ABC, abstractmethod

import requests


class AbstractAPI(ABC):
    """Абстрактный класс для работы с API вакансий"""

    @abstractmethod
    def get_vacancies(self, keyword: str) -> list[dict]:
        """Публичный метод получения вакансий"""
        pass

    def _check_private_method(self):
        """Метод для проверки наличия приватного метода в дочерних классах"""
        if not hasattr(self, f"_{self.__class__.__name__}__connect_to_api"):
            raise NotImplementedError("Private __connect_to_api not implemented")


class HeadHunterAPI(AbstractAPI):
    """Класс для работы с API платформы hh.ru"""

    def __init__(self):
        """Инициализация с приватными атрибутами"""
        self.__base_url = "https://api.hh.ru/vacancies"
        self.__default_params = {"area": 113, "per_page": 100}

    def __connect_to_api(self, url: str, params: dict) -> requests.Response:
        """Приватный метод подключения к API hh.ru"""
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения: {e}")
            raise

    def get_vacancies(self, query: str) -> list[dict]:
        """Публичный метод получения вакансий по заданной строке"""
        self._check_private_method()
        params = self.__default_params.copy()
        params["text"] = query

        try:
            response = self.__connect_to_api(self.__base_url, params)
            return response.json().get("items", [])
        except Exception:
            return []
