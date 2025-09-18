from enum import Enum


class CommandSystemArgument:
    USER_SYSTEM_NAME = "user_system_name"
    SOCIAL_ACCOUNT_NAME = "social_account_name"
    PHONE = "phone"
    CHAT_NAME = "chat_name"


class TelegramEntityAttributes(str, Enum):
    """Атрибуты объектов Telegram"""

    TITLE = "title"
    NAME = "name"
    USERNAME = "username"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    ID = "id"
    PHONE = "phone"
    ACCESS_HASH = "access_hash"
    VERIFIED = "verified"
    BOT = "bot"
    RESTRICTED = "restricted"


class AnalysisAttributes(str, Enum):
    """Атрибуты для анализа метрик и создания отчета"""

    USER_ID = "user_id"
    USERNAME = "username"
    VALUE = "value"
    TOP_REPLIERS = "top_repliers"

    TOP_REPLIED_TO = "top_replied_to"
    TOTAL_REPLIES = "total_replies"
    TOP_QUESTION_ASKERS = "top_question_askers"
    TOTAL_QUESTIONS = "total_questions"

    TOP_ACTIVE_USERS = "top_active_users"
    TOP_POPULAR_USERS = "top_popular_users"
    TOP_ENGAGED_USERS = "top_engaged_users"
    DEGREE_CENTRALITY = "degree_centrality"

    BETWEENNESS_CENTRALITY = "betweenness_centrality"
    CLOSENESS_CENTRALITY = "closeness_centrality"
    EIGENVECTOR_CENTRALITY = "eigenvector_centrality"
    TOP_ACTIVE_WRITERS = "top_active_writers"

    MOST_INFLUENTIAL = "most_influential"
    TOP_BETWEENNESS_LEADERS = "top_betweenness_leaders"
    NETWORK_HUBS = "network_hubs"
    SUMMARY = "summary"

    TOTAL_USERS = "total_users"
    TOTAL_INTERACTIONS = "total_interactions"
    TOTAL_MESSAGES = "total_messages"
    ACTIVITY_ANALYSIS = "activity_analysis"

    REPLY_ANALYSIS = "reply_analysis"
    QUESTION_ANALYSIS = "question_analysis"
    CENTRALITY_METRICS = "centrality_metrics"
    OPINION_LEADERS = "opinion_leaders"

    NETWORK_PROPERTIES = "network_properties"
    DENSITY = "density"
    AVERAGE_CLUSTERING = "average_clustering"
    IS_CONNECTED = "is_connected"

    NUMBER_OF_COMPONENTS = "number_of_components"
    OUT_DEGREE = "out_degree"
    IN_DEGREE = "in_degree"
    TOTAL_DEGREE = "total_degree"

    METRICS_FILE = "metrics_file"
    VISUALIZATION_FILE = "visualization_file"
    ANALYSIS_DIR = "analysis_dir"

    # Для Отчета:
    ANALYSIS_REPORT = "pdf_report_file"


class ChatObjectAttributes(str, Enum):
    """Атрибуты объектов чата"""

    CHAT_URL = "chat_url"
    ID = "id"
    USERNAME = "username"
    TITLE = "title"
    NAME = "name"


class MessageKeys(str, Enum):
    MESSAGE_ID = "message_id"
    USER_ID = "user_id"
    REPLY_TO_ID = "reply_to_message_id"
    MESSAGE_TEXT = "message_text"
    AUTHOR_NAME = "author_name"
    UNKNOWN_AUTHOR = "unknown_author"
    DATE = "date"
    REACTIONS = "reactions"
    MENTIONS = "mentions"


class KnotType(str, Enum):
    USER = "user"
    MESSAGE = "message"


class EdgeType(Enum):
    MESSAGE = 1  # Обычное сообщение
    REPLY = 2  # Ответ на сообщение
    MENTION = 3  # Упоминание @username
    REACTION = 4  # Реакция (❤️, 👍 и т.д.)
    FORWARD = 5  # Пересланное сообщение
