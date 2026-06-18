@echo off
echo Создание виртуального окружения...
python -m venv .venv
echo Установка зависимостей...
call .venv\Scripts\activate
pip install -r requirements.txt
echo Установка завершена.
pause