class Vacancy:
    """Класс для представления вакансии"""

    __slots__ = ("_title", "_url", "_salary", "_description")  # Для экономии памяти

    def __init__(self, title: str, url: str, salary: dict | None, description: str):
        """Конструктор с валидацией всех атрибутов"""
        self._title = self.__validate_title(title)
        self._url = self.__validate_url(url)
        self._salary = self.__validate_salary(salary)
        self._description = self.__validate_description(description)

    def __validate_title(self, title: str) -> str:
        """Приватный метод валидации названия вакансии"""
        if not title or not isinstance(title, str):
            return "Без названия"
        return title.strip()

    def __validate_url(self, url: str) -> str:
        """Приватный метод валидации URL"""
        if not url or not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return "#"
        return url

    def __validate_salary(self, salary: dict | None) -> dict:
        """Приватный метод валидации зарплаты"""
        if not salary or not isinstance(salary, dict):
            return {"from": 0, "to": 0, "currency": "не указана"}

        return {
            "from": int(salary.get("from", 0)) if salary.get("from") else 0,
            "to": int(salary.get("to", 0)) if salary.get("to") else 0,
            "currency": str(salary.get("currency", "не указана")),
        }

    def __validate_description(self, description: str) -> str:
        """Приватный метод валидации описания"""
        if not description or not isinstance(description, str):
            return "Нет описания"
        return description.strip()

    @property
    def title(self) -> str:
        """Геттер для получения атрибута названия вакансии"""
        return self._title

    @property
    def url(self) -> str:
        """Геттер для получения атрибута ссылки на вакансию"""
        return self._url

    @property
    def salary(self) -> dict:
        """Геттер для получения атрибута с зарплатой вакансии"""
        return self._salary

    @property
    def description(self) -> str:
        """Геттер для получения атрибута описания вакансии"""
        return self._description

    def to_dict(self):
        """Метод для преобразования в словарь"""
        return {"title": self._title, "url": self._url, "salary": self._salary, "description": self._description}

    def __lt__(self, other: "Vacancy") -> bool:
        if not isinstance(other, Vacancy):
            raise TypeError("Можно сравнивать только вакансии")
        return self.avg_salary < other.avg_salary

    def __gt__(self, other: "Vacancy") -> bool:
        if not isinstance(other, Vacancy):
            raise TypeError("Можно сравнивать только вакансии")
        return self.avg_salary > other.avg_salary

    def __eq__(self, other: "Vacancy") -> bool:
        if not isinstance(other, Vacancy):
            raise TypeError("Можно сравнивать только вакансии")
        return self.avg_salary == other.avg_salary

    @property
    def avg_salary(self) -> float:
        """Метод для расчета средней зарплаты для сравнения"""
        return (self._salary["from"] + self._salary["to"]) / 2

    def matches_salary_range(self, salary_range: str) -> bool:
        """Проверяет попадание в диапазон зарплат"""
        if not salary_range:
            return True

        try:
            if "-" in salary_range:
                min_s, max_s = map(int, salary_range.split("-"))
            else:
                min_s = max_s = int(salary_range)

            return (self._salary["from"] <= max_s) and (self._salary["to"] >= min_s)
        except (ValueError, AttributeError):
            return False

    @classmethod
    def cast_to_object_list(cls, vacancies_data: list[dict]) -> list["Vacancy"]:
        """Класс-метод для преобразования данных API в список объектов Vacancy"""
        return [
            cls(
                title=item.get("name"),
                url=item.get("alternate_url"),
                salary=item.get("salary"),
                description=item.get("snippet", {}).get("requirement"),
            )
            for item in vacancies_data
        ]

    @classmethod
    def from_db_row(cls, db_row: tuple):
        """Класс-метод для создания объекта Vacancy из строки БД"""
        return cls(
            title=db_row[1],  # предполагаем что title в колонке 1
            url=db_row[6],  # url в колонке 6
            salary={
                "from": db_row[3] if db_row[3] else 0,  # salary_from
                "to": db_row[4] if db_row[4] else 0,  # salary_to
                "currency": db_row[5] if db_row[5] else "не указана",
            },
            description=db_row[7] if len(db_row) > 7 else "",
        )

    def __str__(self) -> str:
        """Строковое представление вакансии"""
        salary = self._salary
        salary_str = (
            f"{salary['from']}-{salary['to']} {salary['currency']}" if salary["from"] or salary["to"] else "не указана"
        )
        return (
            f"Вакансия: {self._title}\n"
            f"Зарплата: {salary_str}\n"
            f"Ссылка: {self._url}\n"
            f"Описание: {self._description[:100]}...\n"
        )
