# unload_chat.py
import asyncio
import argparse
from pathlib import Path
from loguru import logger
from scr.config import (
    SOCIAL_NETWORK_DICT,
    LOG_ROTATION_SIZE,
    TELEGRAM_KEY,
    STORAGE_DIR,
    LogMessages,
    FileTemplates,
    CommandLineArgument
)

from scr.models import User, TelegramAccount, TelegramChat, Mistaken
from scr.manager import FileManager
import sys


async def configure_logger() -> bool:
    """Настройка логгера.

    Return:
        bool: True если настройка выполнена успешно, False иначе.
    """
    try:
        # Добавляем файл-логгер с ротацией
        logger.add(FileTemplates.UNLOAD_OF_CHATS_BASE_NAME_LOG, rotation=LOG_ROTATION_SIZE)
        logger.info(LogMessages.INFO_LOGGER_SUCCESS)
        return True
    except Exception as exc:
        # Можно залогировать ошибку локально, но не поднимать исключение наружу
        # чтобы не ломать асинхронный контекст вызова
        return False

async def unload_chat_data(
    user_system_name: str,
    api_id: int,
    api_hash: str,
    social_account_name: str,
    chat_name: str,
    phone_number: str,
    output_dir: str = None,
):
    """
    Uploads data from the specified chat
    """

    logger.info(LogMessages.INFO_DATA_START.format(chat_name=chat_name))

    # Создаем пользователя
    user = User(name=user_system_name, phone_numbers=[])

    # Базовая директория для хранения
    base_storage_dir = Path(output_dir) if output_dir else\
        Path.cwd() / STORAGE_DIR

    file_manager = FileManager(base_storage_dir=base_storage_dir)

    # Создаем папку для пользователя
    user_dir_path = file_manager.create_object_dir(
        obj_dir_name=user.name,
        parent_dir=file_manager.base_storage_dir
    )

    user.storage_path = user_dir_path

    if social_account_name == SOCIAL_NETWORK_DICT.get(TELEGRAM_KEY):
        # Инициализация Telegram аккаунта
        telegram_account = TelegramAccount(
            user=user,
            phone_number=phone_number,
            api_id=api_id,
            api_hash=api_hash
        )

    else:
        logger.warning(LogMessages.WARNING_NOT_ACCESS_SOCIAL_NETWORK)

        return None

    # Если номера не было, то добавляем пользователю
    if phone_number not in user.get_social_accounts():
        user.add_phone_number(phone_number)

    try:
        # Подключаемся к Telegram
        await telegram_account.client.start(phone=telegram_account.phone_number)

        # Получаем список чатов
        all_chats = await telegram_account.get_chats()

        # Ищем нужный чат
        if chat_name in all_chats:
            chat_id = all_chats[chat_name]
            logger.info(
                LogMessages.INFO_CHAT_FOUND.format(chat_name=chat_name,
                                                   chat_id=chat_id)
            )
        else:
            logger.warning(
                LogMessages.WARNING_CHAT_NOT_FOUND.format(
                    chat_name=chat_name,
                    available_chats=list(all_chats.keys())
                )
            )
            return None

        # Создаем объект чата и инициализируем
        chat = TelegramChat(
            name=chat_name,
            chat_id=chat_id,
            social_account=telegram_account
        )
        await chat.initialize()

        # Создаем директорию для чата
        chat.storage_path = file_manager.create_object_dir(
            obj_dir_name=chat.name,
            parent_dir=telegram_account.storage_path
        )

        # Получаем и сохраняем сообщения
        messages = await chat.get_messages()
        file_path = file_manager.save_chat_json(chat=chat,
                                                data=messages)
        logger.info(LogMessages.INFO_DATA_SAVED.format(file_path=file_path))

        return file_path

    except Exception as e:
        logger.exception(LogMessages.ERROR_DATA_UNLOADING.format(e))
        return None
    finally:
        await telegram_account.client.disconnect()


def main():

    parser = argparse.ArgumentParser(
        description=LogMessages.HELP_TELEGRAM_INFO_UNLOADING_DATA,
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    CLIArg = CommandLineArgument()
    # Конфигурация аргументов для парсера
    required_arguments = [
        (CLIArg.USER_SYSTEM_NAME,
         LogMessages.HELP_TELEGRAM_USER_SYSTEM_NAME),
        (CLIArg.API_HASH, LogMessages.HELP_TELEGRAM_API_HASH),
        (CLIArg.API_ID, LogMessages.HELP_TELEGRAM_API_ID),
        (CLIArg.SOCIAL_ACCOUNT_NAME,
         LogMessages.HELP_TELEGRAM_SOCIAL_ACCOUNT_NAME),
        (CLIArg.CHAT_NAME, LogMessages.HELP_TELEGRAM_CHAT_NAME),
        (CLIArg.PHONE, LogMessages.HELP_TELEGRAM_PHONE),
    ]

    optional_arguments = [
        (CLIArg.OUTPUT, LogMessages.HELP_TELEGRAM_OUTPUT),
    ]

    # Добавляем аргументы в парсер
    for argument, help_text in required_arguments:
        parser.add_argument(argument, type=str, required=True, help=help_text)

    for argument, help_text in optional_arguments:
        parser.add_argument(argument, type=str, required=False, help=help_text)

    args = parser.parse_args()

    # Запускаем выгрузку
    result = asyncio.run(
        unload_chat_data(
            user_system_name=args.user_system_name,
            api_id=int(args.api_id),
            api_hash=args.api_hash,
            social_account_name=args.social_account_name,
            chat_name=args.chat_name,
            phone_number=args.phone,
            output_dir=args.output
        )
    )

    if result:
        return result
    else:
        return None


if __name__ == "__main__":
    if configure_logger():
        main()
