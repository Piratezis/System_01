import json
from pyvis.network import Network
from pathlib import Path
from loguru import logger
from datetime import timezone, timedelta
from abc import ABC, abstractmethod
import smtplib
from email.message import EmailMessage
import networkx as nx
import pytz
import os
from datetime import datetime

from typing import (List,
                    Dict,
                    Any,
                    Callable)

from scr.config import (
    LogMessages,
    GraphVisualizationSettings,
    FileTemplates,
    PythonSettings,
    DateFormat,
    TimezoneConfig,
    QUESTION_KEYWORDS,
    Extensions,
    ReportPDFSettings

)

from scr.enums import (EdgeType,
                       AnalysisAttributes,
                       MessageKeys,
                       ChatObjectAttributes)

from scr.models import (Mistaken,
                        Chat,
                        Graph)

# Работа с pdf
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import ParagraphStyle

import heapq


# _____________________________________________________________________________

class BaseAnalyzer(ABC):
    def __init__(self, nx_graph):
        self.nx_graph = nx_graph
        self.top_limit = ReportPDFSettings.TOP_LEN

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        pass

    def get_top_users_with_names(self, metric_dict: Dict[int, Any]) -> List[
        Dict]:
        # Берём топ-N по значению без полной сортировки
        top_n = heapq.nlargest(self.top_limit, metric_dict.items(),
                               key=lambda x: x[1])

        # Формируем результат, получая username только для отобранных пользователей
        result = []
        for user_id, value in top_n:
            username = self.get_username(user_id)
            result.append({
                AnalysisAttributes.USER_ID.value: user_id,
                AnalysisAttributes.USERNAME.value: username,
                AnalysisAttributes.VALUE.value: value,
            })
        return result

    def get_username(self, user_id: int) -> str:
        node_data = self.nx_graph.nodes.get(user_id, {})
        return node_data.get(AnalysisAttributes.USERNAME.value, str(user_id))


# _____________________________________________________________________________
class ActivityAnalyzer(BaseAnalyzer):
    """считает степени по всем ребрам графа"""

    def analyze(self) -> Dict[str, Any]:
        out_degree = dict(self.nx_graph.out_degree())
        in_degree = dict(self.nx_graph.in_degree())
        total_degree = dict(self.nx_graph.degree())

        return {
            AnalysisAttributes.TOP_ACTIVE_USERS.value: self.get_top_users_with_names(
                out_degree),
            AnalysisAttributes.TOP_POPULAR_USERS.value: self.get_top_users_with_names(
                in_degree),
            AnalysisAttributes.TOP_ENGAGED_USERS.value: self.get_top_users_with_names(
                total_degree),
        }


# _____________________________________________________________________________
class ReplyAnalyzer(BaseAnalyzer):
    """Cчитает степени только по ребрам с attr["type"] == EdgeType.REPLY"""

    def analyze(self) -> Dict[str, Any]:
        reply_edges = [
            (u, v) for u, v, attr in self.nx_graph.edges(data=True)
            if attr.get("type") == EdgeType.REPLY
        ]

        reply_G = nx.DiGraph()
        reply_G.add_edges_from(reply_edges)

        replies_from = dict(reply_G.out_degree())
        replies_to = dict(reply_G.in_degree())

        return {
            AnalysisAttributes.TOP_REPLIERS.value: self.get_top_users_with_names(
                replies_from),
            AnalysisAttributes.TOP_REPLIED_TO.value: self.get_top_users_with_names(
                replies_to),
            AnalysisAttributes.TOTAL_REPLIES.value: sum(replies_from.values()),
        }


# _____________________________________________________________________________
class CentralityAnalyzer(BaseAnalyzer):
    def __init__(self, nx_graph: nx.DiGraph):
        super().__init__(nx_graph)
        self.centrality_metrics = None

    def analyze(self) -> Dict[str, Any]:
        if self.centrality_metrics is None:
            self.centrality_metrics = self.calculate_centrality_metrics()
        return self.centrality_metrics

    def calculate_centrality_metrics(self) -> Dict[str, Any]:
        """Calculation of various centrality metrics"""
        degree_centrality = nx.degree_centrality(self.nx_graph)
        betweenness_centrality = nx.betweenness_centrality(self.nx_graph)
        closeness_centrality = nx.closeness_centrality(self.nx_graph)
        eigenvector_centrality = nx.eigenvector_centrality(self.nx_graph,
                                                           max_iter=1000)

        return {
            AnalysisAttributes.DEGREE_CENTRALITY: self.get_top_users_with_names(
                degree_centrality
            ),
            AnalysisAttributes.BETWEENNESS_CENTRALITY: self.get_top_users_with_names(
                betweenness_centrality
            ),
            AnalysisAttributes.CLOSENESS_CENTRALITY: self.get_top_users_with_names(
                closeness_centrality
            ),
            AnalysisAttributes.EIGENVECTOR_CENTRALITY: self.get_top_users_with_names(
                eigenvector_centrality
            )
        }


