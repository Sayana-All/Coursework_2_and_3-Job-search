class Vacancy:
    """Класс для представления вакансии"""

    def __init__(self, title: str, url: str, salary: dict | None, description: str):
        """Конструктор для создания объектов класса Вакансия"""
        self.title = title
        self.url = url
        self.salary = self._validate_salary(salary)
        self.description = description

    def _validate_salary(self, salary: dict | None) -> dict:
        """Метод для валидации данных о зарплате"""
        if not salary:
            return {"from": 0, "to": 0, "currency": "не указана"}
        return {
            "from": salary.get("from", 0) or 0,
            "to": salary.get("to", 0) or 0,
            "currency": salary.get("currency", "не указана")
        }

    @property
    def avg_salary(self) -> float:
        """Геттер для расчета средней зарплаты (для сравнения)"""
        return (self.salary["from"] + self.salary["to"]) / 2

    def __lt__(self, other) -> bool:
        """Метод для сравнения вакансий по зарплате (`<`)."""
        return self.avg_salary < other.avg_salary

    def __gt__(self, other) -> bool:
        """Метод для сравнения вакансий по зарплате (`>`)."""
        return self.avg_salary > other.avg_salary

    def __str__(self) -> str:
        salary_info = f"Зарплата: {self.salary['from']}-{self.salary['to']} {self.salary['currency']}"
        return f"{self.title}\n{salary_info}\nСсылка: {self.url}\nОписание: {self.description[:100]}...\n"

    @classmethod
    def cast_to_object_list(cls, vacancies_data: list[dict]) -> list["Vacancy"]:
        """Класс-метод для преобразования данных из API в список объектов Vacancy"""
        vacancies = []
        for item in vacancies_data:
            vacancy = cls(
                title=item.get("name", "Без названия"),
                url=item.get("alternate_url", "#"),
                salary=item.get("salary"),
                description=item.get("snippet", {}).get("requirement", "Нет описания")
            )
            vacancies.append(vacancy)
        return vacancies
