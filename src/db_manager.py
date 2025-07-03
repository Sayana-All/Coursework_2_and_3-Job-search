import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config.config import config
from src.vacancy import Vacancy


class DBManager:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.conn = None

    def __enter__(self):
        """Контекстный менеджер для подключения к БД"""
        params = config()
        params.update({"database": self.db_name})

        try:
            self.conn = psycopg2.connect(**params)
            return self
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Метод для завершения соединения с БД"""
        if self.conn:
            self.conn.close()

    def create_database(self):
        """Метод для создания БД или подключения к существующей"""
        conn = None
        try:
            params = config()
            params.pop("database", None)

            conn = psycopg2.connect(**params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = {}").format(sql.Literal(self.db_name)))
            exists = cursor.fetchone()

            if exists:
                print(f"База данных {self.db_name} уже существует")
            else:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name)))
                print(f"База данных {self.db_name} успешно создана")

        except Exception as e:
            print(f"Ошибка при работе с базой данных: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_tables(self):
        """Метод для создания таблиц в БД"""
        commands = (
            """
            CREATE TABLE IF NOT EXISTS employers (
                employer_id SERIAL PRIMARY KEY,
                employer_name VARCHAR(255) NOT NULL,
                employer_url VARCHAR(255),
                hh_id INTEGER UNIQUE NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS vacancies (
                vacancy_id SERIAL PRIMARY KEY,
                employer_id INTEGER REFERENCES employers(employer_id),
                title VARCHAR(255) NOT NULL,
                salary_from INTEGER,
                salary_to INTEGER,
                currency VARCHAR(10),
                url VARCHAR(255),
                description TEXT,
                hh_id INTEGER UNIQUE NOT NULL
            )
            """,
        )

        try:
            with self.conn.cursor() as cursor:
                for command in commands:
                    cursor.execute(command)
            self.conn.commit()
            print("Таблицы успешно созданы/проверены")
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка при создании таблиц: {e}")
            raise

    def insert_employer(self, employer_data):
        """Метод для добавления работодателя в БД"""
        try:
            if not employer_data.get("id"):
                print("Ошибка: отсутствует ID работодателя")
                return None

            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO employers (employer_name, employer_url, hh_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (hh_id) DO UPDATE
                    SET employer_name = EXCLUDED.employer_name,
                        employer_url = EXCLUDED.employer_url
                    RETURNING employer_id
                    """,
                    (
                        employer_data.get("name", "Не указано"),
                        employer_data.get("alternate_url", ""),
                        employer_data["id"],
                    ),
                )
                result = cursor.fetchone()
                self.conn.commit()
                return result[0] if result else None

        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка при добавлении работодателя: {e}")
            return None

    def insert_vacancy(self, vacancy_data):
        """Метод для добавления вакансии в БД"""
        try:
            if not vacancy_data.get("id"):
                print(f"Пропущена вакансия без ID: {vacancy_data}")
                return

            employer = vacancy_data.get("employer", {}) or {}
            salary = vacancy_data.get("salary", {}) or {}
            snippet = vacancy_data.get("snippet", {}) or {}

            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO vacancies (
                        employer_id, title, salary_from, salary_to, 
                        currency, url, description, hh_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hh_id) DO NOTHING
                    """,
                    (
                        employer.get("id"),
                        vacancy_data.get("name", "Без названия"),
                        salary.get("from"),
                        salary.get("to"),
                        salary.get("currency"),
                        vacancy_data.get("alternate_url"),
                        snippet.get("requirement"),
                        vacancy_data["id"],
                    ),
                )
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка при добавлении вакансии {vacancy_data.get('name')}: {str(e)}")

    def get_companies_and_vacancies_count(self):
        """Метод получения списка всех компаний и количество вакансий у каждой компании"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.employer_name, COUNT(v.vacancy_id) as vacancies_count
                FROM employers e
                LEFT JOIN vacancies v ON e.employer_id = v.employer_id
                GROUP BY e.employer_name
                ORDER BY vacancies_count DESC
                """
            )
            return cursor.fetchall()

    def get_all_vacancies(self):
        """Метод получения списка всех вакансий с указанием названия компании,
        названия вакансии, зарплаты, ссылки на вакансию и её описанием"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    e.employer_name, 
                    v.title, 
                    v.salary_from, 
                    v.salary_to, 
                    v.currency, 
                    v.url,
                    v.description,
                    v.vacancy_id
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                ORDER BY e.employer_name, v.title
            """
            )
            return cursor.fetchall()

    def get_avg_salary(self):
        """Метод для получения средней зарплаты по вакансиям"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT AVG((salary_from + salary_to) / 2) as avg_salary
                FROM vacancies
                WHERE salary_from IS NOT NULL AND salary_to IS NOT NULL
                """
            )
            return cursor.fetchone()[0]

    def get_vacancies_with_higher_salary(self):
        """Метод для получения списка всех вакансий, где зарплата выше средней"""
        avg_salary = self.get_avg_salary()
        if not avg_salary:
            return []

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    e.employer_name, 
                    v.title, 
                    v.salary_from, 
                    v.salary_to, 
                    v.currency, 
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE (v.salary_from + v.salary_to) / 2 > %s
                """,
                (avg_salary,),
            )
            return cursor.fetchall()

    def get_vacancies_with_keyword(self, keyword):
        """Метод получения списка всех вакансий, в названии которых содержатся ключевые слова"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    e.employer_name, 
                    v.title, 
                    v.salary_from, 
                    v.salary_to, 
                    v.currency, 
                    v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE v.title ILIKE %s
                """,
                (f"%{keyword}%",),
            )
            return cursor.fetchall()

    def get_all_vacancies_as_objects(self) -> list[Vacancy]:
        """Метод получения всех вакансий из БД, возвращает список объектов Vacancy"""
        vacancies_data = self.get_all_vacancies()
        vacancies = []

        for vac in vacancies_data:
            try:
                (employer_name, title, salary_from, salary_to, currency, url, description, vacancy_id) = vac

                vacancies.append(
                    Vacancy(
                        title=title,
                        url=url,
                        salary={
                            "from": salary_from if salary_from else 0,
                            "to": salary_to if salary_to else 0,
                            "currency": currency if currency else "не указана",
                        },
                        description=description if description else "Нет описания",
                    )
                )
            except Exception as e:
                print(f"Ошибка создания объекта Vacancy из данных: {vac}")
                print(f"Подробности ошибки: {e}")
                continue

        return vacancies

    def get_vacancies_with_keyword_as_objects(self, keyword: str) -> list[Vacancy]:
        """Метод поиска вакансий по ключевому слову с возвратом объектов Vacancy"""
        vacancies_data = self.get_vacancies_with_keyword(keyword)
        return [
            Vacancy(
                title=title,
                url=url,
                salary={"from": salary_from, "to": salary_to, "currency": currency},
                description="",
            )
            for _, title, _, salary_from, salary_to, currency, url, _ in vacancies_data
        ]
