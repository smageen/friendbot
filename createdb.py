import sqlite3

# Подключение к базе данных (если файл не существует, он будет создан)
conn = sqlite3.connect('users.db')

# Создание курсора для выполнения SQL-запросов
cur = conn.cursor()

# Создание таблицы "users" с необходимыми столбцами
cur.execute('''CREATE TABLE IF NOT EXISTS users (
               user_id INTEGER PRIMARY KEY,
               name TEXT,
               age INTEGER,
               gender TEXT,
               preference TEXT,
               interests TEXT,
               media TEXT,
               media_type TEXT,
               nickname TEXT,
               privacy_accepted INTEGER DEFAULT 0
               )''')

# Создание таблицы "favorites" для хранения любимых пользователей
cur.execute('''CREATE TABLE IF NOT EXISTS favorites (
               user_id INTEGER,
               favorite_user_id INTEGER,
               FOREIGN KEY (user_id) REFERENCES users(user_id),
               FOREIGN KEY (favorite_user_id) REFERENCES users(user_id)
               )''')

# Сохранение изменений и закрытие соединения с базой данных
conn.commit()
conn.close()
