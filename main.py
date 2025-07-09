import os
from typing import Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config.config import config
from src.apies import HeadHunterAPI
from src.db_manager import DBManager
from src.reports import CSVSaver, JSONSaver


def initialize_database(db_name: str = "vacancies") -> Optional[DBManager]:
    """Функция автоматического создания БД и таблиц (если их нет)"""
    try:
        temp_params = config()
        temp_params.pop("database", None)

        admin_conn = psycopg2.connect(**temp_params)
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        admin_conn.autocommit = True
        cursor = admin_conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"База данных {db_name} создана")
        else:
            print(f"База данных {db_name} уже существует")
        admin_conn.close()

        manager = DBManager(db_name)

        if not manager.is_connected():
            raise ConnectionError("Не удалось подключиться к БД")

        manager.create_tables()
        print("✅ Таблицы успешно созданы/проверены")
        return manager

    except psycopg2.OperationalError as e:
        print(f"❌ Ошибка подключения: {e}")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
    return None


def user_interaction(manager: DBManager):
    """Основная функция взаимодействия с пользователем"""
    hh_api = HeadHunterAPI()

    def check_connection():
        if not manager.is_connected():
            print("⚠ Соединение потеряно, пробуем переподключиться...")
            if not manager._connect():
                print("❌ Не удалось восстановить соединение!")
                return False
        return True

    while True:
        print("\n=== Главное меню ===")
        print("1. Загрузить вакансии выбранных компаний")
        print("2. Показать список компаний и количество вакансий")
        print("3. Показать все вакансии")
        print("4. Показать среднюю зарплату")
        print("5. Показать вакансии с зарплатой выше средней")
        print("6. Поиск вакансий по ключевому слову")
        print("7. Экспорт вакансий в JSON")
        print("8. Экспорт вакансий в CSV")
        print("0. Выход")

        choice = input("\nВыберите действие: ")

        try:
            if choice == "1":
                if not check_connection():
                    continue
                load_vacancies(hh_api, manager)
            elif choice == "2":
                if not check_connection():
                    continue
                show_companies(manager)
            elif choice == "3":
                if not check_connection():
                    continue
                show_all_vacancies(manager)
            elif choice == "4":
                if not check_connection():
                    continue
                show_avg_salary(manager)
            elif choice == "5":
                if not check_connection():
                    continue
                show_high_salary_vacancies(manager)
            elif choice == "6":
                if not check_connection():
                    continue
                search_vacancies(manager)
            elif choice == "7":
                if not check_connection():
                    continue
                filename = (
                    input("Введите имя файла для экспорта (по умолчанию vacancies_export.json): ")
                    or "vacancies_export.json"
                )
                export_vacancies_to_json(manager, filename)
            elif choice == "8":
                if not check_connection():
                    continue
                filename = (
                    input("Введите имя файла для экспорта (по умолчанию vacancies_export.csv): ")
                    or "vacancies_export.csv"
                )
                export_vacancies_to_csv(manager, filename)
            elif choice == "0":
                print("Работа программы завершена.")
                break
            else:
                print("Неверный ввод, попробуйте еще раз.")

        except Exception as e:
            print(f"⚠ Ошибка: {e}")


def load_vacancies(hh_api: HeadHunterAPI, manager: DBManager):
    """Загрузка вакансий выбранных компаний"""
    print("\nДоступные компании для загрузки:")
    employers = hh_api.get_employers()

    for i, employer in enumerate(employers, 1):
        print(f"{i}. {employer['name']} (ID: {employer['id']})")

    selected = input("\nВведите номера компаний через пробел (или 'all' для всех): ")

    if selected.lower() == "all":
        selected_employers = employers
    else:
        try:
            indexes = [int(i.strip()) - 1 for i in selected.split()]
            selected_employers = [employers[i] for i in indexes if 0 <= i < len(employers)]
        except (ValueError, IndexError):
            print("Ошибка ввода, используйте номера из списка")
            return

    print("\nНачинаю загрузку вакансий...")

    for employer in selected_employers:
        print(f"\n=== Обрабатываем {employer['name']} ===")

        print("Добавляем работодателя в БД...")
        employer_id = manager.insert_employer(employer)

        if not employer_id:
            print(f"Критическая ошибка: не удалось добавить работодателя {employer['name']}")
            continue

        print(f"Работодатель добавлен с ID: {employer_id}")

        print("Загружаем вакансии с hh.ru...")
        vacancies = hh_api.get_employer_vacancies(employer["id"])

        if not vacancies:
            print(f"Для {employer['name']} не найдено вакансий")
            continue

        print(f"Найдено {len(vacancies)} вакансий")

        success_count = 0
        for vacancy in vacancies:
            try:
                vacancy["employer"] = {"id": employer_id}
                manager.insert_vacancy(vacancy)
                success_count += 1
            except Exception as e:
                print(f"Ошибка при добавлении вакансии: {e}")
                continue

        print(f"Успешно добавлено {success_count}/{len(vacancies)} вакансий")

    print("\nЗагрузка завершена!")


