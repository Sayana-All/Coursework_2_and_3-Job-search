import pytest

from src.apies import HeadHunterAPI
from src.reports import CSVSaver, JSONSaver
from src.vacancy import Vacancy


@pytest.fixture
def hh_api():
    return HeadHunterAPI()


@pytest.fixture
def sample_vacancy():
    return Vacancy(
        title="Python Developer",
        url="https://hh.ru/vacancy/123",
        salary={"from": 100000, "to": 150000, "currency": "RUB"},
        description="Требования к кандидату",
    )


@pytest.fixture
def vacancy_no_salary():
    return Vacancy(title="DevOps", url="https://hh.ru/vacancy/2", salary=None, description="Без зарплаты")


@pytest.fixture
def test_vacancy():
    return Vacancy(
        title="Python Developer",
        url="https://hh.ru/vacancy/1",
        salary={"from": 100000, "to": 150000, "currency": "RUB"},
        description="Experience required",
    )


@pytest.fixture
def json_saver(tmp_path):
    """Фикстура с временным путём для тестов"""
    test_file = tmp_path / "vacancies.json"
    return JSONSaver(filename=str(test_file))


@pytest.fixture
def csv_saver(tmp_path):
    """Фикстура с временным путём для тестов"""
    test_file = tmp_path / "test_vacancies.csv"
    return CSVSaver(filename=str(test_file))
