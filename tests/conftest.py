import pytest

from src.apies import AbstractAPI, HeadHunterAPI
from src.vacancy import Vacancy


@pytest.fixture
def abstract_api():
    class TestAPI(AbstractAPI):
        def get_vacancies(self, query):
            return [{"test": "data"}]

    return TestAPI()


@pytest.fixture
def hh_api():
    return HeadHunterAPI()


@pytest.fixture
def sample_vacancy():
    return Vacancy(
        title="Python Developer",
        url="https://hh.ru/vacancy/123",
        salary={"from": 100000, "to": 150000, "currency": "RUB"},
        description="Описание вакансии",
    )


@pytest.fixture
def vacancy_no_salary():
    return Vacancy(title="DevOps", url="https://hh.ru/vacancy/2", salary=None, description="Без зарплаты")


@pytest.fixture
def test_vacancy():
    return Vacancy(
        title="Test Developer",
        url="https://test.ru",
        salary={"from": 100000, "to": 150000, "currency": "RUB"},
        description="Test description",
    )
