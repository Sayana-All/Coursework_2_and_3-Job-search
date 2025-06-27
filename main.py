from src.apies import HeadHunterAPI
from src.reports import CSVSaver, JSONSaver
from src.vacancy import Vacancy


def user_interaction():
    try:
        hh_api = HeadHunterAPI()

        print("🔍 Поиск вакансий на hh.ru")
        search_query = input("Введите поисковый запрос (например, 'Python'): ").title()
        top_n = int(input("Сколько вакансий вывести в топ? "))
        filter_words = input("Введите ключевые слова для фильтрации (через пробел): ").split()
        salary_range = input("Введите диапазон зарплат (например: 100000-150000 или 120000): ").strip()

        # Получение и обработка вакансий
        hh_vacancies = hh_api.get_vacancies(search_query)
        vacancies_list = Vacancy.cast_to_object_list(hh_vacancies)

        # Фильтрация по ключевым словам
        filtered_vacancies = [
            v
            for v in vacancies_list
            if (not filter_words or any(word.lower() in v.description.lower() for word in filter_words))
            and v.matches_salary_range(salary_range)
        ]

        # Сортировка по зарплате
        sorted_vacancies = sorted(filtered_vacancies, reverse=True)
        top_vacancies = sorted_vacancies[:top_n]

        print(f"\nНайдено {len(top_vacancies)} вакансий:")
        for i, vacancy in enumerate(top_vacancies, 1):
            salary = vacancy.salary
            salary_str = f"{salary.get('from', '?')}-{salary.get('to', '?')} {salary.get('currency', '')}"
            print(f"{i}. {vacancy.title}\nЗарплата: {salary_str}\nСсылка: {vacancy.url}\n")

        # Запрос на сохранение
        if top_vacancies and input("\nСохранить результаты? (да/нет): ").lower() == "да":
            save_format = input("В каком формате сохранить? (json/csv): ").lower()
            if save_format == "json":
                saver = JSONSaver()
            elif save_format == "csv":
                saver = CSVSaver()
            else:
                print("Неверный формат. Используется JSON по умолчанию.")
                saver = JSONSaver()

            for vacancy in top_vacancies:
                saver.add_vacancy(vacancy)
            print(f"\nДанные сохранены в файл: {saver.filename}")

        else:
            print("Результаты не сохранены.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    user_interaction()
