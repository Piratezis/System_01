# analysis_chat.py
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
from datetime import datetime
from scr.manager import GraphCreator, ChatAnalyzer, FileManager, TimeManager
from scr.config import (
    LogMessages,
    LOG_ROTATION_SIZE,
    FileTemplates,
    STORAGE_DIR,
    SOCIAL_NETWORK_DICT,
    TELEGRAM_KEY,
    DateFormat,
    Extensions,
    PythonSettings,
    CommandLineArgument,
    ReportPDFSettings
)
from scr.enums import AnalysisAttributes, CommandSystemArgument
from scr.models import Mistaken

# Настройка логгера
logger.add(FileTemplates.ANALYZE_CHAT_BASE_NAME_LOG,
           rotation=LOG_ROTATION_SIZE)


def analyze_chat_data(
        data_file: str,
        output_dir: Optional[str],
        chat_name: Optional[str] = None,
        phone_number: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Performs chat analysis based on a JSON file and saves the results.

    Args:
        data_file: path to JSON with chat messages
        output_dir: folder to save; if None, use the chat folder.

    Returns:
        dict with paths to results or None in case of error
    """
    # Валидация входных данных через Mistaken
    Mistaken.validate_all(data_file, str, param_name="data_file")
    if output_dir is not None:
        Mistaken.validate_all(output_dir, str, param_name="output_dir")
    logger.info(LogMessages.INFO_ANALYSIS_START.format(data_file=data_file))

    file_manager = FileManager(base_storage_dir=Path.cwd())

    # Загружаем данные
    data = file_manager.load_chat_json(Path(data_file))
    if not data:
        logger.error(LogMessages.ERROR_DATA_LOADING)
        return None

    logger.info(LogMessages.INFO_MESSAGES_LOADED.format(count=len(data)))

    # Создаем граф
    creator = GraphCreator()
    graph = creator.process_data(data)

    # Анализируем
    analyzer = ChatAnalyzer(graph)

    # Получаем все метрики анализа
    metrics = analyzer.get_comprehensive_metrics()

    base_name = Path(data_file).stem

    # Определяем базовую директорию результатов: папка чата Analysis
    base_output_dir = Path(output_dir) if output_dir else Path(
        data_file).parent

    analysis_dir_path = file_manager.create_object_dir(
        obj_dir_name=FileTemplates.ANALYZE_CHAT_BASE_NAME,
        parent_dir=base_output_dir
    )

    # Создаем директорию Анализа, если не существует
    analysis_dir_path.mkdir(parents=True, exist_ok=True)

    # Сохраняем метрики через FileManager
    metrics_file = file_manager.save_metrics_to_directory(
        analyzer=analyzer,
        base_name=base_name,
        directory_path = analysis_dir_path,
        type_file=FileTemplates.METRICS_ADDITIONAL_NAME,
        extension=Extensions.CHAT_FILE_EXTENSION,
        metrics_date=TimeManager.now_formatted()
    )
    logger.info(
        LogMessages.INFO_ANALYSIS_RESULTS_SAVED.format(file_path=metrics_file))

    visualization_path = creator.visualize_and_save_file(
        graph=graph,
        directory_path=analysis_dir_path,
        base_name=base_name,
        type_file=FileTemplates.GRAPH_ADDITIONAL_NAME,
        extension=Extensions.HTML_FILE_EXTENSION,
        graph_date=TimeManager.now_formatted()
    )

    # Пытаемся определить chat_name и phone_number, если не переданы
    if not chat_name or not phone_number:
        try:
            # Ожидаем структуру: .../<user>/<social>/<phone>/<chat>/<date>/<file.json>
            p = Path(data_file)
            chat_dir = p.parent.parent  # поднимаемся на дату и чат
            chat_name = chat_dir.name
        except Exception:
            pass

    # Создаем PDF отчет в папке анализа с сылкой на граф
    pdf_path = None
    try:
        pdf_path = FileManager(base_storage_dir=Path.cwd()).create_pdf_report(
            metrics_data=metrics,
            chat_name=chat_name,
            report_date=TimeManager.now_formatted(),
            analysis_dir=analysis_dir_path,
            graph_file=str(visualization_path),
            base_name=base_name,
            type_file=FileTemplates.REPORT_ADDITIONAL_NAME,
            extension=Extensions.PDF_FILE_EXTENSION,
        )
    except Exception:
        logger.error(LogMessages.ERROR_PDF_REPORT_CREATION)

    return {
        AnalysisAttributes.METRICS_FILE: metrics_file,
        AnalysisAttributes.VISUALIZATION_FILE: visualization_path,
        AnalysisAttributes.ANALYSIS_DIR: analysis_dir_path,
        AnalysisAttributes.ANALYSIS_REPORT: pdf_path,
    }


def _resolve_data_file(
        file: Optional[str],
        user_system_name: Optional[str],
        social_account_name: Optional[str],
        phone: Optional[str],
        chat_name: Optional[str],
        output: Optional[str],
        date_str: Optional[str],
) -> Optional[Path]:
    """Определяет путь к последнему JSON с данными чата."""

    if file:
        p = Path(file)
        return p if p.exists() else None

    social_name = social_account_name or SOCIAL_NETWORK_DICT.get(TELEGRAM_KEY)

    # Валидация параметров
    for name, value in {
        CommandSystemArgument.USER_SYSTEM_NAME: user_system_name,
        CommandSystemArgument.SOCIAL_ACCOUNT_NAME: social_name,
        CommandSystemArgument.PHONE: phone,
        CommandSystemArgument.CHAT_NAME: chat_name,
    }.items():
        Mistaken.validate_all(value, str, param_name=name)

    base_dir = Path(output) if output else STORAGE_DIR
    chat_dir = (
            base_dir / user_system_name / social_name / phone.replace("+",
                                                                      "") / chat_name
    )
    if not chat_dir.exists():
        logger.error(
            LogMessages.WARNING_FILE_NOT_FOUND.format(file_path=chat_dir))
        return None

    # Подготовим список датовых папок YYYY-MM-DD
    dated_dirs: List[Path] = [d for d in chat_dir.iterdir() if d.is_dir()]

    # Отфильтруем, оставив только корректные даты
    def parse_date_dir(path: Path):
        try:
            return datetime.strptime(path.name, DateFormat.DATE_FORMAT)
        except Exception:
            return None

    dated_with_dt = [(d, parse_date_dir(d)) for d in dated_dirs]
    dated_with_dt = [(d, dt) for d, dt in dated_with_dt if dt is not None]

    target_dt = None
    if date_str:
        Mistaken.validate_all(date_str, str, param_name="date")
        try:
            target_dt = datetime.strptime(date_str, DateFormat.DATE_FORMAT)
        except ValueError:
            logger.error(
                LogMessages.ERROR_ANALYSIS_WRONG_DATE_FORMAT.format(
                    date=date_str)
            )
            return None

    # Сортировка по дате убыв.
    dated_with_dt.sort(key=lambda x: x[1], reverse=True)

    # Если задана дата — берём папки строго ДО неё (dt < target_dt). Иначе — самую позднюю
    candidates = []
    for d, dt in dated_with_dt:
        if target_dt is None or dt < target_dt:
            candidates.append(d)

    if target_dt is not None and not candidates:
        logger.error(LogMessages.ERROR_ANALYSIS_NO_DATA)
        return None

    for d in candidates:
        # берём самый новый по времени файл в папке даты
        json_files = sorted(
            d.glob("*" + Extensions.JSON_EXTENSION),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if json_files:
            return json_files[0]

    return None


def main():
    """CLI вход для анализа чата. Поддерживает два сценария запуска:

    1) Через прямой путь к файлу: --file <path_to_json>
    2) Через параметры чата (как в выгрузке): --user_system_name --social_account_name --chat_name --phone [--output]
    """
    parser = argparse.ArgumentParser(
        description=LogMessages.HELP_ANALYSIS_DESCRIPTION)

    # Обязательные аргументы
    CLIArg = CommandLineArgument()
    required_arguments = [

        (CLIArg.USER_SYSTEM_NAME_ANALYSIS,
         LogMessages.HELP_TELEGRAM_USER_SYSTEM_NAME),

        (CLIArg.SOCIAL_ACCOUNT_NAME_ANALYSIS,
         LogMessages.HELP_TELEGRAM_SOCIAL_ACCOUNT_NAME),

        (CLIArg.CHAT_NAME_ANALYSIS,
         LogMessages.HELP_TELEGRAM_CHAT_NAME),

        (CLIArg.PHONE_ANALYSIS,
         LogMessages.HELP_TELEGRAM_PHONE)
    ]

    # Опциональные аргументы
    optional_arguments = [
        (CLIArg.FILE,
         LogMessages.HELP_ANALYSIS_FILE),

        (CLIArg.OUTPUT_ANALYSIS,
         LogMessages.HELP_ANALYSIS_OUTPUT),

        (CLIArg.DATE,
         LogMessages.HELP_ANALYSIS_DATE)
    ]

    # Добавляем аргументы в парсер
    for argument, help_text in required_arguments:
        parser.add_argument(argument, type=str, required=True, help=help_text)

    for argument, help_text in optional_arguments:
        parser.add_argument(argument, type=str, required=False, help=help_text)

    args = parser.parse_args()

    data_file_path = _resolve_data_file(
        file=args.file,
        user_system_name=args.user_system_name,
        social_account_name=args.social_account_name,
        phone=args.phone,
        chat_name=args.chat_name,
        output=args.output,
        date_str=args.date
    )

    if not data_file_path or not data_file_path.exists():
        logger.error(f"Файл не найден: {args.file or 'по параметрам чата'}")
        return None

    # Запускаем анализ
    result = analyze_chat_data(
        str(data_file_path),
        args.output,
        chat_name=args.chat_name,
        phone_number=args.phone

    )

    if result:
        logger.info("=" * 60)
        logger.info(LogMessages.ANALYSIS_CLI_HEADER)
        logger.info("=" * 60)
        logger.info(
            LogMessages.INFO_ANALYSIS_DIR.format(
                path=result[AnalysisAttributes.ANALYSIS_DIR]
            )
        )
        logger.info(
            LogMessages.INFO_METRICS_FILE_PATH.format(
                file_path=result[AnalysisAttributes.METRICS_FILE]
            )
        )
        logger.info(
            LogMessages.INFO_VISUALIZATION_FILE_PATH.format(
                file_path=result[AnalysisAttributes.VISUALIZATION_FILE]
            )
        )

        # Загружаем метрики для отображения
        with open(
                result[AnalysisAttributes.METRICS_FILE],
                PythonSettings.FILE_READ_MODE,
                encoding=PythonSettings.ENCODING_UTF8,
        ) as f:
            metrics = json.load(f)

        logger.info(LogMessages.INFO_METRICS_HEADER)
        logger.info(
            LogMessages.INFO_SUMMARY_USERS.format(
                value=metrics[AnalysisAttributes.SUMMARY][
                    AnalysisAttributes.TOTAL_USERS
                ]
            )
        )
        logger.info(
            LogMessages.INFO_SUMMARY_INTERACTIONS.format(
                value=metrics[AnalysisAttributes.SUMMARY][
                    AnalysisAttributes.TOTAL_INTERACTIONS
                ]
            )
        )
        logger.info(
            LogMessages.INFO_SUMMARY_MESSAGES.format(
                value=metrics[AnalysisAttributes.SUMMARY][
                    AnalysisAttributes.TOTAL_MESSAGES
                ]
            )
        )

        # Самые активные пользователи
        logger.info(LogMessages.INFO_TOP_ACTIVE_HEADER.format(top_len=ReportPDFSettings.TOP_LEN))
        for user in metrics.get(AnalysisAttributes.TOP_ACTIVE_USERS.value, [])[:ReportPDFSettings.TOP_LEN]:
            logger.info(
                LogMessages.INFO_TOP_ACTIVE_LINE.format(
                    username=user[AnalysisAttributes.USERNAME],
                    value=user[AnalysisAttributes.VALUE],
                )
            )

    else:
        logger.error(LogMessages.ERROR_DATA_LOADING)

    return result


if __name__ == "__main__":
    main()