# _____________________________________________________________________________
class QuestionAnalyzer(BaseAnalyzer):
    """
    Анализатор вопросов в чате
    """

    def __init__(self, nx_graph: nx.DiGraph):
        super().__init__(nx_graph)
        self._question_stats = None

    def analyze(self) -> Dict[str, Any]:
        """Основной метод анализа вопросов"""
        if self._question_stats is None:
            self._question_stats = self._calculate_question_stats()
        return self._question_stats

    def _calculate_question_stats(self) -> Dict[str, Any]:
        """Вычисляет статистику по вопросам"""
        question_count = self._count_questions()

        return {
            AnalysisAttributes.TOP_QUESTION_ASKERS.value: self.get_top_users_with_names(
                question_count),
            AnalysisAttributes.TOTAL_QUESTIONS.value: sum(
                question_count.values()),
        }

    def _count_questions(self) -> Dict[int, int]:
        """Подсчитывает вопросы по пользователям"""
        question_count = {}

        # Проходим по всем ребрам графа
        for from_user, to_user, attr in self.nx_graph.edges(data=True):
            if (self._is_message_edge(attr) and
                    self._is_question(attr.get("content", ""))):
                question_count[from_user] = question_count.get(from_user,
                                                               0) + 1

        return question_count

    def _is_message_edge(self, edge_attr: Dict) -> bool:
        """Проверяет, является ли ребро сообщением"""
        return edge_attr.get("type") == EdgeType.MESSAGE

    def _is_question(self, text: str) -> bool:
        """Проверяет, является ли текст вопросом"""
        if not text or not isinstance(text, str):
            return False

        text_lower = text.lower().strip()

        # Проверка на знак вопроса в конце
        if text_lower.endswith('?'):
            return True

        # Проверка на ключевые слова из config.py
        return any(keyword in text_lower for keyword in QUESTION_KEYWORDS)

    def get_user_question_stats(self, user_id: int) -> Dict[str, int]:
        """Возвращает статистику вопросов для конкретного пользователя"""
        question_count = self._count_questions()
        return {
            "questions_count": question_count.get(user_id, 0),
            "total_questions": sum(question_count.values())
        }

    def get_question_keywords_usage(self) -> Dict[str, int]:
        """Анализирует использование ключевых слов в вопросах"""
        keyword_usage = {keyword: 0 for keyword in QUESTION_KEYWORDS}

        for _, _, attr in self.nx_graph.edges(data=True):
            if self._is_message_edge(attr):
                content = attr.get("content", "")
                if content and self._is_question(content):
                    text_lower = content.lower()
                    for keyword in QUESTION_KEYWORDS:
                        if keyword in text_lower:
                            keyword_usage[keyword] += 1

        return keyword_usage


# _____________________________________________________________________________

