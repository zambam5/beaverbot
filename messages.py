from datetime import datetime
import re
import logging
from typing import Any
from typing import Dict
from typing import Optional

logger = logging.getLogger("__main__." + __name__)


class Message:
    action: str
    raw_message: Optional[str]
    data: Optional[str]
    name: Optional[str]
    message: str
    channel: Optional[str]
    custom_reward_id: Optional[str]

    regex = {
        "data": re.compile(
            r"^(?:@(?P<tags>\S+)\s)?:(?P<data>\S+)(?:\s)"
            r"(?P<action>[A-Z]+)(?:\s#)?(?P<channel>\S+)?"
            r"(?:\s(?::)?(?P<content>.+))?"
        ),
        "ping": re.compile(r"PING (?P<content>.+)"),
        "reconnect": re.compile(r"RECONNECT"),
        "author": re.compile(
            r"(?P<author>[a-zA-Z0-9_]+)!(?P=author)" r"@(?P=author).tmi.twitch.tv"
        ),
        "mode": re.compile(r"(?P<mode>[\+\-])o (?P<user>.+)"),
        "host": re.compile(r"(?P<channel>[a-zA-Z0-9_]+) " r"(?P<count>[0-9\-]+)"),
    }

    def __init__(self, message) -> None:
        self.raw_message = message
        self.message = None
        self.process_message(message)

    def process_message(self, message: str) -> None:
        """Take a message from the client and build the class from it

        Args:
            message (str): A string from the Twitch IRC client
        """
        messagedict = self._create_message_dict(message)
        if not messagedict:
            self.action = "BAD MESSAGE"
            self.channel = None
        else:
            self.dict = messagedict
            for key in messagedict:
                key_ = key.replace("-", "_")
                setattr(self, key_, messagedict[key])

    def _create_message_dict(self, message: str):
        """
        uses regex to process a message
        some messages come broken
        currently no way to deal with that
        """
        messagedict = {}
        if message.startswith("PING"):
            messagedict["action"] = "PING"
            messagedict["time"] = datetime.now()
            return messagedict
        else:
            m = self.regex["data"].match(message)
            try:
                tags = m.group("tags")
                for tag in tags.split(";"):
                    t = tag.split("=")
                    messagedict[t[0]] = t[1]
            except:
                tags = None

            try:
                action = m.group("action")
                messagedict["action"] = action
            except:
                action = None

            try:
                data = m.group("data")
                messagedict["data"] = data
                try:
                    name = self.regex["author"].match(data).group("author")
                    messagedict["name"] = name
                except:
                    name = None
            except:
                data = None

            try:
                content = m.group("content")
                messagedict["message"] = content
            except:
                content = None

            try:
                channel = m.group("channel")
                messagedict["channel"] = channel
            except:
                channel = None
        return messagedict
