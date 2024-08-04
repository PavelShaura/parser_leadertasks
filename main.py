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

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение email и пароля из переменных окружения
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Авторизация
driver.get("https://www.leadertask.ru/web/login")

# Шаг 1: Ввод email
email_input = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "email"))
)
email_input.send_keys(EMAIL)

# Нажатие кнопки "Продолжить с Email"
continue_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить с Email')]"))
)
continue_button.click()

# Шаг 2: Ввод пароля
password_input = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "password"))
)
password_input.send_keys(PASSWORD)

# Нажатие кнопки "Войти"
login_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit'][contains(., 'Войти')]"))
)
login_button.click()

# Ожидание перехода на страницу задач
WebDriverWait(driver, 10).until(
    EC.url_to_be("https://www.leadertask.ru/web/tasks/today")
)

# Теперь мы на странице задач
print("Успешно вошли в систему!")

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "vtlist-inner"))
)

# Даем время на полную загрузку динамического контента
time.sleep(5)

# Получаем HTML-код страницы
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Находим все элементы с задачами
task_elements = soup.find_all('div', class_='tree-node')

tasks = []

for task_element in task_elements:
    # Находим div с классом wrapperChild
    wrapper_child = task_element.find('div', class_='wrapperChild')
    if wrapper_child:
        task_id = wrapper_child.get('id')

        # Извлекаем заголовок задачи (предполагая, что он находится в элементе с классом 'task-title')
        title_element = wrapper_child.find('div', class_='task-title')
        title = title_element.text.strip() if title_element else "Без названия"

        # Переходим на страницу задачи для получения описания
        driver.get(f"https://www.leadertask.ru/web/tasks/today/{task_id}")

        # Ждем загрузки описания
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "taskPropsCommentEditor"))
        )

        # Получаем HTML страницы задачи
        task_html = driver.page_source
        task_soup = BeautifulSoup(task_html, 'html.parser')

        # Извлекаем описание
        description_element = task_soup.find('div', id='taskPropsCommentEditor')
        description = description_element.text.strip() if description_element else ""

        tasks.append({
            "id": task_id,
            "title": title,
            "description": description
        })

        # Возвращаемся на страницу со списком задач
        driver.back()

        # Ждем загрузки списка задач
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "vtlist-inner"))
        )

# Выводим результат
for task in tasks:
    print(f"ID: {task['id']}")
    print(f"Заголовок: {task['title']}")
    print(f"Описание: {task['description']}")
    print("---")

# Закрываем браузер
driver.quit()