import pytest
from unittest.mock import patch, mock_open, MagicMock
import json
import os
from src.reports import JSONSaver, CSVSaver


def test_json_saver_add(test_vacancy):
    """Тестирование добавления вакансии в JSON"""
    written_data = []

    def mock_write(data):
        written_data.append(data)
        return len(data)

    mock_file = mock_open()
    mock_file().write.side_effect = mock_write

    with (
        patch("builtins.open", mock_file),
        patch("os.path.exists", return_value=True),
        patch("json.load", return_value=[]),
    ):
        saver = JSONSaver("test.json")
        saver.add_vacancy(test_vacancy)

        full_content = "".join(written_data)
        parsed_content = json.loads(full_content)

        assert len(parsed_content) == 1
        assert parsed_content[0]["title"] == "Test Developer"
        assert parsed_content[0]["url"] == "https://test.ru"


def test_json_saver_delete(test_vacancy):
    """Тестирование удаления вакансии из JSON"""
    initial_data = [test_vacancy.__dict__]

    with (
        patch("builtins.open", mock_open(read_data=json.dumps(initial_data))),
        patch("os.path.exists", return_value=True),
        patch("json.load", return_value=initial_data),
    ):
        saver = JSONSaver("test.json")
        saver.delete_vacancy(test_vacancy)


def test_csv_saver_add(test_vacancy):
    """Тестирование добавления в CSV"""
    with patch("builtins.open", mock_open()) as mock_file, patch("csv.DictWriter") as mock_writer:
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance

        saver = CSVSaver("test.csv")
        saver.add_vacancy(test_vacancy)

        mock_writer_instance.writerow.assert_called_once_with(test_vacancy.__dict__)


def test_clear_file():
    """Тестирование удаления файла"""
    with patch("os.remove") as mock_remove, patch("os.path.exists", return_value=True):
        saver = JSONSaver("test.json")
        saver.clear_file()

        mock_remove.assert_called_once_with(os.path.join("data", "test.json"))
