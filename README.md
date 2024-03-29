# hw05_final

### Описание проекта
>>
Проект социальной сети Yatube. 
Позволяет публиковать заметки и размещать к ним фото или любую другую картинку. Также можно смотреть и комментировать заметки других пользователей,
подписываться на понравившихся авторов. Написан бэкенд, тесты, созданы шаблоны с css.

### Технологии
 - _Python 3.9.7
 - _Django 2.2.16
 - _Pillow 8.3.1
 - _Unittest


### Как запустить проект:

Клонировать репозиторий:

```
git clone git@github.com:sasa9089/hw05_final.git
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

Создать и запустить миграции
```
python manage.py makemigrations
python manage.py migrate
```

Запустить локальный сервер
```
python manage.py runserver
```

Функционал:
- Создаются и редактируются собственные записи;
- Добавляются изображения к посту;
- Просмотриваются страницы других авторов;
- Комментируются записи других авторов;
- Подписки и отписки от авторов;
- Записи назначаются в отдельные группы;
- Личная страница для публикации записей;
- Отдельная лента с постами авторов на которых подписан пользователь;
- Через панель администратора модерируются записи, происходит управление пользователями и создаются группы.
