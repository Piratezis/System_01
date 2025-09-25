import pathlib
import typing
from abc import ABC, abstractmethod
from telethon import TelegramClient
from telethon.tl.types import PeerChannel, Channel, User as TelethonUser
from loguru import logger
from scr.config import (
    LogMessages,
    PythonSettings,
    LogMessagesMistaken,
    SOCIAL_NETWORK_DICT,
    TELEGRAM_KEY,
    FileTemplates,
    SystemConfig,
)
from scr.enums import (
    EdgeType,
    ChatObjectAttributes,
    TelegramEntityAttributes,
    MessageKeys,
)


# # ______________________________________________________________________


class SocialAccount(ABC):
    def __init__(self, name: str, phone_number: str):
        self.name = name
        self.phone_number = phone_number
        self.session_path: pathlib.Path | None = None
        self.storage_path: pathlib.Path | None = None

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def get_chats(self):
        pass

    @abstractmethod
    async def add_chat(self, chat_url: str):
        pass


class Chat(ABC):
    """
    Абстрактный базовый класс для всех типов чатов социальных сетей.
    Содержит общие поля и абстрактные методы для взаимодействия с чатами.
    """

    def __init__(
        self,
        chat_id: int | str,
        # Уникальный ID чата (числовой или строковый)
        social_account: SocialAccount,
        user_name: str = None,
        # Имя пользователя, владеющего аккаунтом
        chat_url: str = None,
        chat_type: str = None,
        name: str = None,
        storage_path: str = None
    ):
        self.chat_id = chat_id
        self.social_account = social_account
        self.user_name = user_name
        self.chat_url = chat_url
        self.chat_type = chat_type
        self.name = name
        self.storage_path = storage_path

    @abstractmethod
    async def get_messages(self):
        """Получает и возвращает список сообщений из чата."""
        pass

    @abstractmethod
    async def get_list_users(self):
        """Получает и возвращает список пользователей (участников) чата."""
        pass

    def __str__(self):
        return LogMessages.INFO_OBJECT_CHAT.format(
            chat_id=self.chat_id,
            chat_type=self.chat_type,
            social_account_name=self.social_account.name,
        )


# # _____________________________________________________________________________
class User:
    def __init__(self, name: str, phone_numbers: list):
        self.name = name
        self.phone_numbers = phone_numbers
        self.social_accounts = []
        self.storage_path = None

    def add_phone_number(self, phone_number: str):
        self.social_accounts.append(phone_number)

    def add_social_account(self, account: SocialAccount):
        self.social_accounts.append(account)

    def get_social_accounts(self):
        return self.social_accounts

    def __str__(self):
        return LogMessages.INFO_OBJECT_USER.format(
            name=self.name, phones=self.phone_numbers
        )


