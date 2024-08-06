import os
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение email и пароля из переменных окружения
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)


# Функция для авторизации
def login():
    try:
        print("Начинаем процесс авторизации...")
        driver.get("https://www.leadertask.ru/web/login")

        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys(EMAIL)

        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить с Email')]"))
        )
        continue_button.click()

        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_input.send_keys(PASSWORD)

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit'][contains(., 'Войти')]"))
        )
        login_button.click()

        WebDriverWait(driver, 20).until(
            EC.url_to_be("https://www.leadertask.ru/web/tasks/today")
        )
        print("Успешно вошли в систему!")
        time.sleep(5)  # Дополнительное ожидание после входа
    except Exception as e:
        print(f"Произошла ошибка при авторизации: {str(e)}")
        driver.quit()
        exit(1)


def get_users():
    users = []
    try:
        print("Получаем список пользователей...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/web/tasks/delegate-by-me/')]"))
        )
        user_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/web/tasks/delegate-by-me/')]")
        for user in user_elements:
            try:
                name = user.find_element(By.XPATH, ".//p[contains(@class, 'text-[#1B1B1CCC]')]").text
                link = user.get_attribute('href')
                users.append({'name': name, 'link': link})
                print(f"Найден пользователь: {name} ({link})")
            except StaleElementReferenceException:
                print("Элемент устарел, пропускаем")
        print(f"Всего найдено пользователей: {len(users)}")
    except Exception as e:
        print(f"Ошибка при получении списка пользователей: {str(e)}")
    return users


# Функция для получения задач пользователя
def get_user_tasks(user_link):
    tasks = []
    try:
        print(f"Получаем задачи пользователя: {user_link}")
        driver.get(user_link)
        time.sleep(10)  # Увеличиваем время ожидания до 10 секунд

        # Проверяем наличие задач
        task_elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'wrapperChild')]"))
        )

        if not task_elements:
            print("Задачи не найдены. Возможно, у пользователя нет задач.")
            return tasks

        for task in task_elements:
            try:
                task_id = task.get_attribute('id')
                task_name = task.find_element(By.XPATH, ".//div[contains(@class, 'taskName')]").text
                task_link = f"{user_link}/{task_id}"
                tasks.append({'id': task_id, 'name': task_name, 'link': task_link})
            except (NoSuchElementException, StaleElementReferenceException):
                print(f"Не удалось получить информацию о задаче")

        print(f"Найдено задач: {len(tasks)}")
    except TimeoutException:
        print("Время ожидания истекло при попытке найти задачи")
    except Exception as e:
        print(f"Ошибка при получении задач пользователя: {str(e)}")
    return tasks


# Функция для получения подробной информации о задаче
def get_task_details(task_link):
    try:
        print(f"Получаем детали задачи: {task_link}")
        driver.get(task_link)
        time.sleep(10)  # Увеличиваем время ожидания до 10 секунд

        title = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'focus:ring-2') and contains(@class, 'text-[18px]')]"))
        ).text

        checklists = driver.find_elements(By.XPATH,
                                          "//div[@contenteditable='true' and contains(@class, 'text-[13px]')]")
        checklist_items = [item.text for item in checklists if item.text]

        description = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "taskPropsCommentEditor"))
        ).text

        return {'title': title, 'checklist': checklist_items, 'description': description}
    except TimeoutException:
        print("Время ожидания истекло при попытке получить детали задачи")
    except Exception as e:
        print(f"Ошибка при получении деталей задачи: {str(e)}")
    return {'title': 'Ошибка', 'checklist': [], 'description': 'Не удалось получить данные'}


# Основная функция
def main():
    try:
        login()
        users = get_users()

        for user in users:
            print(f"\nОбрабатываем пользователя: {user['name']} ({user['link']})")
            tasks = get_user_tasks(user['link'])

            if not tasks:
                print(f"У пользователя {user['name']} нет задач или не удалось их получить.")
                continue

            for task in tasks:
                print(f"\n  Задача: {task['name']}")
                details = get_task_details(task['link'])
                print(f"    Заголовок: {details['title']}")
                print(f"    Чек-лист: {', '.join(details['checklist'])}")
                print(f"    Описание: {details['description']}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {str(e)}")
    finally:
        print("Завершаем работу...")
        driver.quit()


if __name__ == "__main__":
    main()