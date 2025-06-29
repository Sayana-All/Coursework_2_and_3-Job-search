import csv
import os


def test_json_saver_private_filename(json_saver):
    """Проверка наличия приватного атрибута __filename в JSONSaver"""
    assert hasattr(json_saver, "_JSONSaver__filename")


def test_json_add_and_get_vacancy(json_saver, test_vacancy):
    """Тест добавления и получения вакансии в JSON-файле"""
    json_saver.add_vacancy(test_vacancy)
    assert os.path.exists(json_saver._JSONSaver__filename)

    vacancies = json_saver.get_vacancies()
    assert len(vacancies) == 1
    assert vacancies[0]["title"] == "Python Developer"
    assert vacancies[0]["url"] == "https://hh.ru/vacancy/1"


def test_json_duplicate_vacancy(json_saver, test_vacancy):
    """Проверка защиты от дубликатов в JSON-файле"""
    json_saver.add_vacancy(test_vacancy)
    json_saver.add_vacancy(test_vacancy)

    vacancies = json_saver.get_vacancies()
    assert len(vacancies) == 1


def test_json_delete_vacancy(json_saver, test_vacancy):
    """Тест удаления вакансии из JSON-файла"""
    json_saver.add_vacancy(test_vacancy)
    json_saver.delete_vacancy(test_vacancy)

    vacancies = json_saver.get_vacancies()
    assert len(vacancies) == 0


def test_json_clear_file(json_saver, test_vacancy):
    """Тест очистки JSON-файла"""
    json_saver.add_vacancy(test_vacancy)
    json_saver.clear_file()

    assert not os.path.exists(json_saver._JSONSaver__filename)


def test_csv_saver_init(csv_saver, tmp_path):
    """Тест инициализации CSVSaver"""
    assert hasattr(csv_saver, "_CSVSaver__filename")
    assert str(csv_saver._CSVSaver__filename) == str(tmp_path / "test_vacancies.csv")


def test_csv_add_vacancy(csv_saver, test_vacancy):
    """Тестирование на добавление вакансии в CSV-файл"""
    csv_saver.add_vacancy(test_vacancy)

    with open(csv_saver._CSVSaver__filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    assert len(data) == 1
    assert data[0]["title"] == "Python Developer"


def test_csv_add_duplicate_vacancy(csv_saver, test_vacancy):
    """Проверка на добавление дубликата вакансии в CSV-файл"""
    csv_saver.add_vacancy(test_vacancy)
    csv_saver.add_vacancy(test_vacancy)  # Пытаемся добавить дубликат

    with open(csv_saver._CSVSaver__filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    assert len(data) == 1


def test_csv_get_vacancies(csv_saver, test_vacancy):
    """Тест получения вакансий из CSV-файла"""
    csv_saver.add_vacancy(test_vacancy)
    vacancies = csv_saver.get_vacancies()

    assert len(vacancies) == 1
    assert vacancies[0]["url"] == "https://hh.ru/vacancy/1"


def test_csv_delete_vacancy(csv_saver, test_vacancy):
    """Тест удаления вакансии из CSV-файла"""
    csv_saver.add_vacancy(test_vacancy)
    csv_saver.delete_vacancy(test_vacancy)

    vacancies = csv_saver.get_vacancies()
    assert len(vacancies) == 0


def test_csv_clear_file(csv_saver, test_vacancy):
    """Тест очистки CSV-файла"""
    csv_saver.add_vacancy(test_vacancy)
    csv_saver.clear_file()

    assert not os.path.exists(csv_saver._CSVSaver__filename)
