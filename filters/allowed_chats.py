import logging
from typing import List

from telegram import Message
from telegram.ext.filters import MessageFilter

logger = logging.getLogger(__name__)


class AllowedChatsMessageFilter(MessageFilter):

    def __init__(self, allowed_chat_ids: List[str]):
        super().__init__()
        self.allowed_chat_ids = allowed_chat_ids

    def filter(self, message: Message) -> bool:
        chat_id = str(message.chat.id)
        is_allowed_user = chat_id in self.allowed_chat_ids
        if not is_allowed_user:
            logger.info(f'chat_id="{chat_id}" is not allowed')

        return is_allowed_user
