"""
Configuration settings for the social network analysis system
"""

from pathlib import Path


# Директории и пути
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
LOG_DIR = BASE_DIR / "logs"

# Создаем необходимые директории
for directory in [STORAGE_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Ключи социальных сетей
TELEGRAM_KEY = "telegram"
SLACK_KEY = "slack"
VK_KEY = "vk"
WHATSAPP_KEY = "whatsapp"

SOCIAL_NETWORK_DICT = {
    TELEGRAM_KEY: "telegram",
    SLACK_KEY: "slack",
    VK_KEY: "vkontakte",
    WHATSAPP_KEY: "whatsApp",
}

LOG_ROTATION_SIZE = 524288000
MESSAGE_FETCH_LIMIT = 1000


# Telegram API настройки
# TELEGRAM_API = {
#     "SESSION_TEMPLATE": "{phone_number}_session",
#     "APP_VERSION": ,
#     "DEVICE_MODEL": ,
#     "SYSTEM_VERSION": ,
#     "LANG_CODE": ,
#     "SYSTEM_LANG_CODE": ,
# }
class CommandLineArgument:
    """Обозначение командных аргументов"""
    FLAG = "--"

    # Маппинг имен аргументов на их значения
    ARGUMENTS = {
        # При выгрузке
        'USER_SYSTEM_NAME': 'user_system_name',
        'API_HASH': 'api_hash',
        'API_ID': 'api_id',
        'SOCIAL_ACCOUNT_NAME': 'social_account_name',
        'CHAT_NAME': 'chat_name',
        'PHONE': 'phone',
        'OUTPUT': 'output',

        # При анализе
        'FILE': 'file',
        'DATE': 'date',

        # send_report.py
        'PDF': 'pdf',
        'TO': 'to',
        'SUBJECT': 'subject',
        'BODY': 'body',

        # Алиасы для анализа
        'USER_SYSTEM_NAME_ANALYSIS': 'user_system_name',
        'SOCIAL_ACCOUNT_NAME_ANALYSIS': 'social_account_name',
        'CHAT_NAME_ANALYSIS': 'chat_name',
        'PHONE_ANALYSIS': 'phone',
        'OUTPUT_ANALYSIS': 'output',
    }

    def __getattr__(self, name):
        if name in self.ARGUMENTS:
            return self.FLAG + self.ARGUMENTS[name]
        raise AttributeError(f"Argument '{name}' not defined")


class TimezoneConfig:
    """Простая конфигурация часовых поясов"""

    # === ПРОСТО ПОМЕНЯЙТЕ ЭТУ СТРОКУ ===
    APP_TIMEZONE = "Europe/Moscow"  # Ваш часовой пояс здесь

    # === ИЛИ ВЫБЕРИТЕ ОДИН ИЗ ВАРИАНТОВ ===
    # "UTC"                      # Всемирное координированное время
    # "Europe/London"            # Лондон (GMT/BST)
    # "Europe/Berlin"            # Берлин (CET/CEST)
    # "Europe/Moscow"            # Москва (MSK)
    # "Asia/Dubai"               # Дубай (GST)
    # "Asia/Shanghai"            # Шанхай (CST)
    # "Asia/Tokyo"               # Токио (JST)
    # "America/New_York"         # Нью-Йорк (EST/EDT)
    # "America/Los_Angeles"      # Лос-Анджелес (PST/PDT)
    # "Australia/Sydney"         # Сидней (AEST/AEDT)

    # === ИЛИ ФИКСИРОВАННОЕ СМЕЩЕНИЕ ===
    # "UTC+3"                    Москва, Стамбул
    # "UTC+5"                    Екатеринбург, Пакистан
    # "UTC-5"                    Нью-Йорк, Торонто
    # "UTC-8"                    Лос-Анджелес, Ванкувер
    # "UTC+9"                    Токио, Сеул
    # "UTC+10"                   Сидней, Владивосток
    # "UTC-10"                   Гавайи

class SystemConfig:
    """Системные настройки ПК(PC)"""
    TELEGRAM_CLIENT_APP_VERSION = "4.16.8-telethon"
    TELEGRAM_CLIENT_DEVICE_MODEL = "PC"
    TELEGRAM_CLIENT_SYSTEM_VERSION = "Windows 10"
    TELEGRAM_CLIENT_LANG_CODE = "ru"
    TELEGRAM_CLIENT_SYSTEM_LANG_CODE = "ru"



# Типы чатов Telegram
CHAT_TYPE_CHANNEL = "channel"
CHAT_TYPE_CHAT = "chat"
CHAT_TYPE_USER = "user"


# Ключи для данных сообщений
class MessageKeys:
    """Ключи"""
    MESSAGE_ID = "message_id"
    USER_ID = "user_id"
    REPLY_TO = "reply_to_message_id"
    TEXT = "message_text"
    AUTHOR = "author_name"
    DATE = "date"
    REACTIONS = "reactions"
    MENTIONS = "mentions"


#  Форматы и шаблоны
JSON_INDENT = 4


class Extensions:
    """Расширения"""
    JSON_EXTENSION = ".json"
    CHAT_FILE_EXTENSION = JSON_EXTENSION
    PDF_FILE_EXTENSION = ".pdf"
    HTML_FILE_EXTENSION = ".html"


class DateFormat:
    """Форматы дат"""
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
    TIME_FORMAT = "%H-%M-%S"
    DATETIME_FORMAT_TZ = "%Y-%m-%d_%H-%M-%S%z"  # с указанием смещения


# URL шаблоны
TELEGRAM_URLS = {
    "USERNAME": "https://t.me/",
    "CHAT_ID": "https://t.me/c/",
    "CHANNEL": "https://t.me/+/"
}
class ReportPDFSettings:
    """Настройки pdf отчета """
    TOP_LEN = 10

class FileTemplates:
    """Templates for file names and directories"""

    # Дополнительное имя
    METRICS_ADDITIONAL_NAME = "metrics"
    GRAPH_ADDITIONAL_NAME = "graph"
    REPORT_ADDITIONAL_NAME = "report"


    UNLOAD_OF_CHATS_BASE_NAME_LOG = "unload.log"
    ANALYZE_CHAT_BASE_NAME_LOG = "analysis.log"
    ANALYZE_CHAT_BASE_NAME = "analysis"

    # Шаблоны имен файлов
    CHAT_FILENAME = (
        "id={chat_id},account={social_account},"
        "unload_time={date}{extension}"
    )

    PDF_REPORT_FILENAME = "{base_name},type={type_file}," \
                          " time={report_date}{extension}"

    METRICS_FILENAME = "{base_name},type={type_file}," \
                       "time={metrics_date}{extension}"

    GRAPH_VISUALIZATION = (
        "{base_name},type={type_file},time={graph_date}{extension}"
    )

    # Шаблоны путей
    SESSION_PATH = "{storage_path}/session_{phone_number}"
    USER_DIR_PATH = "{base_path}/{user_name}"
    CHAT_DIR_PATH = "{user_path}/{chat_name}"
    FULL_NAME_TEMPLATE = "{first_name} {last_name}"


# Текстовые шаблоны для форматирования графа
class TemplateStrings:
    USER_NODE_TITLE = "ID: {user_id}, Имя: {username}"
    MESSAGE_NODE_TITLE = "message_id: {message_id}"
    OPEN_GRAPH_LINK_TEXT = "Открыть интерактивный граф"


# Ключевые слова для анализа
QUESTION_KEYWORDS = [
    "кто",
    "что",
    "где",
    "когда",
    "почему",
    "как",
    "зачем",
    "сколько",
    "какой",
    "какая",
    "какое",
    "какие",
    "?",
    "ли",
]

# Регулярные выражения
MENTION_REGEX = r"@(\w+)"
REACTION_REGEX = r"(\u2764|\ud83d\ude0d|\ud83d\ude0e|\ud83d\ude0a)"
URL_REGEX = r"https?://[^\s]+"

class LogMessagesMistaken:
    """Сообщения обработок ошибок через Mistaken"""
    PARAM_NAME_DEFAULT = 'object'

    ERROR_TYPE_MISMATCH = "Объект '{param_name}' должен быть типа {expected_type}, получен {actual_type}"
    ERROR_NONE_OBJECT = "Объект '{param_name}' не может быть None"
    ERROR_EMPTY_STRING = "Строка '{param_name}' не может быть пустой"
    ERROR_EMPTY_COLLECTION = "Коллекция '{param_name}' не может быть пустой"
    ERROR_FUNCTION_EXECUTION = "Ошибка в функции '{function_name}': {error}"


# Сообщения для логов
class LogMessages:
    """Информационные"""
    # Настройка логгера
    INFO_LOGGER_SUCCESS = "Логер удачно настроен!"


    # При выгрузке nloading_of_chats
    HELP_TELEGRAM_INFO_UNLOADING_DATA = "Выгрузка данных из Telegram чата"
    HELP_TELEGRAM_USER_SYSTEM_NAME = "Имя пользователя системы"
    HELP_TELEGRAM_API_HASH = "API_HASH"
    HELP_TELEGRAM_API_ID = "API_ID"
    HELP_TELEGRAM_SOCIAL_ACCOUNT_NAME = "Название социальной сети"
    HELP_TELEGRAM_CHAT_NAME = "Название чата для выгрузки"
    HELP_TELEGRAM_PHONE = "Номер телефона для авторизации"
    HELP_TELEGRAM_OUTPUT = "Директория для сохранения данных(если не указана," \
                           " используется по умолчанию путь формата: " \
                           "storage/<user>/<social>/<phone>/<chat>" \
                           "/<"+ str(DateFormat.DATE_FORMAT) + ">/... " + str(Extensions.JSON_EXTENSION)





    INFO_CONNECT_SUCCESS = "Подключение успешно."
    INFO_DATA_START = "Начинаем выгрузку данных из чата: {chat_name}"
    INFO_DATA_SAVED = "Данные сохранены в файл: {file_path}"

    INFO_CHAT_FOUND = "Найден чат: {chat_name} (ID: {chat_id})"

    INFO_OBJECT_CHAT = (
        "Chat(ID='{chat_id}', Type='{chat_type}', "
        "Social='{social_account_name}')"
    )
    INFO_OBJECT_USER = "User(name='{self.name}', " \
                       "phones='{self.phone_numbers}')"

    # Предупреждения
    WARNING_CHAT_NOT_FOUND = (
        "Чат '{chat_name}' не найден. Доступные чаты: {available_chats}"
    )
    WARNING_NOT_ACCESS_SOCIAL_NETWORK = "Не доступная социальная сеть"

    # ОШИБКИ
    ERROR_DATA_UNLOADING = "Ошибка при выгрузке данных"



    ERROR_FUNCTION_EXECUTION = "Ошибка в функции {function_name}: {error}"
    ERROR_ENTITY_FETCH_FAILED = "Не удалось получить entity для {chat_id}"

    # Ошибки при выгрузке
    ERROR_NETWORK_SOCIAL = "Неподдерживаемая соцсеть: {social_account_name}"



    ERROR_VALIDATION_ARGUMENTS = "Ошибка валидации аргументов: {error}"
    # Ошибки графа
    ERROR_USER_NOT_FOUND = "Пользователь не найден: {user_id}"
    ERROR_USERS_NOT_FOUND = (
        "Пользователи не найдены: from_user={from_user_id},"
        " to_user={to_user_id}"
    )

    # для FileManager
    INFO_BASE_DIRECTORY_CREATED = (
        "Базовая директория FileManager создана: {directory_path}"
    )
    INFO_DIRECTORY_CREATED = "Создана директория: {directory_path}"
    INFO_CHAT_STORAGE_PATH = "Путь хранения чата: {storage_path}"
    INFO_CHAT_DATA_SAVED = "Данные чата сохранены в: {file_path}"

    WARNING_FILE_NOT_FOUND = "Файл не найден: {file_path}"
    INFO_DATA_LOADED_SUCCESS = "Успешно загружено {count}" \
                               " записей из {file_path}"
    ERROR_JSON_DECODE = "Ошибка декодирования JSON в файле" \
                        " {file_path}: {error}"

    ERROR_FILE_READING = "Ошибка чтения файла {file_path}: {error}"
    ERROR_CHAT_DATA_SAVING = (
        "Ошибка при сохранении данных для чата '{chat_name}': {error}"
    )

    # FileManager Сохранение отчета
    PDF_REPORT_TITLE = "Отчет по чату: {chat_name}"
    INFO_PDF_REPORT_SAVED = "Отчет успешно сохранен в: {file_path}"
    ERROR_PDF_REPORT_CREATION = "Не удалось создать PDF отчет"

    # Сохранение метрик (используется FileManager)
    INFO_METRICS_SAVED = "Метрики анализа сохранены в файл: {file_path}"
    ERROR_METRICS_SAVING = "Ошибка при сохранении метрик в" \
                           " {directory_path}: {error}"
    METRICS_DEBUG_WARNING = "Метрики центральности отсутствуют"

    # analysis_chat.py
    ERROR_ANALYSIS_NO_DATA = "Нет выгрузок до указанной даты."
    ERROR_ANALYSIS_WRONG_DATE_FORMAT = (
        "Неверный формат даты: {date}. Ожидается YYYY-MM-DD"
    )

    # Для analysis_chat.py Анализ
    INFO_ANALYSIS_START = "Начинаем анализ данных из файла: {data_file}"
    ERROR_DATA_LOADING = "Не удалось загрузить данные для анализа"
    INFO_MESSAGES_LOADED = "Загружено {count} сообщений для анализа"
    INFO_ANALYSIS_RESULTS_SAVED = "Результаты анализа сохранены в: {file_path}"

    # CLI помощь для analysis_chat.py (добавлено для совместимости)
    HELP_ANALYSIS_DESCRIPTION = "Анализ данных чата из JSON файла"
    HELP_ANALYSIS_FILE = "Путь к файлу с данными чата (JSON)"
    HELP_ANALYSIS_OUTPUT = "Директория (обычно папка чата)" \
                           " для сохранения результатов"
    HELP_ANALYSIS_DATE = (
        "Фильтр по дате выгрузки (YYYY-MM-DD). Берём последнюю на/до даты"
    )

    # Тексты CLI вывода
    ANALYSIS_CLI_HEADER = "РЕЗУЛЬТАТЫ АНАЛИЗА ЧАТА"
    INFO_ANALYSIS_DIR = "Директория с результатами: {path}"
    INFO_METRICS_FILE_PATH = "Файл с метриками: {file_path}"
    INFO_VISUALIZATION_FILE_PATH = "Визуализация графа: {file_path}"

    INFO_SUMMARY_USERS = "Всего пользователей: {value}"
    INFO_SUMMARY_INTERACTIONS = "Всего взаимодействий: {value}"
    INFO_SUMMARY_MESSAGES = "Всего сообщений: {value}"
    INFO_TOP_ACTIVE_HEADER = "Топ-{top_len} самых активных пользователей:"

    INFO_TOP_ACTIVE_LINE = "  - {username}: {value} сообщений"
    INFO_METRICS_HEADER = "Ключевые метрики:"


# Настройки визуализации графа
class GraphVisualizationSettings:
    """Settings for graph visualization"""

    MIN_NODE_SIZE = 20
    MAX_NODE_SIZE = 50
    MIN_EDGE_WIDTH = 1
    MAX_EDGE_WIDTH = 10

    # Настройки сети
    NETWORK_HEIGHT = "800px"
    NETWORK_WIDTH = "100%"
    NETWORK_BG_COLOR = "#222222"
    NETWORK_FONT_COLOR = "white"
    NETWORK_DIRECTED = True
    NETWORK_NOTEBOOK = False

    # Цвета узлов
    ANONYMOUS_USER_COLOR = "#FF6B6B"
    REGULAR_USER_COLOR = "#4ECDC4"

    # Формы узлов
    ANONYMOUS_USER_SHAPE = "box"
    REGULAR_USER_SHAPE = "dot"

    # Размеры
    NODE_SIZE = 25
    EDGE_WIDTH = 2

    # Цвета ребер по типам
    MESSAGE_COLOR = "#1F77B4"
    REPLY_COLOR = "#FF7F0E"
    MENTION_COLOR = "#2CA02C"
    REACTION_COLOR = "#9467BD"

    # Прочие настройки
    ARROWS_DIRECTION = "to"


    PHYSICS_ENABLED = True
    REPULSION = 6000  # увеличенное отталкивание
    SPRING_LENGTH = 500  # увеличенное расстояние
    GRAVITY = 0.0  # Слабая гравитация
    CENTRAL_GRAVITY = 0.0  # Слабое притяжение к центру

    AVOID_OVERLAP = 0.9  # Избегать перекрытия узлов (0-1)
    EDGE_SMOOTH_TYPE = "continuous"  # Тип сглаживания ребер
    SPRING_CONSTANT = 0.02  # Жесткость пружин (меньше = мягче)
    DAMPING = 0.1  # Затухание
    BARNES_HUT_OPTIMIZE = True  # Использовать оптимизацию Barnes-Hut


    # Цветовая градация для ребер (от зеленого к красному)
    EDGE_COLORS = ["#00ff00", "#ffff00", "#ff0000"]  # green -> yellow -> red

class PythonSettings:
    """Settings for Python-specific operations"""

    # Режимы работы с файлами
    FILE_READ_MODE = "r"
    FILE_WRITE_MODE = "w"

    # Кодировки
    ENCODING_UTF8 = "utf-8"

    # Магические методы
    DUNDER_LEN = "__len__"

