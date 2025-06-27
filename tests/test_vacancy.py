import pytest

from src.vacancy import Vacancy


def test_slots_restriction():
    """Тестирование ограничений __slots__"""
    vacancy = Vacancy("A", "#", None, "")

    assert hasattr(vacancy, "__slots__")

    with pytest.raises(AttributeError):
        vacancy.new_attr = "test"


def test_vacancy_creation(sample_vacancy):
    """Тестирование на создание вакансии с зарплатой"""
    assert sample_vacancy.title == "Python Developer"
    assert sample_vacancy.salary["from"] == 100000
    assert sample_vacancy.salary["to"] == 150000
    assert sample_vacancy.avg_salary == 125000
    assert sample_vacancy.description == "Требования к кандидату"


def test_vacancy_no_salary(vacancy_no_salary):
    """Тестирование на добавление вакансии без зарплаты"""
    assert vacancy_no_salary.salary == {"from": 0, "to": 0, "currency": "не указана"}
    assert vacancy_no_salary.avg_salary == 0


def test_vacancy_to_dict(test_vacancy):
    """Тестирование преобразования вакансии в словарь"""
    vacancy_dict = test_vacancy.to_dict()
    assert vacancy_dict == {
        "title": "Python Developer",
        "url": "https://hh.ru/vacancy/1",
        "salary": {"from": 100000, "to": 150000, "currency": "RUB"},
        "description": "Experience required",
    }


def test_comparison(sample_vacancy, vacancy_no_salary):
    """Тест на сравнения зарплат вакансий"""
    assert sample_vacancy > vacancy_no_salary
    assert vacancy_no_salary < sample_vacancy


def test_matches_salary_range(sample_vacancy):
    """Тест проверки диапазона зарплат"""
    # Полное совпадение
    assert sample_vacancy.matches_salary_range("100000-150000") is True
    # Частичное совпадение
    assert sample_vacancy.matches_salary_range("120000-140000") is True
    # Нижняя граница
    assert sample_vacancy.matches_salary_range("90000-110000") is True
    # Верхняя граница
    assert sample_vacancy.matches_salary_range("140000-160000") is True
    # Нет совпадения
    assert sample_vacancy.matches_salary_range("160000-200000") is False
    # Одно значение
    assert sample_vacancy.matches_salary_range("120000") is True
    # Без диапазона
    assert sample_vacancy.matches_salary_range("") is True


def test_invalid_salary_range(sample_vacancy):
    """Тест с некорректным диапазоном зарплат"""
    assert sample_vacancy.matches_salary_range("abc-def") is False
    assert sample_vacancy.matches_salary_range("100000-") is False
    assert sample_vacancy.matches_salary_range("-150000") is False


def test_cast_to_object_list():
    """Проверка преобразования JSON в объекты"""
    test_data = [
        {
            "name": "Java Dev",
            "alternate_url": "https://hh.ru/vacancy/3",
            "salary": {"from": 90000},
            "snippet": {"requirement": "Нужен Java"},
        }
    ]
    vacancies = Vacancy.cast_to_object_list(test_data)
    assert len(vacancies) == 1
    assert vacancies[0].title == "Java Dev"


def test_str_representation(sample_vacancy):
    """Тест строкового представления класса Vacancy"""
    result = str(sample_vacancy)
    assert "Вакансия: Python Developer" in result
    assert "Зарплата: 100000-150000 RUB" in result
    assert "Ссылка: https://hh.ru/vacancy/123" in result
    assert "Описание: Требования к кандидату" in result