class ChatAnalyzer:
    """
    Координирует работу анализаторов
    """

    def __init__(self, graph):
        self.graph = graph
        self.nx_graph = self.convert_to_nx_graph()

        # Инициализируем анализаторы
        self.analyzers = {
            'activity': ActivityAnalyzer(self.nx_graph),
            'reply': ReplyAnalyzer(self.nx_graph),
            'question': QuestionAnalyzer(self.nx_graph),
            'centrality': CentralityAnalyzer(self.nx_graph)
        }

    def convert_to_nx_graph(self) -> nx.DiGraph:
        """Converts an internal Graph to a NetworkX graph"""
        G = nx.DiGraph()

        # Добавляем узлы (пользователей)
        for user_id, knot in self.graph.users.items():
            G.add_node(user_id,
                       username=knot.username)

        # Добавляем рёбра (взаимодействия)
        for edge in self.graph.edges.values():
            G.add_edge(
                edge.from_user.user_id,
                edge.to_user.user_id,
                type=edge.edge_type,
                content=edge.content
            )

        return G

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Собирает метрики от всех анализаторов"""
        metrics = {
            AnalysisAttributes.SUMMARY.value: self._get_summary(),
            AnalysisAttributes.NETWORK_PROPERTIES.value: self._get_network_properties()
        }

        # Добавляем метрики от всех анализаторов
        for analyzer_name, analyzer in self.analyzers.items():
            metrics.update(analyzer.analyze())

        return metrics

    def _get_summary(self) -> Dict[str, Any]:
        return {
            AnalysisAttributes.TOTAL_USERS.value: len(self.graph.users),
            AnalysisAttributes.TOTAL_INTERACTIONS.value: len(self.graph.edges),
            AnalysisAttributes.TOTAL_MESSAGES.value: sum(
                dict(self.nx_graph.out_degree()).values()
            ),
        }

    def _get_network_properties(self) -> Dict[str, Any]:
        return {
            "density": nx.density(self.nx_graph),
            "average_clustering": nx.average_clustering(
                self.nx_graph.to_undirected()),
            "is_connected": nx.is_weakly_connected(self.nx_graph),
            "number_of_components": nx.number_weakly_connected_components(
                self.nx_graph),
        }

# _____________________________________________________________________________
class TimeManager:
    @classmethod
    def now_formatted(cls) -> str:
        """Текущее время в формате из конфига с учетом таймзоны"""
        return datetime.now(cls.get_timezone()).strftime(
            DateFormat.DATETIME_FORMAT)

    @staticmethod
    def get_timezone():
        """Получает часовой пояс из конфига"""
        tz_string = TimezoneConfig.APP_TIMEZONE.upper()

        if tz_string == "UTC":
            return timezone.utc
        elif tz_string.startswith("UTC+"):
            hours = int(tz_string[4:])
            return timezone(timedelta(hours=hours))
        elif tz_string.startswith("UTC-"):
            hours = int(tz_string[4:])
            return timezone(timedelta(hours=-hours))

        # Для названий городов нужен pytz
        try:
            return pytz.timezone(TimezoneConfig.APP_TIMEZONE)
        except:
            return timezone.utc  # fallback

# _____________________________________________________________________________
class FileManager:
    """
    Класс для управления файлами: сохранения и загрузки данных.
    Работает с объектами pathlib.Path для удобства и надежности.
    """

    def __init__(self,
                 base_storage_dir: Path):  # Ожидает Path для корневой директории
        self.base_storage_dir = base_storage_dir
        self.base_storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            LogMessages.INFO_BASE_DIRECTORY_CREATED.format(
                directory_path=self.base_storage_dir
            )
        )

    def create_object_dir(self, obj_dir_name: str, parent_dir: Path):
        """
        Создает директорию для объекта внутри указанной родительской директории.

        Args:
            obj_dir_name (str): Имя папки.
            parent_dir (pathlib.Path): Родительская директория, где будет создана папка.

        Returns:
            pathlib.Path: Полный путь к созданной директории.
        """

        new_dir_path = parent_dir / obj_dir_name
        new_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(
            LogMessages.INFO_DIRECTORY_CREATED.format(
                directory_path=new_dir_path)
        )
        return new_dir_path

    def save_chat_json(self, chat: Chat, data: List[Dict[str, Any]]) -> Path:
        """
        Сохраняет данные чата в JSON-файл в папке, соответствующей дате выгрузки.
        Возвращает полный Path к сохраненному файлу.
        """
        # Валидация входных параметров
        Mistaken.validate_all(chat, Chat, param_name="chat")
        Mistaken.validate_all(data, list, param_name="data")
        dir_datetime_date = datetime.now().strftime(DateFormat.DATE_FORMAT)
        # Создаем полный путь к папке с датой выгрузки
        logger.info(
            LogMessages.INFO_CHAT_STORAGE_PATH.format(
                storage_path=chat.storage_path)
        )
        dir_path = chat.storage_path / dir_datetime_date

        # Создаем директорию. exist_ok=True предотвращает ошибку, если папка уже существует
        dir_path.mkdir(parents=True, exist_ok=True)

        # Имя файла включает точное время, чтобы не перезаписывать выгрузки в один день
        file_timestamp = TimeManager.now_formatted()
        file_name = FileTemplates.CHAT_FILENAME.format(
            chat_id=chat.chat_id,
            social_account=chat.social_account.name,
            date=file_timestamp,
            extension=Extensions.CHAT_FILE_EXTENSION,
        )
        file_path = dir_path / file_name

        try:
            with open(
                    file_path,
                    PythonSettings.FILE_WRITE_MODE,
                    encoding=PythonSettings.ENCODING_UTF8,
            ) as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(
                LogMessages.INFO_CHAT_DATA_SAVED.format(file_path=file_path))
            return file_path
        except IOError as e:
            logger.error(
                LogMessages.ERROR_CHAT_DATA_SAVING.format(chat_name=chat.name,
                                                          error=e)
            )
            raise

    def load_chat_json(self, file_path: Path) -> List[Dict[str, Any]] | None:
        """
        Загружает данные из JSON-файла.
        """
        try:
            if not file_path.exists():
                logger.warning(
                    LogMessages.WARNING_FILE_NOT_FOUND.format(
                        file_path=file_path)
                )
                return None

            with open(
                    file_path,
                    PythonSettings.FILE_READ_MODE,
                    encoding=PythonSettings.ENCODING_UTF8,
            ) as f:
                data = json.load(f)
                logger.info(
                    LogMessages.INFO_DATA_LOADED_SUCCESS.format(
                        count=len(data), file_path=file_path
                    )
                )
                return data
        except json.JSONDecodeError as e:
            logger.error(
                LogMessages.ERROR_JSON_DECODE.format(file_path=file_path,
                                                     error=e)
            )
        except IOError as e:
            logger.error(
                LogMessages.ERROR_FILE_READING.format(file_path=file_path,
                                                      error=e)
            )
        return None

    def save_metrics_to_directory(
            self,
            analyzer: ChatAnalyzer,
            base_name: str,
            directory_path: Path,
            type_file: str,
            extension: str,
            metrics_date: str
    ) -> Path:

        try:

            filename = FileTemplates.METRICS_FILENAME.format(
                base_name=base_name,
                type_file=type_file,
                metrics_date=metrics_date,
                extension=extension,
            )

            # Полный путь к файлу
            file_path = directory_path / filename

            # Получаем метрики и сохраняем
            metrics = analyzer.get_comprehensive_metrics()

            with open(
                    file_path,
                    PythonSettings.FILE_WRITE_MODE,
                    encoding=PythonSettings.ENCODING_UTF8,
            ) as file:
                json.dump(metrics, file, ensure_ascii=False, indent=2)

            logger.info(
                LogMessages.INFO_METRICS_SAVED.format(file_path=file_path))
            return file_path

        except Exception as e:
            logger.error(
                LogMessages.ERROR_METRICS_SAVING.format(
                    directory_path=directory_path, error=e
                )
            )
            raise

    def create_pdf_report(
            self,
            metrics_data: dict,
            report_date: str,
            analysis_dir: Path,
            base_name: str,
            extension: str,
            chat_name: str,
            type_file: str,
            graph_file: str | None = None
    ) -> Path:
        """
        Creates a PDF report from chat analysis data.
        Universal version that works with any metrics structure.
        """
        try:
            logger.debug(
                f"Анализ директория существует: {analysis_dir.exists()}")
            logger.debug(
                f"Метрики данных keys: {list(metrics_data.keys()) if metrics_data else 'None'}")
            logger.debug(f"Граф файл: {graph_file}")


            # Формируем имя файла
            file_name = FileTemplates.PDF_REPORT_FILENAME.format(
                base_name=base_name,
                type_file=type_file,
                report_date=report_date,
                extension=extension,
            )

            logger.debug(f"Сформировано имя файла: {file_name}")

            # Сохраняем в указанную папку анализа
            analysis_dir.mkdir(parents=True, exist_ok=True)
            file_path = analysis_dir / file_name
            logger.debug(f"Полный путь к файлу: {file_path}")

            # Проверка доступности шрифта
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
                logger.debug("Шрифт DejaVuSans успешно зарегистрирован")
            except Exception as font_error:
                logger.error(f"Ошибка регистрации шрифта: {font_error}")
                # Пробуем стандартный шрифт
                try:
                    pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
                    logger.debug("Используем шрифт Arial как fallback")
                except:
                    logger.warning(
                        "Используем стандартный шрифт без кириллицы")

            # Создаем PDF документ
            doc = SimpleDocTemplate(str(file_path), pagesize=letter)
            styles = getSampleStyleSheet()

            # Настройка стилей с обработкой ошибок
            try:
                styles["Normal"].fontName = "DejaVuSans"
                styles["Title"].fontName = "DejaVuSans"
            except:
                logger.warning(
                    "Не удалось установить шрифт для стилей, используем стандартный")

            # Обновляем существующий стиль вместо добавления с тем же именем
            if "Heading2" in styles.byName:
                styles["Heading2"].fontName = "DejaVuSans"
            else:
                styles.add(
                    ParagraphStyle(
                        name="Heading2", parent=styles["Normal"],
                        fontName="DejaVuSans"
                    )
                )

            story = []

            # Добавляем заголовок
            title = LogMessages.PDF_REPORT_TITLE.format(chat_name=chat_name)
            story.append(Paragraph(title, styles["Title"]))

            # Ссылка на граф (если есть)
            if graph_file and Path(graph_file).exists():
                story.append(Paragraph(
                    f"<a href='{graph_file}'>Открыть интерактивный граф</a>",
                    styles["Normal"]
                ))

            if not metrics_data:
                story.append(
                    Paragraph("Нет данных для отчета", styles["Normal"]))
                logger.warning("Метрики данных пусты")
            else:
                # Универсальная функция для добавления секций
                def add_section(section_title: str, data: Any,
                                formatter: Callable = None):
                    """Добавляет секцию в отчет"""

                    if data is None or (
                            isinstance(data, (list, dict)) and not data):
                        logger.debug(f"Нет данных для секции:{section_title}")
                        return

                    story.append(Paragraph(section_title, styles["Heading2"]))

                    if formatter:
                        # Используем кастомный форматтер
                        formatted_content = formatter(data)
                        if isinstance(formatted_content, list):
                            for item in formatted_content:
                                story.append(Paragraph(item, styles["Normal"]))
                        else:
                            story.append(
                                Paragraph(formatted_content, styles["Normal"]))
                    elif isinstance(data, dict):
                        # Для словарей выводим ключ-значение
                        for key, value in data.items():
                            story.append(Paragraph(f"• {key}: {value}",
                                                   styles["Normal"]))
                    elif isinstance(data, list):
                        # Для списков выводим элементы
                        for item in data:
                            if isinstance(item, dict):
                                # Обрабатываем топ пользователей
                                username = item.get('username',
                                                    item.get('user_id',
                                                             'Unknown'))
                                value = item.get('value', '')
                                story.append(
                                    Paragraph(f"• {username}: {value}",
                                              styles["Normal"]))
                            else:
                                story.append(
                                    Paragraph(f"• {item}", styles["Normal"]))
                    else:
                        # Простые значения
                        story.append(Paragraph(str(data), styles["Normal"]))

                # 1. Сводка
                summary = metrics_data.get(AnalysisAttributes.SUMMARY.value,
                                           {})
                if summary:
                    add_section("Сводка", summary)

                # 2. Автоматически добавляем все основные метрики
                section_config = [
                    ('Топ активных пользователей',
                     AnalysisAttributes.TOP_ACTIVE_USERS.value),
                    ('Топ популярных пользователей',
                     AnalysisAttributes.TOP_POPULAR_USERS.value),
                    ('Топ вовлеченных пользователей',
                     AnalysisAttributes.TOP_ENGAGED_USERS.value),
                    ('Топ отвечающих', AnalysisAttributes.TOP_REPLIERS.value),
                    ('Топ получателей ответов',
                     AnalysisAttributes.TOP_REPLIED_TO.value),
                    ('Топ задающих вопросы',
                     AnalysisAttributes.TOP_QUESTION_ASKERS.value),
                    ('Degree Centrality',
                     AnalysisAttributes.DEGREE_CENTRALITY.value),
                    ('Betweenness Centrality',
                     AnalysisAttributes.BETWEENNESS_CENTRALITY.value),
                    ('Closeness Centrality',
                     AnalysisAttributes.CLOSENESS_CENTRALITY.value),
                    ('Eigenvector Centrality',
                     AnalysisAttributes.EIGENVECTOR_CENTRALITY.value)
                ]

                for title, key in section_config:
                    data = metrics_data.get(key)
                    if data:
                        add_section(title, data)

                # 3. Дополнительные метрики
                add_section("Статистика ответов",
                            metrics_data.get(
                                AnalysisAttributes.TOTAL_REPLIES.value))
                add_section("Всего вопросов",
                            metrics_data.get(
                                AnalysisAttributes.TOTAL_QUESTIONS.value))

                # 4. Свойства сети
                network_props = metrics_data.get('network_properties', {})
                if network_props:
                    add_section("Свойства сети", network_props)

            # Создаем PDF
            try:
                doc.build(story)
                if file_path.exists():
                    logger.info(LogMessages.INFO_PDF_REPORT_SAVED.format(
                        file_path=file_path))

            except Exception as build_error:
                logger.error(f"Ошибка при создании PDF: {build_error}")
                # Fallback: простой отчет
                try:
                    simple_doc = SimpleDocTemplate(str(file_path),
                                                   pagesize=letter)
                    simple_doc.build(
                        [Paragraph("Упрощенный отчет", styles["Normal"])])
                    return file_path
                except:
                    logger.error("Не удалось создать даже упрощенный PDF")
                    return None


        except Exception as e:
            logger.error(f"Критическая ошибка в create_pdf_report: {e}")
            return None

    def send_pdf_report_via_email(
            self,
            pdf_path: Path,
            to_email: str,
            subject: str = "Chat Analysis Report",
            body: str = "Отчет во вложении.",
            smtp_host: str | None = None,
            smtp_port: int | None = None,
            smtp_user: str | None = None,
            smtp_password: str | None = None,
            use_tls: bool = True,
    ) -> bool:
        """
        Отправляет PDF-отчет на указанный email, используя библиотеку email и smtplib.
        SMTP-параметры можно передать явно или через переменные окружения.
        """
        try:
            Mistaken.validate_all(pdf_path, Path, param_name="pdf_path")
            Mistaken.validate_all(to_email, str, param_name="to_email")
            if not pdf_path.exists():
                logger.error(
                    LogMessages.WARNING_FILE_NOT_FOUND.format(
                        file_path=pdf_path)
                )
                return False

            smtp_host = smtp_host or os.getenv("SMTP_HOST")
            smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
            smtp_user = smtp_user or os.getenv("SMTP_USER")
            smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")

            Mistaken.validate_all(smtp_host, str, param_name="SMTP_HOST")

            msg = EmailMessage()
            msg["From"] = smtp_user if smtp_user else "no-reply@example.com"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(body)

            with open(pdf_path, "rb") as f:
                data = f.read()
            msg.add_attachment(
                data,
                maintype="application",
                subtype="pdf",
                filename=pdf_path.name,
            )

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(LogMessages.ERROR_PDF_REPORT_CREATION.format(error=e))
            return False


# _____________________________________________________________________________


class GraphCreator:
    """Создает граф из сырых данных чата"""

    def __init__(self):
        self.graph = Graph()
        self.message_to_user = {}
        self.username_to_user = {}
        self.edge_weights = {}  # Для хранения весов ребер (from-to -> count)

    def _calculate_edge_weights(self):
        """Рассчитывает веса ребер на основе количества взаимодействий"""
        for edge in self.graph.edges.values():
            key = (edge.from_user.user_id, edge.to_user.user_id,
                   edge.edge_type)
            self.edge_weights[key] = self.edge_weights.get(key, 0) + 1

    def _get_normalized_edge_width(self, count: int, max_count: int) -> float:
        """Нормализует толщину ребра"""
        if max_count == 0:
            return GraphVisualizationSettings.MIN_EDGE_WIDTH

        normalized = (count / max_count) * (
                GraphVisualizationSettings.MAX_EDGE_WIDTH -
                GraphVisualizationSettings.MIN_EDGE_WIDTH
        ) + GraphVisualizationSettings.MIN_EDGE_WIDTH

        return normalized

    def _get_edge_color_by_quantile(self, count: int, counts: list) -> str:
        """Возвращает цвет ребра на основе квантиля"""
        if not counts:
            return GraphVisualizationSettings.EDGE_COLORS[0]

        sorted_counts = sorted(counts)
        quantile = sorted_counts.index(count) / len(sorted_counts)

        if quantile < 0.33:
            return GraphVisualizationSettings.EDGE_COLORS[0]  # green
        elif quantile < 0.66:
            return GraphVisualizationSettings.EDGE_COLORS[1]  # yellow
        else:
            return GraphVisualizationSettings.EDGE_COLORS[2]  # red

    def _calculate_node_sizes(self):
        """Рассчитывает размеры узлов на основе исходящих связей"""
        out_degree = {}
        for edge_key in self.edge_weights:
            from_user, to_user, edge_type = edge_key
            out_degree[from_user] = out_degree.get(from_user, 0) + \
                                    self.edge_weights[edge_key]

        max_out_degree = max(out_degree.values()) if out_degree else 1

        for user_id, knot in self.graph.users.items():
            degree = out_degree.get(user_id, 0)
            normalized_size = (
                    GraphVisualizationSettings.MIN_NODE_SIZE +
                    (degree / max_out_degree) * (
                            GraphVisualizationSettings.MAX_NODE_SIZE -
                            GraphVisualizationSettings.MIN_NODE_SIZE
                    )
            )
            knot.size = normalized_size

    def visualize_and_save_file(
            self,
            graph: Graph,
            directory_path: Path,
            base_name: str,
            type_file: str,
            extension: str,
            graph_date: str
    ) -> Path:

        """Визуализация графа с улучшенными настройками"""
        self.graph = graph
        self._calculate_edge_weights()
        self._calculate_node_sizes()

        # Подготовка сети
        net = Network(
            height=GraphVisualizationSettings.NETWORK_HEIGHT,
            width=GraphVisualizationSettings.NETWORK_WIDTH,
            bgcolor=GraphVisualizationSettings.NETWORK_BG_COLOR,
            font_color=GraphVisualizationSettings.NETWORK_FONT_COLOR,
            directed=GraphVisualizationSettings.NETWORK_DIRECTED,
            notebook=GraphVisualizationSettings.NETWORK_NOTEBOOK,
        )

        # ВСЕ НАСТРОЙКИ В ОДНОМ JSON
        all_options = {
        "physics": {
            "enabled": GraphVisualizationSettings.PHYSICS_ENABLED,
            "stabilization": {"iterations": 500},
            "barnesHut": {
                "gravitationalConstant": -GraphVisualizationSettings.REPULSION,
                "centralGravity": GraphVisualizationSettings.CENTRAL_GRAVITY,
                "springLength": GraphVisualizationSettings.SPRING_LENGTH,
                "springConstant": GraphVisualizationSettings.SPRING_CONSTANT,
                "damping": GraphVisualizationSettings.DAMPING,
                "avoidOverlap": GraphVisualizationSettings.AVOID_OVERLAP
            },
            "minVelocity": 0.75,
            "solver": "barnesHut" if GraphVisualizationSettings.BARNES_HUT_OPTIMIZE else "repulsion"
        },
        "edges": {
            "smooth": {
                "enabled": GraphVisualizationSettings.PHYSICS_ENABLED,
                "type": GraphVisualizationSettings.EDGE_SMOOTH_TYPE,
                "roundness": 0.5,
                "forceDirection": "vertical"
            },
            "arrows": {
                "to": {
                    "enabled": GraphVisualizationSettings.PHYSICS_ENABLED,
                    "scaleFactor": 1.3
                }
            }
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 200
            }
        }

        # ПЕРЕДАЕМ ВСЕ НАСТРОЙКИ ОДНИМ ВЫЗОВОМ
        net.set_options(json.dumps(all_options))

        # Добавляем узлы
        for user_id, knot in self.graph.users.items():
            is_anon = str(user_id).startswith("anon_") or user_id < 0
            color = (
                GraphVisualizationSettings.ANONYMOUS_USER_COLOR
                if is_anon
                else GraphVisualizationSettings.REGULAR_USER_COLOR
            )
            shape = (
                GraphVisualizationSettings.ANONYMOUS_USER_SHAPE
                if is_anon
                else GraphVisualizationSettings.REGULAR_USER_SHAPE
            )

            net.add_node(
                user_id,
                label=knot.username,
                color=color,
                shape=shape,
                size=knot.size,
                title=f"ID: {user_id}\nName: {knot.username}\nOutgoing: {sum(1 for e in graph.edges.values() if e.from_user.user_id == user_id)}",
            )

        # Собираем статистику для цветов ребер
        edge_counts = list(self.edge_weights.values())
        max_edge_count = max(edge_counts) if edge_counts else 1

        # Добавляем рёбра
        added_edges = set()
        for edge_key, count in self.edge_weights.items():
            from_user, to_user, edge_type = edge_key

            if (from_user, to_user) in added_edges:
                continue

            added_edges.add((from_user, to_user))

            color = self._get_edge_color_by_quantile(count, edge_counts)
            width = self._get_normalized_edge_width(count, max_edge_count)

            net.add_edge(
                from_user,
                to_user,
                color=color,
                width=width,
                title=f"Messages: {count}",
                arrows=GraphVisualizationSettings.ARROWS_DIRECTION,
                length=GraphVisualizationSettings.SPRING_LENGTH,
                smooth={"enabled": True, "type": "continuous"}
            )

        # Сохранение файла
        directory_path.mkdir(parents=True, exist_ok=True)

        filename = FileTemplates.GRAPH_VISUALIZATION.format(
            base_name=base_name,
            type_file=type_file,
            graph_date=graph_date,
            extension=extension,
        )
        file_path = directory_path / filename

        net.write_html(str(file_path))
        return file_path

    def process_data(self, messages: list) -> Graph:
        """Основной метод обработки данных"""
        for msg in messages:
            user_id = msg.get(MessageKeys.USER_ID)
            username = msg.get(MessageKeys.AUTHOR_NAME,
                               MessageKeys.UNKNOWN_AUTHOR)
            message_id = msg.get(MessageKeys.MESSAGE_ID)

            # Для анонимных пользователей генерируем отрицательный ID
            if user_id is None:
                user_id = -abs(message_id)  # Отрицательный ID

            # Создаем пользователя если его нет
            if user_id not in self.graph.users:
                if user_id < 0:  # Анонимный пользователь
                    user_name = f"Anonymous_{abs(user_id)}"  # Без знака минус
                else:
                    user_name = username

                user = self.graph.add_user(user_id, user_name)
                self.username_to_user[user_name.lower()] = user

            # Запоминаем связь сообщение -> пользователь
            self.message_to_user[message_id] = user_id
            self.process_message(msg)

        return self.graph

    def process_message(self, msg: dict) -> None:
        """Обрабатывает одно сообщение и его связи"""
        sender_id = self.get_or_create_sender(msg)

        # Обрабатываем reply_to связь
        if msg[MessageKeys.REPLY_TO_ID] is not None:
            self.process_reply(sender_id, msg)

        # Обрабатываем mentions (@username)
        self.process_mentions(sender_id, msg[MessageKeys.MESSAGE_TEXT])

        # Обрабатываем реакции, если есть
        self.process_reactions(sender_id, msg)

    def get_or_create_sender(self, msg: dict) -> int:
        """Возвращает или создаёт отправителя сообщения (user_id)"""
        user_id = msg.get(MessageKeys.USER_ID)
        username = msg.get(MessageKeys.AUTHOR_NAME) or "Anonymous"
        message_id = msg.get(MessageKeys.MESSAGE_ID)

        # Отладочная информация (удалите или замените логированием в продакшне)
        print(f"Message keys: {list(msg.keys())}")
        print(f"User ID: {user_id}, Username: {username}")
        if msg.get("chat") is not None:
            print(f"Chat data: {msg.get('chat')}")
        if msg.get("from") is not None:
            print(f"From data: {msg.get('from')}")

        # Если user_id отсутствует, но есть объект чата — используем данные чата
        if user_id is None and (
                ChatObjectAttributes.ID in msg or msg.get("chat") is not None
        ):
            # пытаемся получить id и название чата из разных полей
            chat_field = msg.get("chat") or {}
            user_id = (
                    msg.get(ChatObjectAttributes.ID)
                    or chat_field.get(ChatObjectAttributes.ID)
                    or None
            )
            username = (
                    msg.get(ChatObjectAttributes.TITLE)
                    or msg.get(ChatObjectAttributes.NAME)
                    or chat_field.get(ChatObjectAttributes.TITLE)
                    or chat_field.get(ChatObjectAttributes.NAME)
                    or username
            )
            print(f"Using chat as sender: ID={user_id}, Name={username}")

        # Если user_id всё ещё отсутствует — создаём анонимного пользователя с отрицательным уникальным ID
        if user_id is None:
            # безопасно получить целочисленный base для генерации отрицательного id
            try:
                anon_base = (
                    abs(int(message_id)) if message_id is not None else abs(
                        id(msg))
                )
            except (TypeError, ValueError):
                anon_base = abs(id(msg))
            user_id = -anon_base
            print(f"Creating anonymous user: ID={user_id}")

            if user_id not in self.graph.users:
                user = self.graph.add_user(user_id, f"Anonymous_{anon_base}")
                # сохраняем сопоставление по нормализованному имени
                self.username_to_user[username.lower()] = user
            return user_id

        # Приводим к целому типу и нормализуем username
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            # В редком случае некорректного user_id — fallback в анонимного
            try:
                anon_base = (
                    abs(int(message_id)) if message_id is not None else abs(
                        id(msg))
                )
            except (TypeError, ValueError):
                anon_base = abs(id(msg))
            user_id = -anon_base
            print(f"Invalid user_id, fallback to anonymous: ID={user_id}")

            if user_id not in self.graph.users:
                user = self.graph.add_user(user_id, f"Anonymous_{anon_base}")
                self.username_to_user[username.lower()] = user
            return user_id

        # Гарантируем, что username непустой строкой
        username = username or f"user_{user_id}"

        # Добавляем пользователя в граф при отсутствии и сохраняем сопоставление по имени
        if user_id not in self.graph.users:
            user = self.graph.add_user(user_id, username)
            self.username_to_user[username.lower()] = user

        return user_id

    def process_reply(self, sender_id: int, msg: dict) -> None:
        """Обрабатывает ответ на сообщение"""
        reply_to_msg_id = msg.get(MessageKeys.REPLY_TO_ID)
        if reply_to_msg_id and reply_to_msg_id in self.message_to_user:
            receiver_id = self.message_to_user[reply_to_msg_id]
            if receiver_id is not None:
                self.graph.add_interaction(
                    edge_type=EdgeType.REPLY,
                    from_user_id=sender_id,  # int
                    to_user_id=receiver_id,  # int
                    content=msg.get(MessageKeys.MESSAGE_TEXT, ""),
                )

    def process_mentions(self, sender_id: int, message_text: str) -> None:
        """Обрабатывает упоминания в тексте"""
        for mention in self.extract_mentions(message_text):
            mentioned_user = self.username_to_user.get(mention.lower())
            if mentioned_user:
                self.graph.add_interaction(
                    edge_type=EdgeType.MENTION,
                    from_user_id=sender_id,  # int
                    to_user_id=mentioned_user.user_id,  # int
                    content=f"@{mention}",
                )

    def process_reactions(self, sender_id: int, msg: dict) -> None:
        """Добавляет связи реакций (реагирующий -> автор сообщения)"""
        reactions = msg.get(MessageKeys.REACTIONS)
        if not reactions:
            return
        author_id = sender_id
        for reactor_name in reactions:
            # Ищем пользователя по username
            mentioned_user = self.username_to_user.get(
                str(reactor_name).lower())
            if mentioned_user:
                self.graph.add_interaction(
                    edge_type=EdgeType.REACTION,
                    from_user_id=mentioned_user.user_id,
                    to_user_id=author_id,
                    content=str(reactor_name),
                )

    @staticmethod
    def extract_mentions(text: str) -> list:
        """Извлекает упоминания из текста"""
        import re

        return [m.lower() for m in re.findall(r"@(\w+)", text)]
