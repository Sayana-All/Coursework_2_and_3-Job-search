import os

import psycopg2

from config.config import config
from src.apies import HeadHunterAPI
from src.db_manager import DBManager
from src.reports import CSVSaver, JSONSaver


def user_interaction():
    """Основная функция взаимодействия с пользователем"""
    print("Добро пожаловать в систему сбора вакансий с hh.ru!")

    # Инициализация
    db_name = "vacancies"
    hh_api = HeadHunterAPI()

    # Подключение к БД
    try:
        db_params = config()
        db_params["database"] = db_name

        with psycopg2.connect(**db_params) as conn:
            db_manager = DBManager(db_name)
            db_manager.conn = conn

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

                if choice == "1":
                    load_vacancies(hh_api, db_manager)
                elif choice == "2":
                    show_companies(db_manager)
                elif choice == "3":
                    show_all_vacancies(db_manager)
                elif choice == "4":
                    show_avg_salary(db_manager)
                elif choice == "5":
                    show_high_salary_vacancies(db_manager)
                elif choice == "6":
                    search_vacancies(db_manager)
                elif choice == "7":
                    filename = (
                        input("Введите имя файла для экспорта (по умолчанию vacancies_export.json): ")
                        or "vacancies_export.json"
                    )
                    export_vacancies_to_json(db_manager, filename)
                elif choice == "8":
                    filename = (
                        input("Введите имя файла для экспорта (по умолчанию vacancies_export.csv): ")
                        or "vacancies_export.csv"
                    )
                    export_vacancies_to_csv(db_manager, filename)
                elif choice == "0":
                    print("Работа программы завершена.")
                    break
                else:
                    print("Неверный ввод, попробуйте еще раз.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if "conn" in locals():
            conn.close()


def load_vacancies(hh_api: HeadHunterAPI, db_manager: DBManager):
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

        # Шаг 1: Добавляем работодателя
        print("Добавляем работодателя в БД...")
        employer_id = db_manager.insert_employer(employer)

        if not employer_id:
            print(f"Критическая ошибка: не удалось добавить работодателя {employer['name']}")
            continue

        print(f"Работодатель добавлен с ID: {employer_id}")

        # Шаг 2: Получаем вакансии
        print("Загружаем вакансии с hh.ru...")
        vacancies = hh_api.get_employer_vacancies(employer["id"])

        if not vacancies:
            print(f"Для {employer['name']} не найдено вакансий")
            continue

        print(f"Найдено {len(vacancies)} вакансий")

        # Шаг 3: Добавляем вакансии
        success_count = 0
        for vacancy in vacancies:
            try:
                vacancy["employer"] = {"id": employer_id}
                db_manager.insert_vacancy(vacancy)
                success_count += 1
            except Exception as e:
                print(f"Ошибка при добавлении вакансии: {e}")
                continue

        print(f"Успешно добавлено {success_count}/{len(vacancies)} вакансий")

    print("\nЗагрузка завершена!")


def show_companies(db_manager: DBManager):
    """Показать компании и количество вакансий"""
    print("\nКомпании и количество вакансий:")
    companies = db_manager.get_companies_and_vacancies_count()
    for company, count in companies:
        print(f"{company}: {count} вакансий")


def show_all_vacancies(db_manager: DBManager):
    """Показать все вакансии от выбранных компаний"""
    print("\nВсе вакансии, сгруппированные по компаниям:\n")
    vacancies = db_manager.get_all_vacancies()

    if not vacancies:
        print("В базе данных нет вакансий")
        return

    companies = {}
    for vacancy in vacancies:
        company = vacancy[0]
        if company not in companies:
            companies[company] = []
        companies[company].append(vacancy[1:])

    first_company = True
    for company, company_vacancies in companies.items():
        if not first_company:
            print("\n" + "=" * 50 + "\n")
        first_company = False

        print(f"=== {company.upper()} ===")
        print(f"Всего вакансий: {len(company_vacancies)}\n")

        for i, (title, salary_from, salary_to, currency, url) in enumerate(company_vacancies, 1):
            salary = format_salary(salary_from, salary_to, currency)
            print(f"{i}. {title}")
            print(f"   Зарплата: {salary}")
            print(f"   Ссылка: {url}\n")

    print("\n" + "=" * 50)


def show_avg_salary(db_manager: DBManager):
    """Показать среднюю зарплату"""
    avg_salary = db_manager.get_avg_salary()
    if avg_salary:
        print(f"\nСредняя зарплата по всем вакансиям: {avg_salary:.2f} RUB")
    else:
        print("\nНе удалось рассчитать среднюю зарплату")


def show_high_salary_vacancies(db_manager: DBManager):
    """Показать вакансии с зарплатой выше средней"""
    print("\nВакансии с зарплатой выше средней:")
    vacancies = db_manager.get_vacancies_with_higher_salary()
    for company, title, salary_from, salary_to, currency, url in vacancies:
        salary = format_salary(salary_from, salary_to, currency)
        print(f"{company} - {title}")
        print(f"Зарплата: {salary} (выше средней)")
        print(f"Ссылка: {url}\n")


def search_vacancies(db_manager: DBManager):
    """Поиск вакансий по ключевому слову"""
    keyword = input("\nВведите ключевое слово для поиска: ")
    vacancies = db_manager.get_vacancies_with_keyword(keyword)

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


def export_vacancies_to_json(db_manager: DBManager, filename: str = "vacancies_export.json"):
    """Экспорт вакансий из БД в JSON-файл"""
    try:
        vacancies = db_manager.get_all_vacancies_as_objects()
        if not vacancies:
            print("Нет вакансий для экспорта. Сначала загрузите вакансии.")
            return

        os.makedirs("data", exist_ok=True)

        saver = JSONSaver(filename)
        for vacancy in vacancies:
            saver.add_vacancy(vacancy)

        print(f"Успешно экспортировано {len(vacancies)} вакансий в {filename}")
    except Exception as e:
        print(f"Ошибка при экспорте в JSON: {e}")


def export_vacancies_to_csv(db_manager: DBManager, filename: str = "vacancies_export.csv"):
    """Экспорт вакансий из БД в CSV-файл"""
    try:
        vacancies = db_manager.get_all_vacancies_as_objects()
        if not vacancies:
            print("Нет вакансий для экспорта. Сначала загрузите вакансии.")
            return

        os.makedirs("data", exist_ok=True)

        saver = CSVSaver(filename)
        for vacancy in vacancies:
            saver.add_vacancy(vacancy)

        print(f"Успешно экспортировано {len(vacancies)} вакансий в {filename}")
    except Exception as e:
        print(f"Ошибка при экспорте в CSV: {e}")


if __name__ == "__main__":
    user_interaction()