def show_companies(manager: DBManager):
    """Показать компании и количество вакансий"""
    print("\nКомпании и количество вакансий:")
    companies = manager.get_companies_and_vacancies_count()
    for company, count in companies:
        print(f"{company}: {count} вакансий")


def show_all_vacancies(manager: DBManager):
    """Функция для просмотра всех вакансий от выбранных компаний"""
    if not manager.is_connected():
        print("⚠ Нет соединения с БД!")
        return

    print("\nВсе вакансии, сгруппированные по компаниям:\n")

    try:
        vacancies = manager.get_all_vacancies()
        if not vacancies:
            print("В базе данных нет вакансий")
            return

        companies = {}
        for vacancy in vacancies:
            company = vacancy[0]
            if company not in companies:
                companies[company] = []

            (_, title, salary_from, salary_to, currency, url, description) = vacancy
            companies[company].append((title, salary_from, salary_to, currency, url, description))

        for i, (company, company_vacancies) in enumerate(companies.items()):
            if i > 0:
                print("\n" + "=" * 50 + "\n")

            print(f"=== {company.upper()} ===")
            print(f"Всего вакансий: {len(company_vacancies)}\n")

            for j, (title, salary_from, salary_to, currency, url, _) in enumerate(company_vacancies, 1):
                salary = format_salary(salary_from, salary_to, currency)
                print(f"{j}. {title}")
                print(f"   Зарплата: {salary}")
                print(f"   Ссылка: {url}")

    except Exception as e:
        print(f"⚠ Ошибка при получении вакансий: {e}")


def show_avg_salary(manager: DBManager):
    """Показать среднюю зарплату"""
    avg_salary = manager.get_avg_salary()
    if avg_salary:
        print(f"\nСредняя зарплата по всем вакансиям: {avg_salary:.2f} RUB")
    else:
        print("\nНе удалось рассчитать среднюю зарплату")


def show_high_salary_vacancies(manager: DBManager):
    """Показать вакансии с зарплатой выше средней"""
    print("\nВакансии с зарплатой выше средней:")
    vacancies = manager.get_vacancies_with_higher_salary()
    for company, title, salary_from, salary_to, currency, url in vacancies:
        salary = format_salary(salary_from, salary_to, currency)
        print(f"{company} - {title}")
        print(f"Зарплата: {salary} (выше средней)")
        print(f"Ссылка: {url}\n")


def search_vacancies(manager: DBManager):
    """Поиск вакансий по ключевому слову"""
    keyword = input("\nВведите ключевое слово для поиска: ")
    vacancies = manager.get_vacancies_with_keyword(keyword)

    if vacancies:
        print(f"\nНайдено {len(vacancies)} вакансий по запросу '{keyword}':")
        for company, title, salary_from, salary_to, currency, url in vacancies:
            salary = format_salary(salary_from, salary_to, currency)
            print(f"{company} - {title}")
            print(f"Зарплата: {salary}")
            print(f"Ссылка: {url}\n")
    else:
        print(f"\nВакансий по запросу '{keyword}' не найдено")


def format_salary(salary_from, salary_to, currency) -> str:
    """Форматирование зарплаты для вывода"""
    if salary_from and salary_to:
        return f"{salary_from} - {salary_to} {currency}"
    elif salary_from:
        return f"от {salary_from} {currency}"
    elif salary_to:
        return f"до {salary_to} {currency}"
    return "не указана"


def export_vacancies_to_json(manager: DBManager, filename: str = "vacancies_export.json"):
    """Экспорт вакансий из БД в JSON-файл"""
    try:
        if not manager.is_connected():
            print("⚠ Нет соединения с БД!")
            return

        vacancies = manager.get_all_vacancies_as_objects()
        if not vacancies:
            print("Нет вакансий для экспорта. Сначала загрузите вакансии.")
            return

        os.makedirs("data", exist_ok=True)

        saver = JSONSaver(filename)
        for vacancy in vacancies:
            saver.add_vacancy(vacancy)

        print(f"✅ Успешно экспортировано {len(vacancies)} вакансий в {filename}")

    except Exception as e:
        print(f"❌ Ошибка при экспорте в JSON: {e}")


def export_vacancies_to_csv(manager: DBManager, filename: str = "vacancies_export.csv"):
    """Экспорт вакансий из БД в CSV-файл"""
    try:
        if not manager.is_connected():
            print("⚠ Нет соединения с БД!")
            return

        vacancies = manager.get_all_vacancies_as_objects()
        if not vacancies:
            print("Нет вакансий для экспорта. Сначала загрузите вакансии.")
            return

        os.makedirs("data", exist_ok=True)

        saver = CSVSaver(filename)
        for vacancy in vacancies:
            saver.add_vacancy(vacancy)

        print(f"✅ Успешно экспортировано {len(vacancies)} вакансий в {filename}")

    except Exception as e:
        print(f"❌ Ошибка при экспорте в CSV: {e}")


if __name__ == "__main__":
    manager = initialize_database()
    if manager:
        try:
            user_interaction(manager)
        except KeyboardInterrupt:
            print("\nПрограмма прервана пользователем")
        except Exception as e:
            print(f"\n⚠ Критическая ошибка: {e}")
        finally:
            print("Завершение работы...")
