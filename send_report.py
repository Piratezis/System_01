import argparse
from pathlib import Path
from loguru import logger
from scr.manager import FileManager
from scr.config import LogMessages, LOG_ROTATION_SIZE, CommandLineArgument

logger.add("send_report.log", rotation=LOG_ROTATION_SIZE)


def main():
    parser = argparse.ArgumentParser(
        description="Отправка PDF-отчета на почту",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )

    parser.add_argument(
        CommandLineArgument.PDF, type=str, required=True, help="Путь к PDF отчету"
    )
    parser.add_argument(
        CommandLineArgument.TO, type=str, required=True, help="Email получателя"
    )
    parser.add_argument(
        CommandLineArgument.SUBJECT, type=str, default="Chat Analysis Report"
    )
    parser.add_argument(
        CommandLineArgument.BODY, type=str, default="Отчет во вложении."
    )
    args = parser.parse_args()

    file_manager = FileManager(base_storage_dir=Path.cwd())
    ok = file_manager.send_pdf_report_via_email(
        pdf_path=Path(args.pdf),
        to_email=args.to,
        subject=args.subject,
        body=args.body,
    )
    if ok:
        logger.info("Отчет отправлен.")
    else:
        logger.info("Не удалось отправить отчет.")


if __name__ == "__main__":
    main()
