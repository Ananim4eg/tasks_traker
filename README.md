# Базовое использование (создаст 5 пользователей и 10 задач)
python manage.py init_data

# С указанием количества пользователей и задач
python manage.py init_data --users-count 10 --tasks-count 20

# С очисткой существующих данных
python manage.py init_data --clear

# Комбинация параметров
python manage.py init_data --users-count 8 --tasks-count 15 --clear

# Оставить суперпользователя
python manage.py reset_data

# Удалить суперпользователя
python manage.py reset_data --delete-superuser