class Mistaken:
    """
    Universal class for error handling and validation
    """

    @staticmethod
    def validate_type(obj: typing.Any,
                      expected_type: type,
                      param_name: str = LogMessagesMistaken.PARAM_NAME_DEFAULT)\
            -> None:
        """
        Checks the object type and throws a TypeError

        Args:
            obj: The object being checked
            expected_type: Expected data type
            param_name: The name of the parameter for the error message (optional)

        Raises:
            TypeError: If the object type does not match what is expected.
        """
        if not isinstance(obj, expected_type):
            error_msg = LogMessagesMistaken.ERROR_TYPE_MISMATCH.format(
                expected_type=expected_type.__name__,
                actual_type=type(obj).__name__,
                param_name=param_name)

            raise TypeError(error_msg)

    @staticmethod
    def validate_exists(obj: typing.Any,
                        param_name: str = LogMessagesMistaken.PARAM_NAME_DEFAULT)\
            -> None:
        """
        Checks the existence of an object and its emptiness and throws a ValueError

        Args:
            obj: The object being checked
            param_name: The name of the parameter for the error message (optional)

        Raises:
            ValueError: If the object is None, an empty string or an empty collection
        """
        # Проверка на None
        if obj is None:
            error_msg = (
                    LogMessagesMistaken.ERROR_NONE_OBJECT.format(param_name=param_name)
                )
            raise ValueError(error_msg)

        # Проверка пустой строки
        if isinstance(obj, str) and not obj.strip():
            error_msg = (
                LogMessagesMistaken.ERROR_EMPTY_STRING.format(param_name=param_name)
            )
            raise ValueError(error_msg)

        # Проверка пустой коллекции
        if hasattr(obj, PythonSettings.DUNDER_LEN) and len(obj) == 0:
            error_msg = (
                LogMessagesMistaken.ERROR_EMPTY_COLLECTION.format(
                    param_name=param_name)
            )
            raise ValueError(error_msg)

    @staticmethod
    def validate_all(obj: typing.Any,
                     expected_type: type,
                     param_name: str = LogMessagesMistaken.PARAM_NAME_DEFAULT)\
            -> None:

        """
        Comprehensive verification of the type and existence of an object

                Args:
                    obj: The object being checked
                    expected_type: Expected data type
                    param_name: The name of the parameter for the error message (optional)

                Raises:
                    ValueError: If the object does not exist
                    TypeError: If the object type does not match what is expected.
                """
        Mistaken.validate_type(obj, expected_type, param_name)
        Mistaken.validate_exists(obj, param_name)

    @staticmethod
    def handle_exception(func: callable,
                         *args,
                         **kwargs) -> typing.Any:
        """
        Wrapper for safe execution of functions with exception handling

        Args:
            func: A function to perform
            *args: Function arguments
            **kwargs: Named function arguments

        Returns:
            The result of the function execution or None in case of an error
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                LogMessagesMistaken.ERROR_FUNCTION_EXECUTION.format(
                    function_name=func.__name__, error=e
                )
            )
            return None


class TelegramAccount(SocialAccount):
    def __init__(self, user: User, phone_number: str, api_id: int, api_hash: str):
        super().__init__(
            name=SOCIAL_NETWORK_DICT.get(TELEGRAM_KEY), phone_number=phone_number
        )
        # Валидация входных параметров
        Mistaken.validate_all(user, User)
        Mistaken.validate_all(phone_number, str)
        Mistaken.validate_all(api_id, int)
        Mistaken.validate_all(api_hash, str)

        self.user = user
        self.api_id = api_id
        self.api_hash = api_hash
        self.chats = {}
        self.storage_path = (
            user.storage_path / str(self.name) / phone_number.replace("+", "")
        )

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.session_path = FileTemplates.SESSION_PATH.format(
            storage_path=self.storage_path, phone_number=phone_number.replace("+", "")
        )
        self.client = TelegramClient(
            str(self.session_path),
            self.api_id,
            self.api_hash,
            app_version=SystemConfig.TELEGRAM_CLIENT_APP_VERSION,
            device_model=SystemConfig.TELEGRAM_CLIENT_DEVICE_MODEL,
            system_version=SystemConfig.TELEGRAM_CLIENT_SYSTEM_VERSION,
            lang_code=SystemConfig.TELEGRAM_CLIENT_LANG_CODE,
            system_lang_code=SystemConfig.TELEGRAM_CLIENT_SYSTEM_LANG_CODE,
        )
        self._is_connected = False

    async def connect(self):
        if not self._is_connected:
            await self.client.start(phone=self.phone_number)
            self._is_connected = True
            logger.info(LogMessages.INFO_CONNECT_SUCCESS)

    async def disconnect(self):
        if self._is_connected:
            await self.client.disconnect()
            self._is_connected = False

    async def ensure_connection(self):
        if not self._is_connected:
            await self.connect()

    async def get_chats(self):
        await self.ensure_connection()
        all_chats = {}
        async for dialog in self.client.iter_dialogs():
            name = dialog.name or getattr(
                dialog.entity, TelegramEntityAttributes.TITLE, None
            )
            if name:
                all_chats[name] = dialog.id
        return all_chats

    async def add_chat(self, chat_obj):

        key = getattr(
            chat_obj,
            ChatObjectAttributes.CHAT_URL,
            getattr(chat_obj, ChatObjectAttributes.ID, None),
        )
        if key:
            self.chats[key] = chat_obj


# # _____________________________________________________________________________
class TelegramChat(Chat):
    def __init__(self, name: str | None, chat_id: int, social_account: TelegramAccount):
        """
        Инициализация объекта TelegramChat.

            Args:
                name: str | None - Название чата (может быть None для неизвестных чатов)
                chat_id: int- Уникальный идентификатор чата
                social_account: TelegramAccount - Объект Telegram аккаунта для работы с API


            Raises:
                TypeError: Если параметры имеют неправильный тип
                ValueError: Если параметры пустые или невалидные
        """
        # Валидация входных параметров
        Mistaken.validate_all(name, (str, type(None)), "name")
        Mistaken.validate_all(chat_id, int, "chat_id")
        Mistaken.validate_all(social_account, TelegramAccount, "social_account")

        # Проверка что chat_id не пустой если это строка
        if isinstance(chat_id, str):
            Mistaken.validate_exists(chat_id, "chat_id")

        # Проверка что social_account имеет client
        Mistaken.validate_exists(social_account.client, "social_account.client")

        super().__init__(chat_id=chat_id, social_account=social_account, name=name)
        # Эти поля можно заполнить позже, если они необходимы
        self.social_account = social_account

        self.chat_url = None
        self.chat_type = None

        self.name = name
        self.client = self.social_account.client
        self.entity = None
        self.storage_path = self.social_account.storage_path

    async def initialize(self):
        try:
            await self.social_account.ensure_connection()
            self.entity = await self.client.get_entity(self.chat_id)
        except Exception as e:
            raise RuntimeError(
                LogMessages.ERROR_ENTITY_FETCH_FAILED.format(chat_id=self.chat_id)
            ) from e

            async def get_messages(self):
        messages = []
        message_count = 0

        try:
            async for message in self.client.iter_messages(self.entity,
                                                           reverse=True,
                                                           limit=TelegramAPISettings.MAX_MESSAGES_PER_SESSION):  # Добавил limit
                if message_count >= TelegramAPISettings.MAX_MESSAGES_PER_SESSION:  # Дополнительная проверка
                    break

                if not getattr(message, "text", None):
                    continue

                # ЗАДЕРЖКА КАЖДЫЕ 50 СООБЩЕНИЙ
                if message_count > 0 and message_count % TelegramAPISettings.MESSAGES_PER_REQUEST == 0:
                    logger.info(
                        f"Обработано {message_count} сообщений. Пауза {TelegramAPISettings.DELAY_BETWEEN_REQUESTS} секунд...")
                    await asyncio.sleep(TelegramAPISettings.DELAY_BETWEEN_REQUESTS)

                # ВАШ СУЩЕСТВУЮЩИЙ КОД (без изменений)
                author_name = MessageKeys.UNKNOWN_AUTHOR
                author_id = None

                if getattr(message, "sender", None):
                    sender_entity = await self.client.get_entity(
                        message.sender)
                    if isinstance(sender_entity, TelethonUser):
                        author_id = sender_entity.id
                        if getattr(sender_entity, "last_name", None):
                            author_name = FileTemplates.FULL_NAME_TEMPLATE.format(
                                first_name=getattr(sender_entity, "first_name",
                                                   "") or "",
                                last_name=getattr(sender_entity, "last_name",
                                                  "") or "",
                            )
                        else:
                            author_name = getattr(
                                sender_entity, "first_name",
                                MessageKeys.UNKNOWN_AUTHOR
                            )
                    elif isinstance(sender_entity, (Channel, PeerChannel)):
                        author_id = getattr(sender_entity, "id", None)
                        title = getattr(sender_entity,
                                        TelegramEntityAttributes.TITLE, None)
                        author_name = title or MessageKeys.UNKNOWN_AUTHOR
                    else:
                        author_name = MessageKeys.UNKNOWN_AUTHOR

                elif getattr(message, "sender_chat", None):
                    sender_chat = await self.client.get_entity(
                        message.sender_chat)
                    author_id = getattr(sender_chat, "id", None)
                    title = getattr(sender_chat,
                                    TelegramEntityAttributes.TITLE, None)
                    author_name = f"{title or MessageKeys.UNKNOWN_AUTHOR} [channel]"

                else:
                    try:
                        chat_entity = await self.client.get_entity(self.entity)
                        if isinstance(chat_entity, (Channel, PeerChannel)):
                            author_id = getattr(chat_entity, "id", None)
                            title = getattr(chat_entity,
                                            TelegramEntityAttributes.TITLE,
                                            None)
                            author_name = title or MessageKeys.UNKNOWN_AUTHOR
                    except Exception:
                        pass

                message_dict = {
                    MessageKeys.MESSAGE_ID: message.id,
                    MessageKeys.USER_ID: author_id,
                    MessageKeys.MESSAGE_TEXT: message.text,
                    MessageKeys.AUTHOR_NAME: author_name,
                    MessageKeys.DATE: (
                        message.date.isoformat() if getattr(message, "date",
                                                            None) else None
                    ),
                    MessageKeys.REPLY_TO_ID: getattr(message,
                                                     "reply_to_msg_id", None),
                }
                messages.append(message_dict)
                message_count += 1

                # НЕБОЛЬШАЯ ЗАДЕРЖКА МЕЖДУ КАЖДЫМ СООБЩЕНИЕМ
                await asyncio.sleep(TelegramAPISettings.DELAY_BETWEEN_MESSAGES)

        except Exception as e:
            logger.error(f"Ошибка при выгрузке сообщений: {e}")

        logger.info(f"Выгрузка завершена. Сообщений: {len(messages)}")
        return messages

    async def get_list_users(self):
        participants = await self.client.get_participants(self.entity)
        users = []
        for participant in participants:
            if participant.last_name:
                user_name = FileTemplates.FULL_NAME_TEMPLATE.format(
                    first_name=participant.first_name, last_name=participant.last_name
                )
            else:
                user_name = participant.first_name
            users.append(user_name)
        return users


# # _____________________________________________________________________________


class Knot:
    """Узел графа - представляет пользователя"""

    def __init__(self, user_id: int, username: str):
        """
        Инициализация узла графа.

        Args:
            user_id: ID пользователя
            username: Имя пользователя

        Raises:
            TypeError: Если параметры имеют неправильный тип
            ValueError: Если параметры пустые или невалидные
        """
        Mistaken.validate_all(user_id, int, "user_id")
        Mistaken.validate_all(username, str, "username")
        Mistaken.validate_exists(username, "username")

        self.user_id = user_id  # ID пользователя
        self.username = username  # Имя пользователя
        self.edges = []  # Все связанные ребра


class Edge:
    """Ребро графа - представляет взаимодействие между пользователями"""

    def __init__(
        self,
        edge_id: int,
        edge_type: EdgeType,
        from_user: Knot,
        to_user: Knot,
        content: str | None,
    ):
        """
        Инициализация ребра графа.

        Args:
            edge_id: Уникальный ID ребра
            edge_type: Тип взаимодействия
            from_user: Отправитель
            to_user: Получатель
            content: Содержание

        Raises:
            TypeError: Если параметры имеют неправильный тип
            ValueError: Если параметры пустые или невалидные
        """
        Mistaken.validate_all(edge_id, int, "edge_id")
        Mistaken.validate_all(edge_type, EdgeType, "edge_type")
        Mistaken.validate_all(from_user, Knot, "from_user")
        Mistaken.validate_all(to_user, Knot, "to_user")

        self.edge_id = edge_id  # Уникальный ID ребра
        self.edge_type = edge_type  # Тип взаимодействия
        self.from_user = from_user  # Отправитель
        self.to_user = to_user  # Получатель
        self.content = content  # Содержание (текст/реакция)
        self.timestamp = None  # Временная метка


class Graph:
    """Граф социальных взаимодействий"""

    def __init__(self):
        """
        Инициализация графа социальных взаимодействий.
        """
        self.users: dict[int, Knot] = {}  # Все пользователи
        self.messages: dict[int, dict] = (
            {}
        )  # Узлы сообщений: message_id -> {text, author_id}
        self.edges: dict[int, Edge] = {}  # Все взаимодействия (user<->user), для метрик
        self.message_edges: list[tuple] = (
            []
        )  # Доп. рёбра для визуализации (user/message смешанные)
        self.next_edge_id = 1  # Счетчик ID ребер

    def add_user(self, user_id: int, username: str) -> Knot:
        """
        Добавляет нового пользователя.

        Args:
            user_id: ID пользователя
            username: Имя пользователя

        Returns:
            Knot: Созданный или существующий узел пользователя

        Raises:
            TypeError: Если параметры имеют неправильный тип
            ValueError: Если параметры пустые или невалидные
        """

        Mistaken.validate_all(user_id, int, "user_id")
        Mistaken.validate_all(username, str, "username")
        Mistaken.validate_exists(username, "username")
        if user_id not in self.users:
            self.users[user_id] = Knot(user_id, username)
        return self.users[user_id]

    def add_interaction(
        self,
        edge_type: EdgeType,
        from_user_id: int,
        to_user_id: int,
        content: str = None,
    ) -> Edge:
        """
        Добавляет новое взаимодействие.

        Args:
            edge_type: Тип взаимодействия
            from_user_id: ID пользователя-отправителя
            to_user_id: ID пользователя-получателя
            content: Содержание взаимодействия

        Returns:
            Edge: Созданное ребро взаимодействия

        Raises:
            TypeError: Если параметры имеют неправильный тип
            ValueError: Если пользователи не найдены
        """
        Mistaken.validate_all(edge_type, EdgeType, "edge_type")
        Mistaken.validate_all(from_user_id, int, "from_user_id")
        Mistaken.validate_all(to_user_id, int, "to_user_id")

        from_user = self.users.get(from_user_id)
        to_user = self.users.get(to_user_id)

        if not from_user or not to_user:
            if not from_user and not to_user:
                raise ValueError(
                    LogMessages.ERROR_USERS_NOT_FOUND.format(
                        from_user_id=from_user_id, to_user_id=to_user_id
                    )
                )
            elif not from_user:
                raise ValueError(
                    LogMessages.ERROR_USER_NOT_FOUND.format(user_id=from_user_id)
                )
            else:
                raise ValueError(
                    LogMessages.ERROR_USER_NOT_FOUND.format(user_id=to_user_id)
                )

        edge = Edge(
            edge_id=self.next_edge_id,
            edge_type=edge_type,
            from_user=from_user,
            to_user=to_user,
            content=content,
        )

        self.edges[edge.edge_id] = edge
        from_user.edges.append(edge)
        to_user.edges.append(edge)
        self.next_edge_id += 1

        return edge

    def add_message_node(
        self, message_id: int, author_user_id: int | None, text: str | None
    ) -> None:
        """
        Добавляет узел сообщения в граф.

        Args:
            message_id: ID сообщения
            author_user_id: ID автора сообщения
            text: Текст сообщения

        Raises:
            TypeError: Если параметры имеют неправильный тип
        """
        Mistaken.validate_all(message_id, int, "message_id")

        if author_user_id is not None:
            Mistaken.validate_all(author_user_id, int, "author_user_id")

        if text is not None:
            Mistaken.validate_all(text, str, "text")

        if message_id in self.messages:
            return
        self.messages[message_id] = {
            "author_id": author_user_id,
            "text": text or "",
        }

    def add_mixed_edge(
        self, from_id, to_id, edge_type: EdgeType, content: str | None = None
    ) -> None:
        """
        Добавляет смешанное ребро для визуализации.

        Args:
            from_id: ID исходного узла
            to_id: ID целевого узла
            edge_type: Тип ребра
            content: Содержание ребра

        Raises:
            TypeError: Если параметры имеют неправильный тип
        """
        Mistaken.validate_all(edge_type, EdgeType, "edge_type")

        if content is not None:
            Mistaken.validate_all(content, str, "content")
        self.message_edges.append((from_id, to_id, edge_type, content))
