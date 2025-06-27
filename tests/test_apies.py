from unittest.mock import patch, Mock

import pytest
import requests

from src.apies import AbstractAPI, HeadHunterAPI


def test_abstract_api(abstract_api):
    """Проверка, что абстрактный класс нельзя создать напрямую"""
    with pytest.raises(TypeError):
        AbstractAPI()

    assert abstract_api.get_vacancies("test") == [{"test": "data"}]


def test_hh_api():
    """Тестирование успешного запроса к HH API"""
    with patch("src.apies.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"items": [{"name": "Python Dev"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        hh_api = HeadHunterAPI()
        result = hh_api.get_vacancies("Python")
        assert len(result) == 1
        assert result[0]["name"] == "Python Dev"
        mock_get.assert_called_once_with(
            "https://api.hh.ru/vacancies", params={"text": "Python", "area": 113, "per_page": 100}
        )


def test_hh_api_invalid_json(hh_api):
    """Тест обработки невалидного JSON"""
    with patch("src.apies.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        result = hh_api.get_vacancies("Python")
        assert result == []


def test_hh_api_connection_error(hh_api):
    """Тест ошибки соединения"""
    with patch("src.apies.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("No connection")
        result = hh_api.get_vacancies("Python")

        assert result == []
