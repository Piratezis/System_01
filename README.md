# active_system

Коротко о проекте

- Выгрузка чатов (Telegram) в JSON по структуре storage/<user>/<social>/<phone>
  /<chat>/<YYYY-MM-DD>/id=...,date=YYYY-MM-DD_HH-MM-SS.json
- Анализ выгрузки: метрики JSON + HTML граф + PDF-отчет в подпапке analysis до
  выбранной даты или последняя свежая дата
- Отправка PDF-отчета на e-mail

## Настройка внешних сервисов для системы. Требуется для коректности создания отчетов:

```https://dejavu-fonts.github.io/Download.html
1. Скачайте архив по ссылке
2. Разархивируйте
3. Возьмите файл dejavu-sans.ttf из папки ttf
4. Положите в корень проекта как DejaVuSans.ttf```
```

## Настройка внешних сервисов для Telegram
# Для работы с Telegram API необходимо получить учетные данные на официальном портале разработчиков Telegram.
``` Шаги получения API-ключей:
1) Откройте my.telegram.org
2) Войдите с вашим номером телефона Telegram(ВАЖНО: на аккаунте не должно быть ограничений, наложенных Telegram)
3) В разделе "API Development Tools"
Заполните обязательные поля:

App title: Название вашего приложения (например, "Chat Analyzer")
Short name: Короткое имя (латинскими буквами)
Platform: Desktop (или иная, под ваши нужды)
Description: Описание функциональности

4) нажмите "Create application"
5) Копируйте и сохраните api_id и api_hash

```

## Установка окружения

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Выгрузка данных чата (unloading_of_chats.py)

- о том как получить .json файл вашего чата Telegram
- Чтобы получить подсказку о вводимых аргументах введите в консоли терминала:

```commandline
    python unloading_of_chats.py -h
```

```powershell
python unloading_of_chats.py --user_system_name "Имя пользователя" --api_id 33330000 --api_hash "40b85b1a818c842836e7f5fb0bdcadb7" --social_account_name telegram --chat_name "Название вашего чата" --phone +79935554499
```

Файл(ы) выгрузки создаются по пути:

```
storage/<user>/<social>/<phone>/<chat>/<YYYY-MM-DD>/id=...,social_account=...,date=YYYY-MM-DD_HH-MM-SS.json
```

## Анализ чата и метрики (analysis_chat.py)

- о том как проанализировать .json файл вашего чата Telegram и получить .json с
  метриками, граф в формате HTML, отчет в формате .pdf
- Чтобы получить подсказку о вводимых аргументах введите в консоли терминала:

```commandline
    python analysis_chat.py -h
```

Есть два способа анализа выгрузок из чата:

1. Последняя совершенная выгрузка из storage/....

```powershell
python analysis_chat.py --user_system_name "Имя пользователя" --social_account_name telegram --chat_name "Название вашего чата" --phone +79935554499
```

2. Выгрузка последняя до даты не включая её (YYYY-MM-DD) из storage/....

```powershell
python analysis_chat.py --user_system_name "Имя пользователя" --social_account_name telegram --chat_name "Название вашего чата" --phone +79935554499 --date 2025-09-06
```

Результаты сохраняются в папке даты в подпапку `analysis`: метрики (.json),
граф (.html), PDF-отчет (.pdf).

Примечание: для корректного отображения кириллицы в PDF
положите `DejaVuSans.ttf` рядом с проектом.

_________________________Еще не реализовано____________________________________

## Отправка PDF-отчёта на почту (send_report.py)

- о том как отправить отчет pdf на почту пользователя
- Чтобы получить подсказку о вводимых аргументах введите в консоли терминала:

```commandline
    python send_report.py -h
```

1. Найти последний PDF и отправить, введите:

```powershell
$p = "C:\\Users\\Админ\\PycharmProjects\\active_system\\storage\\Илья Волков\\telegram\\79935474292\\Обсудим восхождение по низу"; $d=(Get-ChildItem $p -Directory | Sort-Object Name -Descending | Select-Object -First 1).FullName; $a=Join-Path $d "analysis"; $pdf=(Get-ChildItem $a -Filter *.pdf | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName; python send_report.py --pdf "$pdf" --to "email@example.com"
```

## Примечания

- В логах (`logs/`) можно смотреть ход выгрузки/анализа.
- Граф показывает пользователей как узлы; рёбра — типы взаимодействий (MESSAGE,
  REPLY, MENTION, REACTION). Наведение на узел показывает `user_id` и имя.


