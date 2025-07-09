import unittest
from unittest.mock import MagicMock, patch

import requests

from src.apies import AbstractAPI, HeadHunterAPI


class TestAbstractAPI(unittest.TestCase):
    """Тесты для абстрактного класса API"""

    def test_abstract_methods(self):
        """Проверка, что абстрактные методы действительно абстрактные"""
        with self.assertRaises(TypeError):
            api = AbstractAPI()


class TestHeadHunterAPI(unittest.TestCase):
    """Тесты для класса HeadHunterAPI"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.api = HeadHunterAPI()
        self.test_employer_id = 3529  # ID Сбера
        self.mock_response = {
            "items": [
                {
                    "name": "Python Developer",
                    "alternate_url": "https://hh.ru/vacancy/123",
                    "salary": {"from": 100000, "to": 150000, "currency": "RUR"},
                    "snippet": {"requirement": "Опыт работы с Python"},
                }
            ]
        }

    def test_get_employers(self):
        """Тест получения списка работодателей"""
        employers = self.api.get_employers()
        self.assertIsInstance(employers, list)
        self.assertEqual(len(employers), 10)
        self.assertEqual(employers[0]["name"], "Сбер")
        self.assertEqual(employers[-1]["name"], "Wildberries")

    @patch("requests.get")
    def test_get_employer_vacancies_success(self, mock_get):
        """Тест успешного получения вакансий"""
        # Настраиваем mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        vacancies = self.api.get_employer_vacancies(self.test_employer_id)

        self.assertIsInstance(vacancies, list)
        self.assertEqual(len(vacancies), 1)
        self.assertEqual(vacancies[0]["name"], "Python Developer")

        # Проверяем параметры запроса
        mock_get.assert_called_once_with(
            "https://api.hh.ru/vacancies",
            params={"employer_id": self.test_employer_id, "per_page": 100, "area": 113},
            timeout=30,
        )

    @patch("requests.get")
    def test_get_employer_vacancies_no_items(self, mock_get):
        """Тест случая, когда API возвращает неожиданный формат"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"wrong_key": []}
        mock_get.return_value = mock_response

        vacancies = self.api.get_employer_vacancies(self.test_employer_id)
        self.assertEqual(vacancies, [])

    @patch("requests.get")
    def test_get_employer_vacancies_request_exception(self, mock_get):
        """Тест обработки ошибки запроса"""
        mock_get.side_effect = requests.RequestException("Connection error")

        vacancies = self.api.get_employer_vacancies(self.test_employer_id)
        self.assertEqual(vacancies, [])

    @patch("requests.get")
    def test_get_employer_vacancies_json_decode_error(self, mock_get):
        """Тест обработки ошибки декодирования JSON"""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        vacancies = self.api.get_employer_vacancies(self.test_employer_id)
        self.assertEqual(vacancies, [])

    def test_get_employer_vacancies_invalid_id(self):
        """Тест с несуществующим ID работодателя"""
        vacancies = self.api.get_employer_vacancies(-1)
        self.assertEqual(vacancies, [])

    @patch("requests.get")
    def test_get_employer_vacancies_empty_response(self, mock_get):
        """Тест пустого ответа от API"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        vacancies = self.api.get_employer_vacancies(self.test_employer_id)
        self.assertEqual(vacancies, [])


if __name__ == "__main__":
    unittest.main()
