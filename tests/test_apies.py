from unittest.mock import MagicMock, patch

from src.apies import HeadHunterAPI


def test_private_connection():
    """Проверка наличия приватного метода"""
    api = HeadHunterAPI()
    assert hasattr(api, "_HeadHunterAPI__connect_to_api")


@patch("requests.get")
def test_api_connection(mock_get):
    """Тест работы приватного метода"""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    api = HeadHunterAPI()
    # Вызываем приватный метод через name mangling
    result = api._HeadHunterAPI__connect_to_api("test_url", {})
    assert result == mock_response


def test_get_vacancies():
    """Тестирование на получение списка вакансий"""
    api = HeadHunterAPI()

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [{"id": "1"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api.get_vacancies("Python")
        assert len(result) == 1
        mock_get.assert_called_once_with(
            "https://api.hh.ru/vacancies", params={"area": 113, "per_page": 100, "text": "Python"}, timeout=10
        )
