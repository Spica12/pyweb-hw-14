# Домашнє завдання #14

У цьому домашньому завданні ми продовжуємо доопрацьовувати наш REST API застосунок із домашнього завдання 13.

## Завдання

За допомогою Sphinx створіть документацію для вашого домашнього завдання. Для цього додайте в основних модулях до необхідних функцій і методів класів рядки docstrings.
Покрийте модульними тестами модулі репозиторію домашнього завдання, використовуючи фреймворк Unittest. За основу візьміть приклад із конспекту для модуля tests/test_unit_repository_notes.py
Покрийте функціональними тестами будь-який маршрут на вибір з вашого домашнього завдання, використовуючи фреймворк pytest.


## Додаткове завдання

Покрийте ваше домашнє завдання тестами більш ніж на 95%. Для контролю використовуйте пакет pytest-cov

----

## Інструкція для запуску

Для запуску цього проекту, впевніться, що у вас встановлено Docker та Docker Compose.

1. Склонуйте цей репозиторій на свій локальний комп'ютер:

```
git clone https://github.com/Spica12/pyweb-hw-13.git
```

2. Перейдіть у директорію проекту:

```
cd pyweb-hw-13
```

3. Створіть файл .env у кореневій директорії проекту, використовуючи приклад .env.example:

```
cp .env.example .env
```

4. Відкрийте файл .env у вашому текстовому редакторі та вкажіть необхідні значення змінних середовища. Зверніть увагу, що для запуску PostgresSQL та Redis в docker-compose необхідно вказати наступні параметри:

```
POSTGRES_DOMAIN=postgres
REDIS_DOMAIN=redis
```

5. Запустіть проект за допомогою docker-compose:

```
docker-compose up --build
```

Після успішного запуску проекту, він буде доступний за адресою http://localhost:8000 у вашому веб-браузері.